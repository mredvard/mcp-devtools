"""Security guardrails for devtools.

Prevents LLMs from destroying the system, deleting critical files,
accessing secrets, or making SSRF requests to internal services.
"""

import ipaddress
import re
import socket
from pathlib import Path
from urllib.parse import urlparse


class GuardrailError(Exception):
    """Raised when a guardrail blocks an operation."""


# ---------------------------------------------------------------------------
# Path protection
# ---------------------------------------------------------------------------

# System paths that must never be written to, edited, or deleted via tools
PROTECTED_PATHS = {
    "/bin", "/sbin", "/usr/bin", "/usr/sbin", "/usr/lib", "/usr/libexec",
    "/System", "/Library",                          # macOS system
    "/boot", "/initrd",                             # Linux boot
    "/etc", "/var/log",                             # System config & logs
    "/dev", "/proc", "/sys",                        # Virtual filesystems
    "/root",                                        # Root home
}

# Sensitive files that should not be read or written
SENSITIVE_PATTERNS = [
    r"\.env($|\.)",                                 # .env, .env.local, .env.production
    r"id_rsa", r"id_ed25519", r"id_ecdsa",          # SSH private keys
    r"\.pem$", r"\.key$",                           # TLS private keys
    r"/\.ssh/",                                     # SSH directory
    r"/\.gnupg/",                                   # GPG directory
    r"/\.aws/credentials",                          # AWS creds
    r"/\.kube/config",                              # Kubernetes config
    r"/etc/shadow",                                 # Password hashes
    r"/etc/passwd",                                 # User accounts
    r"credentials\.json",                           # Generic credentials
    r"secrets\.ya?ml",                              # Secret configs
    r"\.keychain",                                  # macOS keychain
    r"token\.json",                                 # OAuth tokens
]

_sensitive_re = re.compile("|".join(SENSITIVE_PATTERNS), re.IGNORECASE)


def validate_path_not_protected(file_path: str) -> None:
    """Block writes/edits to protected system paths.

    Checks both the literal path and the resolved path to handle
    symlinks (e.g., /etc → /private/etc on macOS).
    """
    literal = str(Path(file_path))
    resolved_str = str(Path(file_path).resolve())

    for protected in PROTECTED_PATHS:
        for candidate in (literal, resolved_str):
            if candidate == protected or candidate.startswith(protected + "/"):
                raise GuardrailError(
                    f"Blocked: refusing to modify protected system path '{file_path}'"
                )


def validate_path_not_sensitive(file_path: str, *, operation: str = "access") -> None:
    """Block access to files that likely contain secrets."""
    resolved = str(Path(file_path).resolve())
    if _sensitive_re.search(resolved):
        raise GuardrailError(
            f"Blocked: refusing to {operation} sensitive file '{file_path}' — "
            "this file may contain secrets or credentials"
        )


def validate_no_path_traversal(file_path: str, base_dir: str | None = None) -> None:
    """Ensure resolved path doesn't escape the base directory via '..' tricks.

    Only enforced when base_dir is provided (e.g., for workspace-confined tools).
    """
    if base_dir is None:
        return
    resolved = Path(file_path).resolve()
    base = Path(base_dir).resolve()
    if not str(resolved).startswith(str(base) + "/") and resolved != base:
        raise GuardrailError(
            f"Blocked: path '{file_path}' resolves outside allowed directory '{base_dir}'"
        )


# ---------------------------------------------------------------------------
# Bash command guardrails
# ---------------------------------------------------------------------------

# Commands/patterns that are never acceptable
BLOCKED_COMMANDS = [
    # Destructive filesystem operations — block rm targeting root or critical system dirs
    r"\brm\s+(-[a-zA-Z]*\s+)*/$",                                         # rm / or rm -rf /
    r"\brm\s+(-[a-zA-Z]*\s+)*/\s+",                                       # rm / <more args>
    r"\brm\s+(-[a-zA-Z]*\s+)*/(bin|sbin|usr|etc|boot|dev|proc|sys|root|System|Library|var)\b",
    r"\bmkfs\b",                                                           # Format filesystem
    r"\bdd\b.*\bof=/dev/",                                                 # Raw disk write
    r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;",                                    # Fork bomb
    r"\b>\s*/dev/sd[a-z]",                                                 # Overwrite disk
    r"\bshred\b",                                                          # Secure delete
    r"\bwipefs\b",                                                         # Wipe filesystem

    # System control
    r"\bshutdown\b", r"\breboot\b", r"\bhalt\b", r"\bpoweroff\b",
    r"\binit\s+[0-6]\b",
    r"\bsystemctl\s+(stop|disable|mask)\b",

    # Privilege escalation
    r"\bsudo\b", r"\bsu\s", r"\bsu$",
    r"\bchmod\s+[0-7]*777\b",                                             # World-writable
    r"\bchmod\s+[0-7]*666\b",                                             # World-writable files
    r"\bchown\s+root\b",

    # Dangerous network operations
    r"\bnc\s+-[a-zA-Z]*l",                                                # Netcat listen
    r"\bcurl\b.*\|\s*(ba)?sh\b",                                          # Pipe curl to shell
    r"\bwget\b.*\|\s*(ba)?sh\b",                                          # Pipe wget to shell

    # Credential/key theft
    r"\bcat\b.*\.(pem|key|env)\b",
    r"\bcat\b.*/\.ssh/",
    r"\bcat\b.*/etc/shadow",

    # History/audit tampering
    r"\bunset\s+HISTFILE\b",
    r"\bexport\s+HISTFILE=/dev/null\b",
    r"\bhistory\s+-c\b",
    r"\b>\s*~/\..*_history\b",

    # Container/VM escape
    r"\bnsenter\b",
    r"\bmount\s",
    r"\bumount\s",
    r"\bchroot\b",
]

_blocked_re = [re.compile(p, re.IGNORECASE) for p in BLOCKED_COMMANDS]


def validate_bash_command(command: str) -> None:
    """Block dangerous shell commands."""
    for pattern in _blocked_re:
        if pattern.search(command):
            raise GuardrailError(
                f"Blocked: command matches dangerous pattern. "
                f"Refusing to execute: {command!r}"
            )


# ---------------------------------------------------------------------------
# SSRF protection for web_fetch
# ---------------------------------------------------------------------------

PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),      # Link-local / cloud metadata
    ipaddress.ip_network("::1/128"),              # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),             # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),            # IPv6 link-local
]

BLOCKED_HOSTNAMES = {
    "metadata.google.internal",
    "metadata.google.internal.",
    "169.254.169.254",                            # AWS/GCP/Azure metadata
}


def validate_url_not_internal(url: str) -> None:
    """Block requests to private/internal network addresses (SSRF protection)."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise GuardrailError(f"Blocked: could not parse hostname from URL '{url}'")

    # Check blocked hostnames first
    if hostname.lower() in BLOCKED_HOSTNAMES:
        raise GuardrailError(
            f"Blocked: refusing to fetch internal/metadata URL '{url}'"
        )

    # Resolve hostname and check against private ranges
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        # If we can't resolve, let httpx handle the error naturally
        return

    for family, _, _, _, sockaddr in addr_infos:
        ip = ipaddress.ip_address(sockaddr[0])
        for network in PRIVATE_RANGES:
            if ip in network:
                raise GuardrailError(
                    f"Blocked: URL '{url}' resolves to private address {ip} — "
                    "refusing to make request (SSRF protection)"
                )

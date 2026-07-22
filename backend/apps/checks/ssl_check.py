import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

# separate from tasks.py on purpose - this is a distinct piece of logic
# (inspect a cert) from the orchestration in perform_check, and easier to
# poke at on its own in a shell if something looks wrong later


def check_ssl_certificate(url, timeout=5):
    """Returns (ssl_valid, ssl_expires_at) for an https:// URL.
    Returns (None, None) for anything else - SSL just doesn't apply."""
    parsed = urlparse(url)
    if parsed.scheme != 'https':
        return None, None

    hostname = parsed.hostname
    port = parsed.port or 443

    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as tls_sock:
                cert = tls_sock.getpeercert()
    except (ssl.SSLError, socket.error, socket.timeout):
        # covers everything from "cert doesn't match hostname" to "site is
        # down entirely" - either way there's no cert info to report, and
        # this isn't the check that should decide up/down (that's is_up)
        return False, None

    expires_at = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z').replace(
        tzinfo=timezone.utc
    )
    is_valid = expires_at > datetime.now(timezone.utc)
    return is_valid, expires_at

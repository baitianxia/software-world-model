"""Direct HTTPS opener with verified system-CA fallback."""

from __future__ import annotations

import os
import ssl
from urllib import request as urllib_request


_SYSTEM_CA_FILE_CANDIDATES = (
    "/etc/ssl/cert.pem",
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
)


def build_direct_https_opener():
    """Build a proxy-free HTTPS opener without weakening certificate checks."""

    context = ssl.create_default_context()
    defaults = ssl.get_default_verify_paths()
    if defaults.cafile is None and defaults.capath is None:
        for candidate in _SYSTEM_CA_FILE_CANDIDATES:
            if os.path.isfile(candidate):
                context.load_verify_locations(cafile=candidate)
                break
    return urllib_request.build_opener(
        urllib_request.ProxyHandler({}),
        urllib_request.HTTPSHandler(context=context),
    )

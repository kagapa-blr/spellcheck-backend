from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Load environment variables from the .env file
load_dotenv()


def add_security_middleware(app):
    """
    Add security-related middleware to a FastAPI/Starlette app.

    Notes:
    - Do NOT set `X-Frame-Options: DENY` if you want `frame-ancestors` to allow
      specific external framing origins — X-Frame-Options can block framing.
    - Avoid using a scheme + wildcard like `https://*.example.com` inside
      `frame-ancestors` because some user agents reject that form. Use either
      a host-source wildcard (`*.example.com`) or an explicit origin.
    - For CORS with wildcard subdomains, prefer `allow_origin_regex`.
    """

    # Performance
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    environment = os.getenv("ENV", "dev")
    if environment != "dev":
        app.add_middleware(HTTPSRedirectMiddleware)

    # Trusted hosts (starlette supports wildcard host patterns)
    allowed_hosts = ["127.0.0.1", "localhost", "*.karnataka.gov.in", "*"]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # CORS: allow local dev origins explicitly; allow karnataka subdomains via regex
    allow_origin_regex = r"^https://([a-z0-9-]+\.)*karnataka\.gov\.in$"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1",
            "http://localhost",
            "http://localhost:5173",
            "http://localhost:5174",
        ],
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "*"],
    )

    class SecureHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)

            # IMPORTANT: do not set X-Frame-Options: DENY if you rely on CSP frame-ancestors
            # Remove or leave out X-Frame-Options so CSP controls framing.

            # Basic secure headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains"

            # Build frame-ancestors directive from env or defaults.
            # Provide tokens separated by spaces; environment variable may be e.g.
            # FRAME_ANCESTORS="self https://karnataka.gov.in *.karnataka.gov.in"
            raw_frame_ancestors = os.getenv(
                "FRAME_ANCESTORS", "self https://karnataka.gov.in *.karnataka.gov.in"
            )

            parts = []
            for token in raw_frame_ancestors.split():
                if token == "self":
                    parts.append("'self'")
                else:
                    # do not wrap host/origin tokens in extra quotes
                    parts.append(token)

            frame_ancestors_value = " ".join(parts)

            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https://karnataka.gov.in *.karnataka.gov.in; "
                "font-src 'self' data:; "
                f"frame-ancestors {frame_ancestors_value};"
            )

            response.headers["Content-Security-Policy"] = csp

            return response

    app.add_middleware(SecureHeadersMiddleware)

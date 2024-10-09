import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# Load environment variables from the .env file
load_dotenv()

def add_security_middleware(app):
    """
    Add all necessary security-related middleware to the FastAPI application.
    """

    # Enable GZip middleware for better performance
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Get the environment variable from .env file
    environment = os.getenv("ENV", "dev")

    # Allow HTTP connections for local development, enforce HTTPS for production
    if environment != "dev":
        app.add_middleware(HTTPSRedirectMiddleware)

    # Trusted Hosts Middleware to prevent Host header attacks
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.karnataka.gov.in", "127.0.0.1", "localhost", "yourdomain.com"]
    )

    # Allow CORS for trusted origins only, including subdomains of karnataka.gov.in
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://*.karnataka.gov.in", "http://127.0.0.1", "http://localhost"],  # Allow local and production domains
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Secure Headers Middleware (custom)
    class SecureHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

            # Updated Content-Security-Policy
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' https://*.karnataka.gov.in data:; "  # Allow images from ekannada.karnataka.gov.in
                "font-src 'self';"
            )

            return response

    app.add_middleware(SecureHeadersMiddleware)

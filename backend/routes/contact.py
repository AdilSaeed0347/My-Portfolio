"""
backend/routes/contact.py
Contact form endpoint — sends email via Resend API.
"""

import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, field_validator
import re
import time
from collections import defaultdict

from services.email_service import EmailService

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Simple in-memory rate limiter (per IP, max 3 submissions per 10 minutes)
# ---------------------------------------------------------------------------
_rate_store: dict = defaultdict(list)
_RATE_LIMIT    = 3       # max requests
_RATE_WINDOW   = 600     # seconds (10 minutes)


def _check_rate_limit(ip: str) -> bool:
    """Returns True if request is allowed, False if rate-limited."""
    now = time.time()
    timestamps = _rate_store[ip]
    # Remove timestamps outside window
    _rate_store[ip] = [t for t in timestamps if now - t < _RATE_WINDOW]
    if len(_rate_store[ip]) >= _RATE_LIMIT:
        return False
    _rate_store[ip].append(now)
    return True


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------

class ContactRequest(BaseModel):
    name:    str
    email:   EmailStr
    subject: str
    message: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters.")
        if len(v) > 80:
            raise ValueError("Name is too long.")
        return v

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Subject must be at least 3 characters.")
        if len(v) > 120:
            raise ValueError("Subject is too long.")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Message must be at least 10 characters.")
        if len(v) > 3000:
            raise ValueError("Message is too long (max 3000 characters).")
        return v


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/contact")
async def send_contact(request: Request, body: ContactRequest):
    """
    Accepts contact form submission and sends email via Resend.
    Rate-limited to 3 requests per IP per 10 minutes.
    """
    client_ip = request.client.host if request.client else "unknown"

    if not _check_rate_limit(client_ip):
        logger.warning(f"Rate limit hit for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a few minutes before trying again."
        )

    try:
        email_service = EmailService()
        success = await email_service.send_contact_email(
            sender_name    = body.name,
            sender_email   = body.email,
            subject        = body.subject,
            message        = body.message,
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to send email. Please try again.")

        logger.info(f"Contact email sent from {body.email} | subject: {body.subject}")
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Your message was sent successfully!"}
        )

    except HTTPException:
        raise
    except Exception as exc:
        print("🔥 CONTACT ROUTE ERROR:", str(exc))
        logger.error(f"Contact endpoint error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
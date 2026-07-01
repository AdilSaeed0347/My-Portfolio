"""
backend/services/email_service.py
Resend-powered email service with a clean HTML template.
"""

import logging
import resend
from config.settings import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return parts[0][:2].upper() if parts else "?"


# ---------------------------------------------------------------------------
# HTML email template — notification to Adil
# ---------------------------------------------------------------------------

def _build_html(sender_name: str, sender_email: str,
                subject: str, message: str) -> str:
    import html as html_module
    import datetime

    safe_name    = html_module.escape(sender_name)
    safe_email   = html_module.escape(sender_email)
    safe_subject = html_module.escape(subject)
    safe_message = html_module.escape(message).replace("\n", "<br>")
    initials     = _get_initials(sender_name)
    timestamp    = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Portfolio Contact</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:16px;overflow:hidden;
                      box-shadow:0 4px 24px rgba(0,0,0,0.10);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);padding:32px 36px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td valign="middle">
                    <p style="margin:0;font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.3px;">
                      📬 New Portfolio Message
                    </p>
                    <p style="margin:6px 0 0;font-size:13px;color:#94a3b8;">
                      Adil Saeed — Portfolio Contact Form &nbsp;·&nbsp; {timestamp}
                    </p>
                  </td>
                  <td align="right" valign="middle">
                    <span style="display:inline-block;background:#22c55e;color:#ffffff;
                                 font-size:11px;font-weight:700;padding:5px 14px;
                                 border-radius:20px;letter-spacing:0.8px;
                                 text-transform:uppercase;">
                      ● New Message
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px 36px;">

              <!-- Avatar + Sender info card -->
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:#f8fafc;border-radius:12px;
                            border:1px solid #e2e8f0;margin-bottom:24px;">
                <tr>
                  <td style="padding:20px 24px;">
                    <table cellpadding="0" cellspacing="0">
                      <tr>
                        <!-- Initials Avatar -->
                        <td valign="middle" style="padding-right:18px;">
                          <table cellpadding="0" cellspacing="0">
                            <tr>
                              <td width="52" height="52"
                                  style="width:52px;height:52px;border-radius:50%;
                                         background:linear-gradient(135deg,#3b82f6,#6366f1);
                                         color:#ffffff;font-size:18px;font-weight:700;
                                         text-align:center;vertical-align:middle;
                                         font-family:'Segoe UI',Arial,sans-serif;
                                         border-radius:26px;">
                                {initials}
                              </td>
                            </tr>
                          </table>
                        </td>
                        <!-- Details -->
                        <td valign="middle">
                          <p style="margin:0 0 2px;font-size:12px;font-weight:600;
                                     color:#64748b;text-transform:uppercase;letter-spacing:0.6px;">
                            Sender Details
                          </p>
                          <p style="margin:0 0 3px;font-size:16px;font-weight:700;color:#0f172a;">
                            {safe_name}
                          </p>
                          <p style="margin:0 0 3px;font-size:14px;">
                            <a href="mailto:{safe_email}"
                               style="color:#3b82f6;text-decoration:none;">{safe_email}</a>
                          </p>
                          <p style="margin:0;font-size:13px;color:#64748b;">
                            <strong>Subject:</strong> {safe_subject}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Message -->
              <p style="margin:0 0 10px;font-size:12px;font-weight:600;color:#64748b;
                         text-transform:uppercase;letter-spacing:0.6px;">
                Message
              </p>
              <div style="background:#f8fafc;border-left:4px solid #3b82f6;
                          border-radius:0 12px 12px 0;padding:20px 24px;
                          font-size:15px;line-height:1.8;color:#334155;">
                {safe_message}
              </div>

              <!-- Reply button -->
              <table cellpadding="0" cellspacing="0" style="margin-top:28px;">
                <tr>
                  <td>
                    <a href="mailto:{safe_email}?subject=Re: {safe_subject}"
                       style="display:inline-block;
                              background:linear-gradient(135deg,#3b82f6,#6366f1);
                              color:#ffffff;font-size:14px;font-weight:600;
                              padding:13px 28px;border-radius:8px;
                              text-decoration:none;letter-spacing:0.2px;">
                      ↩ Reply to {safe_name}
                    </a>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:0 36px;">
              <hr style="border:none;border-top:1px solid #e2e8f0;margin:0;">
            </td>
          </tr>

          <!-- Footer with social links -->
          <tr>
            <td style="background:#f8fafc;padding:20px 36px;">
              <p style="margin:0 0 12px;font-size:12px;color:#94a3b8;text-align:center;">
                Sent via Adil Saeed's Portfolio
              </p>
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <a href="https://github.com/AdilSaeed0347"
                       style="display:inline-block;margin:0 6px;color:#64748b;font-size:12px;
                              text-decoration:none;border:1px solid #e2e8f0;border-radius:6px;
                              padding:5px 14px;background:#ffffff;">
                      🔗 GitHub
                    </a>
                    <a href="https://www.linkedin.com/in/adil-saeed-9b7b51363/"
                       style="display:inline-block;margin:0 6px;color:#64748b;font-size:12px;
                              text-decoration:none;border:1px solid #e2e8f0;border-radius:6px;
                              padding:5px 14px;background:#ffffff;">
                      💼 LinkedIn
                    </a>
                    <a href="mailto:adilahmad0347@gmail.com"
                       style="display:inline-block;margin:0 6px;color:#64748b;font-size:12px;
                              text-decoration:none;border:1px solid #e2e8f0;border-radius:6px;
                              padding:5px 14px;background:#ffffff;">
                      📧 Email
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Auto-reply template — sent to the visitor
# ---------------------------------------------------------------------------

def _build_auto_reply_html(sender_name: str) -> str:
    import html as html_module
    safe_name = html_module.escape(sender_name)

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Thanks for reaching out!</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:16px;overflow:hidden;
                      box-shadow:0 4px 24px rgba(0,0,0,0.10);">

          <tr>
            <td style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);padding:32px 36px;">
              <p style="margin:0;font-size:22px;font-weight:700;color:#ffffff;">
                Hi {safe_name} 👋
              </p>
              <p style="margin:6px 0 0;font-size:13px;color:#94a3b8;">
                Thanks for getting in touch!
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding:32px 36px;">
              <p style="margin:0 0 16px;font-size:15px;line-height:1.8;color:#334155;">
                I've received your message and will get back to you as soon
                as possible — usually within 24–48 hours.
              </p>
              <p style="margin:0 0 24px;font-size:15px;line-height:1.8;color:#334155;">
                In the meantime, feel free to explore my work:
              </p>

              <table cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                <tr>
                  <td style="padding:6px 0;">
                    <a href="https://github.com/AdilSaeed0347"
                       style="color:#3b82f6;text-decoration:none;font-size:14px;">
                      🔗 GitHub — github.com/AdilSaeed0347
                    </a>
                  </td>
                </tr>
                <tr>
                  <td style="padding:6px 0;">
                    <a href="https://www.linkedin.com/in/adil-saeed-9b7b51363/"
                       style="color:#3b82f6;text-decoration:none;font-size:14px;">
                      💼 LinkedIn — Adil Saeed
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:0;font-size:15px;color:#334155;">
                Best regards,<br>
                <strong>Adil Saeed</strong><br>
                <span style="color:#64748b;font-size:13px;">
                  Software Engineering Student · AI/ML Developer · IMSciences Peshawar
                </span>
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding:0 36px;">
              <hr style="border:none;border-top:1px solid #e2e8f0;margin:0;">
            </td>
          </tr>

          <tr>
            <td style="background:#f8fafc;padding:20px 36px;">
              <p style="margin:0 0 12px;font-size:12px;color:#94a3b8;text-align:center;">
                Adil Saeed's Portfolio
              </p>
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <a href="https://github.com/AdilSaeed0347"
                       style="display:inline-block;margin:0 6px;color:#64748b;font-size:12px;
                              text-decoration:none;border:1px solid #e2e8f0;border-radius:6px;
                              padding:5px 14px;background:#ffffff;">
                      🔗 GitHub
                    </a>
                    <a href="https://www.linkedin.com/in/adil-saeed-9b7b51363/"
                       style="display:inline-block;margin:0 6px;color:#64748b;font-size:12px;
                              text-decoration:none;border:1px solid #e2e8f0;border-radius:6px;
                              padding:5px 14px;background:#ffffff;">
                      💼 LinkedIn
                    </a>
                    <a href="mailto:adilahmad0347@gmail.com"
                       style="display:inline-block;margin:0 6px;color:#64748b;font-size:12px;
                              text-decoration:none;border:1px solid #e2e8f0;border-radius:6px;
                              padding:5px 14px;background:#ffffff;">
                      📧 Email
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Email Service class
# ---------------------------------------------------------------------------

class EmailService:
    """Wraps Resend SDK. One class, two email types."""

    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY
        self._from_address = settings.RESEND_FROM_EMAIL
        self._to_address   = settings.CONTACT_RECEIVER_EMAIL
        logger.info(f"EmailService ready — delivering to: {self._to_address}")

    async def send_contact_email(
        self,
        sender_name:  str,
        sender_email: str,
        subject:      str,
        message:      str,
    ) -> bool:
        try:
            resend.Emails.send({
                "from":     self._from_address,
                "to":       [self._to_address],
                "subject":  f"[Portfolio] {subject} — from {sender_name}",
                "html":     _build_html(sender_name, sender_email, subject, message),
                "text": (
                    f"New contact form submission\n\n"
                    f"Name:    {sender_name}\n"
                    f"Email:   {sender_email}\n"
                    f"Subject: {subject}\n\n"
                    f"Message:\n{message}"
                ),
                "reply_to": sender_email,
            })

            logger.info(f"Email delivered to {self._to_address} | reply-to: {sender_email}")
            return True

        except Exception as exc:
            print("🔥 REAL EMAIL ERROR:", str(exc))
            logger.error(f"Resend API error: {exc}", exc_info=True)
            raise exc
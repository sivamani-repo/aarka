import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import settings

logger = logging.getLogger("aarka.email")


def _send_email(to_email: str, subject: str, html_content: str, text_content: str) -> bool:
    """
    Sends an email using the configured SMTP server.
    If no SMTP host is configured (local dev mode), logs the email content to stdout.
    If SMTP host is configured and delivery fails, raises RuntimeError.
    """
    if not settings.smtp_host:
        logger.warning(
            f"\n=======================================================\n"
            f"[AARKA DEV EMAIL SERVICE - NO SMTP_HOST CONFIGURED]\n"
            f"To: {to_email}\n"
            f"Subject: {subject}\n"
            f"-------------------------------------------------------\n"
            f"{text_content}\n"
            f"=======================================================\n"
        )
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.emails_from_name} <{settings.emails_from_email}>"
    msg["To"] = to_email

    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    msg.attach(part1)
    msg.attach(part2)

    try:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
        if settings.smtp_tls:
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.emails_from_email, [to_email], msg.as_string())
        server.quit()
        logger.info(f"Email successfully delivered to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        raise RuntimeError(f"Email delivery failed: {str(e)}")


def send_verification_email(to_email: str, name: str, token: str) -> bool:
    verify_url = f"{settings.frontend_url}/verify-email?token={token}"
    subject = "Verify your AARKA account"

    text_content = (
        f"Hello {name},\n\n"
        f"Thank you for registering with AARKA (Solar Operations, Simplified).\n\n"
        f"Please verify your email address by visiting the following link:\n"
        f"{verify_url}\n\n"
        f"This verification link will expire in {settings.verification_token_expire_hours} hours.\n"
        f"If you did not register for an AARKA account, please ignore this email.\n\n"
        f"— AARKA Operations Team"
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f9f9f6; margin: 0; padding: 24px; color: #1c1917; }}
        .card {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e7e5e4; padding: 36px 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
        .brand {{ color: #1b4d36; font-size: 22px; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 4px; }}
        .tagline {{ color: #78716c; font-size: 13px; margin-bottom: 24px; }}
        .btn {{ display: inline-block; background-color: #1b4d36; color: #ffffff !important; text-decoration: none; font-weight: 600; font-size: 14px; padding: 12px 28px; border-radius: 8px; margin: 20px 0; }}
        .footer {{ font-size: 12px; color: #a8a29e; margin-top: 24px; border-top: 1px solid #f5f5f4; padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="brand">AARKA</div>
        <div class="tagline">Solar Operations, Simplified.</div>
        <h2 style="font-size: 18px; margin-top: 0;">Verify your email address</h2>
        <p style="font-size: 14px; line-height: 1.6;">Hello <strong>{name}</strong>,</p>
        <p style="font-size: 14px; line-height: 1.6;">Thank you for registering on the AARKA platform. To complete your account setup and log in, please confirm your email address by clicking the button below:</p>
        <div style="text-align: center;">
          <a href="{verify_url}" class="btn" target="_blank">Verify Email Address</a>
        </div>
        <p style="font-size: 13px; color: #78716c; line-height: 1.5;">Or copy and paste this link in your browser:<br><span style="color: #1b4d36; word-break: break-all;">{verify_url}</span></p>
        <div class="footer">
          This verification link is valid for {settings.verification_token_expire_hours} hours. If you did not create this account, no action is needed.
        </div>
      </div>
    </body>
    </html>
    """

    return _send_email(to_email, subject, html_content, text_content)


def send_password_reset_email(to_email: str, name: str, token: str) -> bool:
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"
    subject = "Reset your AARKA account password"

    text_content = (
        f"Hello {name},\n\n"
        f"We received a request to reset your password for your AARKA account.\n\n"
        f"You can reset your password by opening the following link:\n"
        f"{reset_url}\n\n"
        f"This link will expire in {settings.reset_token_expire_minutes} minutes.\n"
        f"If you did not request a password reset, you can safely ignore this email.\n\n"
        f"— AARKA Operations Team"
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f9f9f6; margin: 0; padding: 24px; color: #1c1917; }}
        .card {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e7e5e4; padding: 36px 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
        .brand {{ color: #1b4d36; font-size: 22px; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 4px; }}
        .tagline {{ color: #78716c; font-size: 13px; margin-bottom: 24px; }}
        .btn {{ display: inline-block; background-color: #1b4d36; color: #ffffff !important; text-decoration: none; font-weight: 600; font-size: 14px; padding: 12px 28px; border-radius: 8px; margin: 20px 0; }}
        .footer {{ font-size: 12px; color: #a8a29e; margin-top: 24px; border-top: 1px solid #f5f5f4; padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="brand">AARKA</div>
        <div class="tagline">Solar Operations, Simplified.</div>
        <h2 style="font-size: 18px; margin-top: 0;">Password Reset Request</h2>
        <p style="font-size: 14px; line-height: 1.6;">Hello <strong>{name}</strong>,</p>
        <p style="font-size: 14px; line-height: 1.6;">We received a request to reset the password for your AARKA account. Click the button below to choose a new password:</p>
        <div style="text-align: center;">
          <a href="{reset_url}" class="btn" target="_blank">Reset Password</a>
        </div>
        <p style="font-size: 13px; color: #78716c; line-height: 1.5;">Or copy and paste this link in your browser:<br><span style="color: #1b4d36; word-break: break-all;">{reset_url}</span></p>
        <div class="footer">
          This link will expire in {settings.reset_token_expire_minutes} minutes. If you did not request a password reset, please ignore this email.
        </div>
      </div>
    </body>
    </html>
    """

    return _send_email(to_email, subject, html_content, text_content)


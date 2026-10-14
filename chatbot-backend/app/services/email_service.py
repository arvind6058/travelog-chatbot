import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


class EmailService:
    @staticmethod
    def send_password_reset_email(recipient_email: str, reset_token: str) -> bool:
        """
        Generate password reset link and send via SMTP or log in dev mode.
        """
        frontend_base = (getattr(settings, "FRONTEND_BASE_URL", None) or "http://localhost:3000").rstrip("/")
        reset_link = f"{frontend_base}/reset-password?token={reset_token}"

        # Dev / fallback logging
        logger.info(
            f"[DEVELOPMENT ONLY] Password Reset requested for '{recipient_email}'. "
            f"Reset Link: {reset_link}"
        )

        email_host = getattr(settings, "EMAIL_HOST", "").strip()
        email_port = int(getattr(settings, "EMAIL_PORT", 587) or 587)
        email_user = getattr(settings, "EMAIL_USERNAME", "").strip()
        email_pass = getattr(settings, "EMAIL_PASSWORD", "").strip()
        email_from = getattr(settings, "EMAIL_FROM", "noreply@travelogix.com")

        if not email_host or not email_user:
            logger.info("SMTP email provider not configured. Reset link logged to server output.")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Reset Your Travelogix Password"
            msg["From"] = email_from
            msg["To"] = recipient_email

            text_body = (
                f"Hello,\n\n"
                f"We received a request to reset your Travelogix customer account password.\n\n"
                f"Click the link below or copy it into your browser to set a new password:\n"
                f"{reset_link}\n\n"
                f"This link will expire in 15 minutes.\n"
                f"If you did not request a password reset, please ignore this message.\n\n"
                f"Best regards,\nTravelogix Team"
            )

            html_body = f"""
            <div style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 24px; border-radius: 12px;">
              <h2 style="color: #38bdf8; margin-top: 0;">Travelogix Password Reset</h2>
              <p>Hello,</p>
              <p>We received a request to reset your Travelogix account password.</p>
              <p style="margin: 24px 0;">
                <a href="{reset_link}" style="background-color: #0284c7; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Reset Password</a>
              </p>
              <p style="font-size: 12px; color: #94a3b8;">Or copy and paste this URL into your browser:<br><a href="{reset_link}" style="color: #38bdf8;">{reset_link}</a></p>
              <p style="font-size: 12px; color: #64748b; margin-bottom: 0;">This link is valid for 15 minutes. If you did not request this, no action is needed.</p>
            </div>
            """

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(email_host, email_port) as server:
                server.starttls()
                if email_pass:
                    server.login(email_user, email_pass)
                server.sendmail(email_from, [recipient_email], msg.as_string())

            logger.info(f"Password reset email sent to {recipient_email}")
            return True
        except Exception as exc:
            logger.error(f"Failed to send password reset email to {recipient_email}: {exc}")
            return False

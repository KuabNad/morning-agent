from email.message import EmailMessage
import smtplib


def send_email_backup(settings, subject: str, body: str) -> bool:
    if not settings.email_enabled:
        return False

    required = [
        settings.smtp_host,
        settings.smtp_port,
        settings.smtp_user,
        settings.smtp_password,
        settings.email_from,
        settings.email_to,
    ]
    if not all(required):
        print("Email backup is enabled but SMTP settings are incomplete.")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from
    message["To"] = settings.email_to
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
        return True
    except Exception as exc:
        print(f"Email backup failed: {exc}")
        return False

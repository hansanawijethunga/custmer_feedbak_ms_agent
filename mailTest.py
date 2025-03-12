import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


def send_email(subject, body, recipient_email):
    try:
        # Get email and app password from environment variables
        sender_email = os.getenv('GMAIL_EMAIL')  # Email from environment variable
        app_password = os.getenv('GMAIL_APP_PASSWORD')  # App Password from environment variable

        if not sender_email or not app_password:
            raise ValueError("Gmail email or app password not set in environment variables.")

        # Set up the SMTP server
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # Create a MIME email
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Connect to Gmail's SMTP server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")


# Example Usage
send_email(
    subject="Test Email",
    body="This is a test email sent using Python with environment variables!",
    recipient_email="rapidminds99@gmail.com"
)

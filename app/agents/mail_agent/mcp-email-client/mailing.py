import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_email_with_attachment(to, subject, body, attachment_path):
    msg = MIMEMultipart()
    msg["From"] = "dtol@noreply.com"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with open(attachment_path, "rb") as f:
        part = MIMEApplication(f.read(), Name="result.xlsx")
        part["Content-Disposition"] = 'attachment; filename="result.xlsx"'
        msg.attach(part)

    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp.login("you@example.com", "your_password")
    smtp.send_message(msg)
    smtp.quit()

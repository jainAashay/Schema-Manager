from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

smtp_server = "smtp.gmail.com"
port = 587  
sender_email = "aashay1000@gmail.com"
sender_password = os.getenv("GMAIL_PASSWORD")
server=smtplib.SMTP(smtp_server, port)
server.connect(smtp_server, port)
server.starttls()
server.login(sender_email, sender_password)


def send_email(email, msg,verification):
    
    if verification:
        msg=create_verification_email(email,msg)
        server.sendmail(sender_email, email, msg.as_string())
    else:
        logging.info(str(email)+' '+str(msg))
        server.sendmail(sender_email, email, msg) 

def create_verification_email(email,verification_url):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Account Verification"
    msg["From"] = sender_email
    msg["To"] = email

    # Create the HTML message
    html_content = f"""
    <html>
        <body>
            <p>Please click the following link to verify your account:<br>
               <a href="{verification_url}" target="_blank">Verify Account</a>
            </p>
        </body>
    </html>
        """
    msg.attach(MIMEText(html_content, "html"))
    return msg

    

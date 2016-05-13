from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from django.conf import settings
EMAIL_TAG = "[varapp] "

def send_email(email_to, subject='No subject', text='', html='', tofile=None):
    """Call _send_email using the app's settings"""
    _send_email(settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_FROM,
                email_to, subject=subject, text=text, html=html, tofile=tofile)

def _send_email(email_host, email_port, email_from,
                email_to, subject='No subject', text='', html='', tofile=None):
    """
    :param email_to: email of the receiver
    :param subject: head of the message
    :param text: plain text to send if HTML cannot be used
    :param html: message contend, in HTML format (has priority over *text*)
    :param tofile: file object, for testing purposes
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = EMAIL_TAG + subject
    msg['From'] = email_from
    msg['To'] = email_to
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred. If it is supported, only the HTML
    # message will be received.
    msg.attach(part1)
    msg.attach(part2)
    if tofile:
        tofile.write(msg.as_string())
    else:
        try:
            server = smtplib.SMTP(email_host, email_port)
            server.send_message(msg)
            server.quit()
        except ConnectionRefusedError:
            raise ConnectionRefusedError("No SMTP server was found at {}:{}".format(email_host, email_port))


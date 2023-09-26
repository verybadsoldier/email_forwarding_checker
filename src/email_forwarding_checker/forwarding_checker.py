from datetime import datetime, timedelta
from typing import Dict, List
import smtplib
import logging
import time
import imaplib

_logger = logging.getLogger(__name__)


class ForwardingChecker:
    def __init__(
        self,
        smtp_sender: str,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        imap_host: str,
        imap_username: str,
        imap_password: str,
        imap_mailbox: str,
        delete_emails: bool,
        email_timeout: int,
    ) -> None:
        self._smtp_sender = smtp_sender
        self._smtp_username = smtp_username
        self._smtp_password = smtp_password
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._imap_host = imap_host
        self._imap_username = imap_username
        self._imap_password = imap_password
        self._body = "This is an automated email to test if configured mail forwarding is working  - sent by email_forwarding_checker (https://github.com/verybadsoldier/email_forwarding_checker)"
        self._subject_base = "EMail Forward Test - email_forwarding_checker"
        self._delete_emails = delete_emails
        self._mailbox = imap_mailbox
        self._email_timeout = email_timeout

    def check_multiple_emails(
        self, emails: List[str], email_timeout: int
    ) -> Dict[str, bool]:
        report = {}
        for addr in emails:
            result = self.send_and_check_email(addr, email_timeout)
            report[addr] = result
        return report

    def send_and_check_email(self, dest_email: str, email_timeout) -> bool:
        start_time = datetime.now()

        subject = f"{self._subject_base} - {dest_email}"

        # Send the email
        _logger.info(f"Logging into SMTP server: {self._smtp_host}")
        with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
            server.starttls()
            server.login(self._smtp_username, self._smtp_password)
            message = f"Subject: {subject}\n\n{self._body}"
            _logger.info(f"Sending email to {dest_email}")
            server.sendmail(self._smtp_sender, dest_email, message)

        _logger.info(f"Logging into IMAP server {self._imap_host}")
        with imaplib.IMAP4_SSL(self._imap_host) as mail:
            mail.login(self._imap_username, self._imap_password)
            mail.select(self._mailbox)

            while True:
                now = datetime.now()

                if now - start_time > timedelta(seconds=email_timeout):
                    return False

                wait_time = 5
                _logger.info(
                    f"Waiting for {wait_time} seconds for the mail to arrive..."
                )
                time.sleep(wait_time)

                # Refresh mails without reconnect
                mail.noop()

                _logger.info(f"Searching for the mail in the inbox...")
                status, email_ids = mail.search(None, f'(SUBJECT "{subject}")')

                if status != "OK":
                    raise RuntimeError("Error IMAP search")

                found = False
                for email_id_raw in email_ids[0].split():
                    _, msg_data = mail.fetch(email_id_raw, "(INTERNALDATE)")
                    timestamp = imaplib.Internaldate2tuple(msg_data[0])

                    if self._delete_emails:
                        mail.store(email_id_raw, "+FLAGS", "\\Deleted")

                    if now - datetime.fromtimestamp(time.mktime(timestamp)) < timedelta(
                        seconds=120
                    ):
                        _logger.info(f"Mail found")
                        found = True

                if self._delete_emails:
                    _logger.info(f"Deleting marked emails")
                    mail.expunge()

                if found:
                    return True
                else:
                    _logger.info(f"Mail not found")

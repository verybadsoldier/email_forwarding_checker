import email
import imaplib
import logging
import smtplib
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Dict, List

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
        repeat_interval: int,
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
        self._repeat_interval = repeat_interval

    def check_multiple_emails(self, emails: List[str], email_timeout: timedelta) -> Dict[str, int]:
        report: Dict[str, int] = {}
        for addr in emails:
            result = self.send_and_check_email(addr, email_timeout)
            report[addr] = 1 if result else 0
        return report

    def send_and_check_email(self, dest_email: str, email_timeout: timedelta) -> bool:
        subject = f"{self._subject_base} - {dest_email}"

        # Send the email
        start_time = datetime.now().astimezone()
        _logger.info("%s - Logging into SMTP server: %s", dest_email, self._smtp_host)
        with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
            server.starttls()
            server.login(self._smtp_username, self._smtp_password)

            body = self._body + f"\nSent on: {str(datetime.now().isoformat())}"

            message = f"Subject: {subject}\n\n{body}"
            _logger.info("%s - Sending email to %s", dest_email, dest_email)
            server.sendmail(self._smtp_sender, dest_email, message)

        _logger.info("%s - Logging into IMAP server %s", dest_email ,self._imap_host)
        with imaplib.IMAP4_SSL(self._imap_host) as mail:
            mail.login(self._imap_username, self._imap_password)
            mail.select(self._mailbox)

            num_delete = 0
            while True:
                now = datetime.now().astimezone()

                diff = now - start_time
                if diff > email_timeout:
                    _logger.info("%s - Timeout reached. Giving up", dest_email)
                    return False

                _logger.info("%s - Waiting for %d seconds for the mail to arrive... (Trying since %s/%s)", dest_email, self._repeat_interval, diff, email_timeout)
                time.sleep(self._repeat_interval)

                _logger.info("%s - Searching for the mail in the inbox...", dest_email)
                #status, email_ids = mail.search(None, f'(SUBJECT "{subject}")')
                status, email_ids = mail.search(None, 'UNSEEN')

                if status != "OK":
                    raise RuntimeError("{dest_email} - Error IMAP search")

                found = False
                for email_id_raw in email_ids[0].split():
                    _, msg_data = mail.fetch(email_id_raw, "(BODY.PEEK[HEADER.FIELDS (SUBJECT DATE)])")
                    if msg_data is None:
                        _logger.warning("%s - No email data found", dest_email)
                        continue
                    
                    response = msg_data[0]
                    if response is None:
                        _logger.warning("%s - No email response data found", dest_email)
                        continue

                    raw_email = response[1]
                    assert isinstance(raw_email, bytes)
                    msg = email.message_from_bytes(raw_email)

                    email_subject = msg["Subject"]
                    if email_subject != subject:
                        continue

                    if self._delete_emails:
                        num_delete += 1
                        mail.store(email_id_raw, "+FLAGS", "\\Deleted")

                    timestamp = parsedate_to_datetime(msg["Date"])
                    if timestamp > start_time:
                        _logger.info("%s - Mail found", dest_email)
                        found = True

                if num_delete > 0:
                    _logger.info("%s - Deleting marked emails", dest_email)
                    mail.expunge()

                if found:
                    return True
                else:
                    _logger.info("%s - Mail not found", dest_email)

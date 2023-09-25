from datetime import datetime, timedelta
import time
import smtplib
import imaplib


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
        delete_emails: bool = True,
    ) -> None:
        """
        Initializes the EmailForwarder class with the given SMTP and IMAP credentials.

        Args:
            smtp_sender (str): The email address of the sender.
            smtp_host (str): The SMTP server hostname.
            smtp_port (int): The SMTP server port.
            smtp_username (str): The username for the SMTP server.
            smtp_password (str): The password for the SMTP server.
            imap_host (str): The IMAP server hostname.
            imap_username (str): The username for the IMAP server.
            imap_password (str): The password for the IMAP server.
            delete_emails (bool, optional): Whether to delete forwarded emails from the destination mailbox. Defaults to True.

        Returns:
            None
        """
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

    def send_and_check_email(self, dest_email: str, timeout=120) -> bool:
        """
        Sends an email to the specified destination email address and checks if it has been forwarded within the last 2 minutes.

        Args:
            dest_email (str): The destination email address where the email will be sent.

        Returns:
            bool: True if the email has been forwarded within the last 2 minutes, False otherwise.
        """
        start_time = datetime.now()

        subject = f"{self._subject_base} - {dest_email}"

        # Send the email
        with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
            server.starttls()
            server.login(self._smtp_username, self._smtp_password)
            message = f"Subject: {subject}\n\n{self._body}"
            server.sendmail(self._smtp_sender, dest_email, message)

        with imaplib.IMAP4_SSL(self._imap_host) as mail:
            mail.login(self._imap_username, self._imap_password)
            mail.select("inbox")

            while True:
                now = datetime.now()

                if now - start_time > timedelta(seconds=timeout):
                    return False

                time.sleep(5)

                # Refresh mails without reconnect
                mail.noop()

                # Check if the email has been forwarded
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
                        found = True

                if self._delete_emails:
                    mail.expunge()

                if found:
                    return True

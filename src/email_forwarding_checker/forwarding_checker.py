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
    ) -> None:
        """
        Initializes the SMTP client with the provided sender, SMTP host, SMTP port, username, and password.

        Args:
            sender (str): The email address of the sender.
            smtp_host (str): The hostname or IP address of the SMTP server.
            smtp_port (int): The port number of the SMTP server.
            username (str): The username for authentication with the SMTP server.
            password (str): The password for authentication with the SMTP server.

        Returns:
            None: This function does not return any value.
        """
        self._sender = smtp_sender
        self._smtp_username = smtp_username
        self._smtp_password = smtp_password
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._imap_host = imap_host
        self._imap_username = imap_username
        self._imap_password = imap_password
        self._body = "This is an automated email to test if mail forwarding is working"
        self._subject_base = "FHEM EMail Forward Test"

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
            server.sendmail(self._sender, dest_email, message)

        with imaplib.IMAP4_SSL(self._imap_host) as mail:
            mail.login(self._imap_username, self._imap_password)
            mail.select("inbox")

            while True:
                time.sleep(5)

                now = datetime.now()

                if now - start_time > timedelta(seconds=timeout):
                    return False

                # Check if the email has been forwarded
                status, email_ids = mail.search(None, f'(SUBJECT "{subject}")')

                if status != "OK":
                    raise RuntimeError("Error IMAP search")

                for email_id_raw in email_ids[0].split():
                    _, msg_data = mail.fetch(email_id_raw, "(INTERNALDATE)")
                    timestamp = imaplib.Internaldate2tuple(msg_data[0])

                    if now - datetime.fromtimestamp(time.mktime(timestamp)) < timedelta(
                        seconds=120
                    ):
                        return True

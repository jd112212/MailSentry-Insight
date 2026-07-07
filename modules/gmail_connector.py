import imaplib
import logging

logger = logging.getLogger(__name__)

class GmailConnector:
    """
    Handles secure IMAP connection and authentication to Gmail.
    """
    def __init__(self, username: str, app_password: str):
        self.username = username
        self.app_password = app_password
        self.mail = None

    def connect(self) -> imaplib.IMAP4_SSL:
        """
        Connects and logs into imap.gmail.com using the SSL port.
        Raises ValueError if login fails.
        """
        try:
            logger.info("Initiating connection to imap.gmail.com...")
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            logger.info("Attempting login...")
            self.mail.login(self.username, self.app_password)
            logger.info("Gmail authentication successful.")
            return self.mail
        except imaplib.IMAP4.error as e:
            logger.error(f"Gmail IMAP authentication failed: {e}")
            self.disconnect()
            raise ValueError(f"Gmail authentication failed: {e}")
        except Exception as e:
            logger.error(f"Connection failure: {e}")
            self.disconnect()
            raise ConnectionError(f"Failed to connect to Gmail: {e}")

    def disconnect(self):
        """
        Closes the folder connection and logs out securely.
        """
        if self.mail:
            try:
                # If selected folder is open, close it
                if self.mail.state in ('SELECTED', 'AUTH'):
                    try:
                        self.mail.close()
                    except Exception:
                        pass
                self.mail.logout()
                logger.info("Gmail connection closed successfully.")
            except Exception as e:
                logger.warning(f"Error while disconnecting Gmail connection: {e}")
            finally:
                self.mail = None

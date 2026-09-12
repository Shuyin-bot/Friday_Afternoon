import imaplib
import email
import os
from dotenv import load_dotenv
from db_contexts.repos.email_repository import create_email_if_not_exist, does_email_exist

load_dotenv()

def record_new_email(
    email_id: int, 
    from_email: str, 
    subject: str,
) -> bool:
    if create_email_if_not_exist(email_id, from_email, subject):
        print(f"New email recorded: {subject} from {from_email}")
        return True
    return False

def connect_and_retrieve_email(fetch_all: bool = True) -> None:
    # load the env variable
    IMAP_HOST = os.getenv("IMAP_HOST")
    IMAP_PORT = os.getenv("IMAP_PORT")
    IMAP_USERNAME = os.getenv("IMAP_USERNAME")
    IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")
    MAILBOX = os.getenv("MAILBOX", "inbox")

    if not IMAP_HOST or not IMAP_PASSWORD or not IMAP_USERNAME or not IMAP_PORT:
        raise ValueError("make sure all the environment variables are set")
    
    imap = imaplib.IMAP4_SSL(IMAP_HOST)
    imap.login(IMAP_USERNAME, IMAP_PASSWORD)
    imap.select(MAILBOX)

    status, messages = imap.search(None, "ALL" if fetch_all else "UNSEEN")
    if status != "OK":
        raise Exception("Failed to retrieve emails")
    
    for email_id in messages[0].split():
        if does_email_exist(int(email_id.decode('utf8'))):
            continue
        status, msg_data = imap.fetch(email_id, "(RFC822)")

        if status != "OK":
            raise Exception("Error occurred when retrieving email")
        
        email_message = email.message_from_bytes(msg_data[0][1])
        
        content = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    content += part.get_payload(decode=True).decode()
        else:
            content = email_message.get_payload(decode=True).decode()
        
        record_new_email(
            email_id=int(email_id.decode('utf8')),
            from_email=email_message.get("From"),
            subject=email_message.get("Subject"),
        )

    imap.close()
    imap.logout()

if __name__ == "__main__":
    connect_and_retrieve_email()

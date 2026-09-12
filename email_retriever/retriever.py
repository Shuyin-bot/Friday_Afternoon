import imaplib
import email
import os, json
from dotenv import load_dotenv
from db_contexts.repos.email_repository import create_email_if_not_exist, filter_out_seen_emails
from pathlib import Path

load_dotenv()

def record_new_email(
    email_id: int, 
    from_email: str, 
    subject: str,
    content: str
) -> bool:
    data_dir = os.getenv('DATA', 'data')

    if create_email_if_not_exist(email_id, from_email, subject):
        print(f"New email recorded: {subject} from {from_email}")
    
        file_path = Path(f"{data_dir}/emails/{email_id}_email.json")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as fh:
            mp = {
                'email_id':email_id, 
                'from': from_email, 
                'subject': subject, 
                'content': content
            }
            json.dump(mp, fh, indent=4)
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

    email_ids = filter_out_seen_emails(messages[0].split())
    print(f"skipped {len(messages[0].split()) - len(email_ids)}....\nProcessing {len(email_ids)}")

    for email_id in email_ids:
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
            content=content
        )

    imap.close()
    imap.logout()

if __name__ == "__main__":
    connect_and_retrieve_email()

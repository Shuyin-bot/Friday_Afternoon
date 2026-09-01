import imaplib
from email import policy
from email.parser import BytesParser
from dotenv import load_dotenv
import os


def establish_connection() -> (bool, any):
    try:
        imap = imaplib.IMAP4_SSL("outlook.office365.com", 993)
    except:
        return False, None
    return True, imap


def fetch_email(imap, email_id):
    status, data = imap.fetch(email_id, "(RFC822)")
    raw_data = data[0][1]
    msg = BytesParser(policy=policy.default).parsebytes(raw_data)
    print(msg)
    

def check_new_emails(imap):
    pass


if __name__ == "__main__":
    load_dotenv()
    did_conn, imap_conn = establish_connection()
    outlook_pass = os.getenv("OUTLOOK_PASS")
    
    if did_conn:
        res, val = imap_conn.login("pack_flow@outlook.com", outlook_pass)
        imap_conn.select("INBOX")
        stat, unread_mail_bytes = imap_conn.search(None, "UNSEEN")
        unread_email = unread_mail_bytes[0].split()
        fetch_email(imap_conn, unread_email[-1])
        imap_conn.logout()

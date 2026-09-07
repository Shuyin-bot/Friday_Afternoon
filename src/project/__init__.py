import asyncio
from agent_system.llm_classifier import PydanticAIQuotationClassifier
from agent_system.models import AgentContext
from job_queue.models import Job, JobType

async def main() -> None:
    job = Job(
        job_type=JobType.CLASSIFY_EMAIL,
        email_uid=1,
        mailbox="INBOX",
        payload={
            "subject": "2-Step Verification turned on",
  "received_at": "2026-09-04T10:53:08+00:00",
  "plain_text": "[image: Google]\r\n2-Step Verification turned on\r\n\r\n\r\nflow.pack.business@gmail.com\r\n\r\nYour Google Account flow.pack.business@gmail.com is now protected with\r\n2-Step Verification. When you sign in on a new or untrusted device, you\u2019ll\r\nneed your second factor to verify your identity.\r\n\r\n*Don't get locked out!*\r\nYou can add a backup phone or get backup codes to use when you don\u2019t have\r\nyour second factor with you.\r\nYou can review your 2SV settings\r\n<https://accounts.google.com/AccountChooser?Email=flow.pack.business@gmail.com&continue=https://myaccount.google.com/signinoptions/twosv?rfn%3D16%26rfnc%3D1%26eid%3D-3543574515881406505%26et%3D0>\r\nto make changes.\r\nYou can also see security activity at\r\nhttps://myaccount.google.com/notifications\r\nYou received this email to let you know about important changes to your\r\nGoogle Account and services.\r\n\u00a9 2026 Google Ireland Ltd., Gordon House, Barrow Street, Dublin 4, Ireland\r\n",
           }
    )

    context = AgentContext(
        job=job,
        input_data=job.payload
    )

    classifier = PydanticAIQuotationClassifier()
    result = await classifier.run(context)

    print(result.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())

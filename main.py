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
            "subject": "Request for quotation",
            "plain_text": "Please provide pricing for 10 routers.",
            "received_at": "2026-09-04T10:52:53+00:00",
           }
    )

    context = AgentContext(
        job=job,
        input_data=job.payload
    )

    classifier = PydanticAIQuotationClassifier()
    result = await classifier.run(context)

    print(result.model_dump_json(indent=2))

if _name_ == "_main_":
    asyncio.run(main())
from db_contexts.repos.email_repository import get_queued_jobs_by_stat, update_queued_job
from db_contexts.repos.product_repository import get_product_by_sku, search_products
from db_contexts.models.email_retriever_models import JobStatus
from .agents.classifier import get_classifying_agent
from .agents.extractor_agent import get_extractor_agent
from .agents.external_research_agent import get_external_research_agent
from .agents.product_catalog_research_agent import get_internal_research_agent
from .agents.email_draft_agent import get_email_draft_agent
import asyncio
import os
from pydantic_ai.agent import Agent
from pathlib import Path
import json


def get_path_to_email(email_external_id) -> Path:
    return Path.joinpath(Path.cwd(), "data", "emails", f"{email_external_id}_email.json")


def _load_meta(job) -> dict:
    """Load and return the job's meta_data as a dict, tolerating empty/missing data."""
    try:
        return json.loads(job.meta_data or "{}")
    except json.JSONDecodeError:
        return {}


def _save_meta(job, meta: dict, status: JobStatus) -> None:
    update_queued_job(job.id, status, json.dumps(meta))


async def classify_emails():
    jobs = get_queued_jobs_by_stat()
    print(f"retrieved {len(jobs)} jobs to be processed")
    classifier = get_classifying_agent()

    for job in jobs:
        # job.email_id is the FK to retrieved_email.id (internal PK), not
        # the external email_id the retriever/seeder used for the filename
        # — use job.email.email_id instead (see get_queued_jobs_by_stat).
        file_path = get_path_to_email(job.email.email_id)
        email_data = json.loads(file_path.read_text())
        res = await classifier.run(email_data.get('content'))

        meta = _load_meta(job)
        meta["classification"] = res.output.model_dump_json()
        print(meta)

        if not res.output.is_quote:
            _save_meta(job, meta, JobStatus.COMPLETED)
            # file_path.unlink()
            continue
        _save_meta(job, meta, JobStatus.CLASSIFIED)


async def extract_quotations():
    quotation_emails = get_queued_jobs_by_stat(JobStatus.CLASSIFIED)
    print(f"extracting quote from {len(quotation_emails)} emails")
    extractor = get_extractor_agent()

    for job in quotation_emails:
        file_path = get_path_to_email(job.email.email_id)
        email_data = json.loads(file_path.read_text())
        res = await extractor.run(email_data.get("content"))

        meta = _load_meta(job)
        meta["extraction"] = res.output.model_dump_json()
        print(meta)
        _save_meta(job, meta, JobStatus.EXTRACTED)


async def research_companies():
    jobs = get_queued_jobs_by_stat(JobStatus.EXTRACTED)
    print(f"researching {len(jobs)} companies")
    researcher = get_external_research_agent()
    tavily_key_present = bool(os.getenv("TAVILY_API_KEY"))

    for job in jobs:
        meta = _load_meta(job)
        extraction = json.loads(meta.get("extraction", "{}"))
        company = extraction.get("company")

        if not company:
            meta["external_research_skipped"] = "no company extracted"
        elif not tavily_key_present:
            meta["external_research_skipped"] = "TAVILY_API_KEY not configured"
        else:
            res = await researcher.run(f"Research this company: {company}")
            meta["external_research"] = res.output.model_dump_json()

        print(meta)
        # Always advance the job so a missing field cannot stall the pipeline.
        _save_meta(job, meta, JobStatus.RESEARCH_EXT)


async def research_products():
    jobs = get_queued_jobs_by_stat(JobStatus.RESEARCH_EXT)
    print(f"researching {len(jobs)} products")
    researcher = get_internal_research_agent()

    for job in jobs:
        meta = _load_meta(job)
        extraction = json.loads(meta.get("extraction", "{}"))
        # `products` may be missing entirely on jobs seeded/extracted before
        # this field existed; fall back to the old singular `product` key so
        # older meta_data does not silently stop advancing.
        products = extraction.get("products") or (
            [extraction["product"]] if extraction.get("product") else []
        )
        # 只有存在内部产品研究结果时才会生成草稿邮件，否则会跳过草稿阶段，直接进入完成状态。
        if not products:
            meta["internal_research_skipped"] = "no product extracted"
        else:
            # One tool-backed research call per distinct requested product,
            # so a multi-machine request (e.g. "case erector + carton
            # sealer") is not collapsed into a single fuzzy search string.
            results = []
            for product in products:
                res = await researcher.run(f"Find this product in the catalog: {product}")
                entry = {"requested_as": product, **res.output.model_dump()}
                # The research agent's structured output only carries
                # sku/name/category — not the full spec/description text
                # (LLM structured output is not a reliable way to copy a
                # large free-form spec blob verbatim). It has also been
                # observed to leave `sku` empty even when `found` is true
                # and `name` is filled in correctly, so resolve by sku
                # first and fall back to a name lookup before giving up.
                # Once resolved, fetch the grounding facts straight from
                # the DB, so the draft agent can answer technical questions
                # (e.g. "does this handle KLT containers?") and carry any
                # engineering caveats from specs.options, without relying
                # on the LLM to have faithfully repeated them.
                full = None
                if entry.get("found"):
                    if entry.get("sku"):
                        full = get_product_by_sku(entry["sku"])
                    elif entry.get("name"):
                        candidates = search_products(entry["name"])
                        full = next(
                            (c for c in candidates if c.name.lower() == entry["name"].lower()),
                            candidates[0] if candidates else None,
                        )
                if full:
                    entry["sku"] = full.sku
                    entry["name"] = full.name
                    entry["description"] = full.description
                    if full.specs_json:
                        try:
                            entry["specs"] = json.loads(full.specs_json)
                        except json.JSONDecodeError:
                            pass
                results.append(entry)
            meta["internal_research"] = json.dumps(results)

        print(meta)
        _save_meta(job, meta, JobStatus.RESEARCH_INT)


async def draft_emails():
    jobs = get_queued_jobs_by_stat(JobStatus.RESEARCH_INT)
    print(f"drafting {len(jobs)} emails")
    drafter = get_email_draft_agent()

    for job in jobs:
        meta = _load_meta(job)
        internal_research = meta.get("internal_research")
        external_research = meta.get("external_research")

        if not internal_research:
            meta["draft_skipped"] = "no internal research available"
        else:
            prompt = (
                f"Company research on the sender's organisation: "
                f"{external_research or 'not available - do not guess who they are'}\n\n"
                f"Catalog research, one entry per requested product: {internal_research}\n\n"
                "Write a quotation reply email using this information."
            )
            res = await drafter.run(prompt)
            meta["draft"] = res.output.model_dump_json()

        print(meta)
        _save_meta(job, meta, JobStatus.DRAFTED)


async def main():
    await classify_emails()
    await extract_quotations()
    await research_companies()
    await research_products()
    await draft_emails()

if __name__ == "__main__":
    asyncio.run(main())

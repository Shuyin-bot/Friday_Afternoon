from ..extractor_agent import ExtractorOutput, get_extractor_agent
from .tool_logger import log_tool_use


async def email_data_extraction_tool(email: str) -> ExtractorOutput:
    """Extract quotation details from an inbound email."""
    log_tool_use("email_data_extraction_tool")
    extractor = get_extractor_agent()
    res = await extractor.run(email)
    return res.output

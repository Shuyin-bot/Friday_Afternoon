import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("quotation_bot.tools")


def log_tool_use(tool_name: str, details: str = "") -> None:
    message = f"tool used: {tool_name}"
    if details:
        message = f"{message} ({details})"
    logger.info(message)

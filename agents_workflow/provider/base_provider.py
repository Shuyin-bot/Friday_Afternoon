
from dotenv import load_dotenv
import os
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.google import GoogleModel

load_dotenv()

llm_provider = os.getenv('LLM_PROVIDER', None)
api_key = os.getenv("LLM_API_KEY")
llm_model_name = os.getenv("LLM_MODEL")

if not llm_model_name or not api_key:
    raise Exception("Some env variables are missing")

provider = GoogleProvider(api_key=os.getenv("LLM_API_KEY"))
model = GoogleModel(
    model_name=os.getenv("LLM_MODEL"),
    provider=provider
)

if llm_provider == "openai":
    from pydantic_ai.providers.openai import OpenAIProvider
    from pydantic_ai.models.openai import OpenAIChatModel

    provider =  OpenAIProvider(api_key=os.getenv("LLM_API_KEY"))
    model = OpenAIChatModel(
        model_name=os.getenv('LLM_MODEL'),
        provider= provider
    )
elif llm_provider == "ollama":
    from pydantic_ai.providers.ollama import OllamaProvider
    from pydantic_ai.models.ollama import OllamaModel

    provider = OllamaProvider(api_key="", base_url=os.getenv("LLM_BASE_URL"))
    model = OllamaModel(
        model_name=os.get('LLM_MODEL'),
        provider=provider
    )
elif llm_provider == "groq":
    from pydantic_ai.providers.groq import GroqProvider
    from pydantic_ai.models.groq import GroqModel

    provider = GroqProvider(api_key=os.getenv('LLM_API_KEY'))
    model = GroqModel(
        model_name=os.getenv('LLM_MODEL'),
        provider=provider
    )

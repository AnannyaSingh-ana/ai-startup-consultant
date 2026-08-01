import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI (keep for comparison/testing)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")

# Other services
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Demo controls
GENERATION_ENABLED = os.getenv("GENERATION_ENABLED", "true").lower() == "true"
DAILY_REPORT_LIMIT = int(os.getenv("DAILY_REPORT_LIMIT", "50"))
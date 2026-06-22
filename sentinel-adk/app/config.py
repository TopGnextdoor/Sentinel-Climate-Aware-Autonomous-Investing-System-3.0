# Switch GEMINI_ENV=prod before recording the demo video
# Switch GEMINI_ENV=dev for all build and test sessions

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_api_key() -> str:
    gemini_env = os.environ.get("GEMINI_ENV", "dev")
    if gemini_env == "prod":
        key = os.environ.get("GEMINI_API_KEY_PROD")
    else:
        key = os.environ.get("GEMINI_API_KEY_DEV")
    
    if not key:
        raise ValueError(f"Active Gemini API key is missing or empty for environment: {gemini_env}")
    
    # Expose the active key to os.environ so the ADK and Google GenAI SDK pick it up
    os.environ["GEMINI_API_KEY"] = key
    return key

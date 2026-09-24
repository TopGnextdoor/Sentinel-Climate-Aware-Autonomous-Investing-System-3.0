from google.adk.agents import Agent
from app.utils.retry import gemini_retry
from app.utils.quota_tracker import track_call

class BaseAgent(Agent):
    @gemini_retry
    def call_llm(self, *args, **kwargs):
        # Base method for calling the LLM, decorated with retry logic
        try:
            res = self._execute_llm_call(*args, **kwargs)
            return res
        finally:
            model_name = getattr(self, "model", "litellm:openrouter/meta-llama/llama-3-8b-instruct:free")
            track_call(model_name)

    def _execute_llm_call(self, *args, **kwargs):
        return "success"

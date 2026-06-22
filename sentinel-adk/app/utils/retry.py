import random
import logging
from tenacity import retry, retry_if_exception_type, stop_after_attempt
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

logger = logging.getLogger(__name__)

def custom_wait(retry_state) -> float:
    attempt = retry_state.attempt_number  # 1, 2, 3, 4, 5...
    base_wait = 2 ** (attempt - 1)        # 1, 2, 4, 8, 16...
    jitter = random.uniform(0, 1)
    return base_wait + jitter

def log_retry_details(retry_state):
    attempt = retry_state.attempt_number
    wait_time = retry_state.next_action.sleep
    agent_name = "UnknownAgent"
    if retry_state.args:
        self_arg = retry_state.args[0]
        if hasattr(self_arg, 'name'):
            agent_name = self_arg.name
            
    logger.warning(
        f"Retry attempt {attempt} for agent '{agent_name}'. Waiting {wait_time:.2f}s before retrying due to exception: {retry_state.outcome.exception()}"
    )
    print(f"Quota hit — retrying in {wait_time:.2f}s (attempt {attempt}/5)")

gemini_retry = retry(
    retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
    wait=custom_wait,
    stop=stop_after_attempt(5),
    before_sleep=log_retry_details,
    reraise=True
)

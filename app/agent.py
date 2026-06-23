# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import google.auth

from google.adk.agents import SequentialAgent
from google.adk.apps import App
import app.main

from app.agents.climate_agent import climate_agent
from app.agents.financial_agent import financial_agent
from app.agents.simulation_agent import simulation_agent
from app.agents.portfolio_agent import portfolio_agent
from app.agents.trader_agent import trader_agent
from app.agents.guard_agent import guard_agent
from app.agents.explain_agent import explain_agent

from app.config import get_api_key

try:
    get_api_key()
except Exception:
    pass

if not os.environ.get("GEMINI_API_KEY"):
    try:
        _, project_id = google.auth.default()
        if project_id:
            os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    except Exception:
        pass

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

root_agent = SequentialAgent(
    name="sentinel_pipeline",
    sub_agents=[
        climate_agent,
        financial_agent,
        simulation_agent,
        portfolio_agent,
        trader_agent,
        guard_agent,
        explain_agent
    ]
)

app = App(
    root_agent=root_agent,
    name="app",
)

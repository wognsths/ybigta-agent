import httpx
from app.common.types import (
    AgentCard,
    A2AClientJSONError,
)
import json


class A2ACardResolver:
    def __init__(self, base_url, agent_card_path="/.well-known/agent.json"):
        self.base_url = base_url.rstrip("/")
        self.agent_card_path = agent_card_path.lstrip("/")
        ## (db-agent) http://localhost:8001 + / + .well-known/agent.json

    def get_agent_card(self) -> AgentCard:
        """Remote-agent url에 가서 Agent Card를 받아오는 함수"""
        with httpx.Client() as client:
            response = client.get(self.base_url + "/" + self.agent_card_path)
            response.raise_for_status() ## 응답 상태 보여주기 (정상 / 오류 등)
            try:
                return AgentCard(**response.json())
            except json.JSONDecodeError as e:
                raise A2AClientJSONError(str(e)) from e
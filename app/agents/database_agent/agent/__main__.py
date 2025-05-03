# main.py
import os
import logging
from dotenv import load_dotenv
from starlette.responses import JSONResponse

from app.common.server.server import A2AServer
from app.common.types import AgentCard, AgentCapabilities, AgentSkill
from app.common.utils.push_notification_auth import PushNotificationSenderAuth
from .task_manager import AgentTaskManager
from .agent import DBAgent

# 1) 환경변수 & 로깅
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2) JWK 생성
notification_sender_auth = PushNotificationSenderAuth()
notification_sender_auth.generate_jwk()

# 3) 에이전트 메타정보
capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
skill = AgentSkill(
    id="text_to_sql",
    name="Text to SQL",
    description="Converts NL queries into SQL and runs them.",
    tags=["text-to-sql", "database"],
    examples=["Show me the top 5 customers by revenue"]
)
agent_card = AgentCard(
    name="Database Agent",
    description="NL→SQL 에이전트",
    url="http://database-agent:10001/",
    version="1.0.0",
    defaultInputModes=DBAgent.SUPPORTED_CONTENT_TYPES,
    defaultOutputModes=DBAgent.SUPPORTED_CONTENT_TYPES,
    capabilities=capabilities,
    skills=[skill],
)

# 4) 서버 생성
server = A2AServer(
    agent_card=agent_card,
    task_manager=AgentTaskManager(
        agent=DBAgent(),
        notification_sender_auth=notification_sender_auth,
    ),
    host="0.0.0.0",
    port=10001,
)
app = server.app

# 5) 헬스체크
@app.route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok"})

# 6) 분리된 라우터 마운트
from ..routes.query_router import router as query_router
app.include_router(query_router)

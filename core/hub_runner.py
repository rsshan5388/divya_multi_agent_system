
# Hub runner and hub agent extracted

import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agents.hub_agent import hub_agent
APP_NAME="Divya_Multi_Agent_Member"

_session_service = InMemorySessionService()
_runner = None

def _get_runner():
    global _runner
    if _runner is None:
        _runner = Runner(agent=hub_agent, session_service=_session_service, app_name=APP_NAME)
    return _runner

async def call_hub_async(query: str) -> str:
    runner = _get_runner()

    session = await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id="user"
    )
    session_id = session.id   

    content = types.Content(
        role="user",
        parts=[types.Part(text=query)]
    )

    final = "No response"

    async for event in runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            part = event.content.parts[0]
            if part.text:
                final = part.text

    return final

def call_hub_sync(query: str) -> str:
    return asyncio.run(call_hub_async(query))
    #return asyncio.run(call_hub_async(str))

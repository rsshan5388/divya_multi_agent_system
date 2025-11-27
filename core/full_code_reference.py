# Full original file for reference


import os
import re
import json
import random
import asyncio
import traceback
from datetime import date, datetime
from typing import List, Dict, Optional

import feedparser
import requests
from dotenv import load_dotenv
from pathlib import Path

from google.adk.agents import LlmAgent, Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner, Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import load_memory, preload_memory


from google.genai import types
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
POLL1_FOLDER = DATA_DIR / "polls_1"
POLL2_FOLDER = DATA_DIR / "polls_2"
BIRTHDAY_FOLDER = DATA_DIR / "birthdays"
BIRTHDAY_DIR = DATA_DIR / "birthdays"
# PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# POLL1_FOLDER = os.path.join(PROJECT_ROOT, "data", "polls_1")
# POLL2_FOLDER = os.path.join(PROJECT_ROOT, "data", "polls_2")
# BIRTHDAY_FOLDER = os.path.join(PROJECT_ROOT, "data", "birthdays")
# BIRTHDAY_DIR = os.path.join(PROJECT_ROOT, "data", "birthdays")
# POLL1_FOLDER = os.path.join(PROJECT_ROOT, "polls_1")
# POLL2_FOLDER = os.path.join(PROJECT_ROOT, "polls_2")
# BIRTHDAY_FOLDER = os.path.join(PROJECT_ROOT, "birthdays")
# BIRTHDAY_DIR = os.path.join(PROJECT_ROOT, "birthdays")
#BIRTHDAYS_FILE = os.path.join(BIRTHDAY_DIR, "birthdays.json")
AGENT_MODEL="gemini-2.0-flash"
print("✅ ADK components imported successfully.")

load_dotenv()
session_service = InMemorySessionService()
APP_NAME = "Divya_Multi_Agent_Member"
USER_ID = "divya"
SESSION_ID = "divya_session"
session_service = InMemorySessionService()
#GLOBAL_BDAY_SESSION_SERVICE = InMemorySessionService()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is not set. Put it in .env or your environment.")

async def init_session():
    try:
        return await session_service.create_session(
            app_name=APP_NAME, 
            user_id=USER_ID, 
            session_id=SESSION_ID
        )
    except Exception:
        # Ignore if already exists and fetch existing
        return await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID
        )

#print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")
def get_today_birthdays() -> dict:
    """Returns today's birthday entries based on dd-mm.json file."""
    today = date.today().strftime("%d-%m")
    path = BIRTHDAY_FOLDER / f"{today}.json"

    if not path.exists():
        return {
            "date": today,
            "birthdays": [],
            "message": "No birthdays today."
        }

    data = json.loads(path.read_text())

    return {
        "date": today,
        "birthdays": data,
        "message": "Birthday list loaded"
    }

def _load_poll_from_folder(folder: str, day_of_year: int | None = None) -> dict:
    """
    Internal helper to load today's poll JSON from the given folder.

    Supports JSON like:
    {
      "id": "poll1_320",
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "answer_index": 0,              
      "correct_answer": "Apache Hadoop",  
      "explanation": "..."
    }
    """
    if day_of_year is None:
        from datetime import datetime as _dt
        day_of_year = _dt.now().timetuple().tm_yday

    filename = f"{day_of_year:03d}.json"
    path = os.path.join(folder, filename)

    if not os.path.exists(path):
        return {"error": f"No poll file found for day {day_of_year} at {path}"}

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    question = raw.get("question") or raw.get("text")
    options = raw.get("options") or []
    explanation = raw.get("explanation", "")

    answer_index = raw.get("answer_index")
    answer_text = raw.get("correct_answer") or raw.get("answer")

    if isinstance(answer_text, str) and answer_text.lower().startswith("answer:"):
        try:
            line = answer_text.splitlines()[0]
            key = line.split(":", 1)[1].strip().lower().rstrip(".")
            letter_to_idx = {"a": 0, "b": 1, "c": 2, "d": 3}
            if key in letter_to_idx and 0 <= letter_to_idx[key] < len(options):
                answer_index = letter_to_idx[key]
                answer_text = options[answer_index]
        except Exception:
            pass

    if answer_index is None and answer_text and answer_text in options:
        answer_index = options.index(answer_text)

    if not question:
        return {"error": f"Poll file {path} missing 'question' field"}

    return {
        "id": raw.get("id", filename),
        "question": question,
        "options": options,
        "answer_index": answer_index,
        "answer_text": answer_text,
        "correct_answer": answer_text,      
        "explanation": explanation,
        "_source_image": raw.get("_source_image"),
    }

def _load_birthday_from_folder(folder: str, day_month: str | None = None) -> dict:
    """
    Load today's birthday JSON from <folder>/<DD-MM>.json.

    Expected JSON format:
    [
      {
        "name": "Sudarshan",
        "relation": "Friend",
        "age": 34,
        "notes": "AI expert"
      },
      ...
    ]
    """
    
    if day_month is None:
        day_month = datetime.now().strftime("%d-%m")

    filename = f"{day_month}.json"
   #path = os.path.join(folder, filename)
    path = Path(folder) / filename

    print(path)

    
    if not os.path.exists(path):
        return {"error": f"No birthday file found for {day_month} at {path}"}

    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"error": f"Error reading {path}: {e}"}

    
    if not isinstance(data, list):
        return {"error": f"Birthday file {path} must contain a list of entries."}

    
    cleaned = []
    for entry in data:
        if not isinstance(entry, dict):
            continue

        name = entry.get("name")
        if not name:
            continue

        cleaned.append({
            "name": name,
                   })

    if not cleaned:
        return {"error": f"No valid birthday entries in {path}"}

    return {
        "date": day_month,
        "entries": cleaned,
        "file": filename,
        "path": str(path),
    }

# birthday_tool = AgentTool(
#     func=run_today_birthday_greetings(),
#     name="run_today_birthday_greetings",
#     description="Generate birthday wishes for today's date"
# )
   
def get_weekly_job_digest():
    """Return a placeholder weekly job digest."""
    return {
        "jobs": [
            {"link": "https://docs.google.com/forms/d/e/1FAIpQLSdzkGG-oEfSP36n0chep3CcNw2bDaIvPPaK8b93zG52k7wVew/viewform?pli=1&pli=1"},
           
        ]
    }

def web_search(query: str):
    """Simple LLM-based search explanation (not real Google search)."""
    return {
        "query": query,
        "note": "This is a simulated search because ADK 1.19 does not include real web search tool.",
        "result": f"A helpful explanation for: {query}"
    }
def fetch_rss(url: str):
    """Fetch top 2 RSS items from TechCrunch and summarize."""
    try:
        parsed = feedparser.parse(url)
        items = parsed.entries[:2]
        out = []
        for i in items:
            out.append({
                "title": i.title,
                "summary": i.get("summary", "")[:300],
                "link": i.link
            })
        return {"items": out}
    except Exception as e:
        return {"error": str(e)}

def tell_tech_joke(category: str = "random"):
    """Return a fun technical joke (Python, Cloud, AI, DevOps, DB)."""

    jokes = {
        "python": [
            "Why did the Python developer quit? Because they couldn't handle the indentation!",
            "I tried to write a Python joke, but it kept throwing exceptions."
        ],
        "cloud": [
            "Why did the sysadmin go to therapy? Too many unresolved cloud issues.",
            "The cloud is just someone else's computer—don’t tell management."
        ],
        "ai": [
            "My AI told me it needs more data. I told it we all have needs.",
            "I asked my AI for help. It replied: 'Have you tried being less human?'"
        ],
        "devops": [
            "DevOps engineers do it continuously.",
            "Why did the DevOps engineer break up? They needed more space."
        ],
        "db": [
            "Why was the SQL query so sad? It had too many joins.",
            "I asked the DB admin for help—he said: 'SELECT * FROM support WHERE help = true;'"
        ]
    }

def get_today_poll1_question() -> dict:
    """
    Tool: return today's Poll 1 question (from polls_1/<day>.json),
    WITHOUT revealing the answer.

    Intended to be used around 11:30 IST.
    """
    poll = _load_poll_from_folder(POLL1_FOLDER)
    if "error" in poll:
        return poll

    return {
        "id": poll["id"],
        "question": poll["question"],
        "options": poll["options"],
        "_source_image": poll["_source_image"],
    }


def get_today_poll2_question() -> dict:
    """
    Tool: return today's Poll 2 question (from polls_2/<day>.json),
    WITHOUT revealing the answer.

    Intended to be used around 15:30 IST.
    """
    poll = _load_poll_from_folder(POLL2_FOLDER)
    if "error" in poll:
        return poll

    return {
        "id": poll["id"],
        "question": poll["question"],
        "options": poll["options"],
        "_source_image": poll["_source_image"],
    }


def get_today_poll1_answer() -> dict:
    """
    Tool: return today's Poll 1 correct answer + explanation.
    Intended to be used around 12:45 IST.
    """
    poll = _load_poll_from_folder(POLL1_FOLDER)
    if "error" in poll:
        return poll

    answer_text = poll.get("answer_text") or poll.get("correct_answer")

    return {
        "id": poll["id"],
        "question": poll["question"],
        "answer": answer_text,
        "answer_index": poll.get("answer_index"),
        "explanation": poll.get("explanation"),
        "_source_image": poll.get("_source_image"),
    }


def get_today_poll2_answer() -> dict:
    """
    Tool: return today's Poll 2 correct answer + explanation.
    Intended to be used around 17:15 IST.
    """
    poll = _load_poll_from_folder(POLL2_FOLDER)
    if "error" in poll:
        return poll

    answer_text = poll.get("answer_text") or poll.get("correct_answer")

    return {
        "id": poll["id"],
        "question": poll["question"],
        "answer": answer_text,
        "answer_index": poll.get("answer_index"),
        "explanation": poll.get("explanation"),
        "_source_image": poll.get("_source_image"),
    }


POLL_ANSWERS: Dict[tuple, str] = {}  


def submit_poll_answer(poll_id: str, user_id: str, chosen_option: str) -> dict:
    """Record a user's answer to a poll in local memory."""
    key = (poll_id, user_id)
    POLL_ANSWERS[key] = chosen_option
    return {
        "status": "ok",
        "poll_id": poll_id,
        "user_id": user_id,
        "chosen_option": chosen_option,
    }


def get_poll_answer_stats(poll_id: str) -> dict:
    """
    Compute a simple distribution of answers for a poll from the in-memory store.

    Returns:
        {"question_id": ..., "counts": {...}, "total": N}
    """
    counts: Dict[str, int] = {}
    total = 0

    for (qid, _uid), opt in POLL_ANSWERS.items():
        if qid == poll_id:
            counts[opt] = counts.get(opt, 0) + 1
            total += 1

    return {"question_id": poll_id, "counts": counts, "total": total}


def search_blog(query: str) -> dict:
    """
    Search internal blogs for relevant posts matching the query.

    For now returns stub data. Replace with your own API / RSS index.

    Returns:
        {"results": [ {title, url, snippet}, ... ]}
    """
    sample = [
        {
            "title": "Building multi-agent systems with ADK",
            "url": "https://example.com/blog/adk-multi-agents",
            "snippet": (
                "Overview of designing coordinator and specialist agents for "
                "RSS feeds, polls, and more using ADK."
            ),
        },
        {
            "title": "Using ADK to power WhatsApp-style bots",
            "url": "https://example.com/blog/adk-whatsapp-bots",
            "snippet": (
                "How we wired ADK agents to pull RSS, send polls, jokes, and "
                "respond to user questions in chat groups."
            ),
        },
    ]

    filtered = [b for b in sample if query.lower() in b["snippet"].lower()
                or query.lower() in b["title"].lower()]

    return {"results": filtered or sample}



def fetch_rss_feed(url: str, limit: int = 3) -> dict:
    """
    Fetch RSS entries from the given URL and return a short summary.

    Returns:
        {"feed_title": ..., "items": [ {title, link, summary}, ... ]}
    """
    parsed = feedparser.parse(url)
    items = []

    for entry in parsed.entries[:limit]:
        items.append({
            "title": getattr(entry, "title", ""),
            "link": getattr(entry, "link", ""),
            "summary": getattr(entry, "summary", "")[:280],
        })

    return {
        "feed_title": getattr(parsed.feed, "title", "Unknown feed"),
        "items": items,
    }
def load_birthday_file(prefix: str) -> dict:
    """
    Loads today's birthday JSON file.
    prefix = 'DD-MM' format
    """
    filename = f"{prefix}.json"
    path = os.path.join(BIRTHDAY_DIR, filename)

    if not os.path.exists(path):
        return {"entries": []}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {"entries": data}
def get_today_prefix() -> str:
    today = datetime.today()
    return today.strftime("%d-%m")  

def build_birthday_prompt(entry: dict) -> str:
    name = entry.get("name", "Friend")
    
    

    return (
        f"Generate a birthday greeting.\n"
        f"Name: {name}\n"
        "Return only the greeting text."
    )

def run_today_birthday_greetings() -> list[str]:
    """
    Load birthdays from today's DD-MM.json and generate greetings
    using the birthday_agent.
    """

    
    resp = _load_birthday_from_folder(BIRTHDAY_DIR)
    entries = resp.get("entries", [])

    if not entries:
        print("[BIRTHDAY_AGENT] No birthdays today.")
        return []

    greetings = []

    for entry in entries:
        prompt = _build_birthday_prompt(entry)

        content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
        session = asyncio.run(init_session())
        runner = Runner(
        agent=birthday_agent, # The agent we want to run
    app_name=APP_NAME,   # Associates runs with our app
    session_service=session_service # Uses our session manager
     )
       

        final_text_parts = []

        
        events = runner.run(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content,
        )

        for event in events:
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text_parts.append(part.text)

        greeting = "".join(final_text_parts).strip()
        greetings.append(greeting)

    return greetings

def run_today_birthday_greetings_sync() -> list[str]:
    """
    Synchronous birthday tool for ADK. NO asyncio inside.
    """

    prefix = datetime.now().strftime("%d-%m")
    resp = _load_birthday_from_folder(BIRTHDAY_DIR, prefix)
    entries = resp.get("entries", [])

    if not entries:
        return ["No birthdays today."]

    greetings = []

    for entry in entries:
        prompt = _build_birthday_prompt(entry)

        # Synchronous runner (no async)
        runner = InMemoryRunner(birthday_agent)

        content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)],
        )

        final_parts = []

        for event in runner.run(
            user_id="bday-user",
            session_id="birthday-session",
            new_message=content,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if part.text:
                        final_parts.append(part.text)

        greetings.append("".join(final_parts))

    return greetings


# retry_config = types.HttpRetryOptions(
#     attempts=5,  
#     exp_base=7,  
#     initial_delay=1,
#     http_status_codes=[429, 500, 503, 504],  
# )
async def run_today_birthday_greetings_async() -> list[str]:
    prefix = get_today_prefix()
    resp = _load_birthday_from_folder(BIRTHDAY_DIR, prefix)
    entries = resp.get("entries", [])

    if not entries:
        print("[BIRTHDAY_AGENT] No birthdays today.")
        return []

    greetings = []

    for entry in entries:

        prompt = _build_birthday_prompt(entry)

        content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)],
        )

        
        runner = InMemoryRunner(birthday_agent)

        
        raw_name = entry.get("name", "user")
        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "", raw_name)
        session_id = f"bday-session-{clean_name}"

        
        await runner.session_service.create_session(
            app_name="birthday_app",
            user_id="birthday-user",
            session_id=session_id
        )

        final_text = []

        
        async for event in runner.run_async(
            user_id="birthday-user",
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if part.text:
                        final_text.append(part.text)

        greetings.append("".join(final_text).strip())

    return greetings
def load_today_birthdays():
    prefix = datetime.now().strftime("%d-%m")
    resp = _load_birthday_from_folder(BIRTHDAY_DIR, prefix)
    return resp

def _build_birthday_prompt(entry: dict) -> str:
    name = entry.get("name", "Friend")
   

    return (
        f"Generate a birthday greeting.\n\n"
        f"Name: {name}\n"
        f"Return only the greeting text."
    )

birthday_agent = LlmAgent(
    name="birthday_agent_v1",
    model=AGENT_MODEL, # Can be a string for Gemini or a LiteLlm object
    description="Provides birthday greets to memebers.",
    instruction="""
        You are an AI assistant specializing in crafting well-written, professional, and personalized birthday messages. Your output must always follow the constraints below.

        PURPOSE:
        Generate thoughtful, workplace-appropriate birthday wishes tailored for colleagues, managers, and professional contacts. Messages must be warm, respectful, and uplifting, with a touch of light humor when appropriate, while maintaining professionalism.

        GUIDELINES:

        1. PERSONALIZATION
        - Always address the recipient by name.
        - If details are provided (role, contributions, qualities), incorporate them naturally.
        - End the message with the sender's name.

        2. TONE & STYLE
        - Maintain a professional, respectful, and warm tone.
        - Light humor is allowed but avoid sarcasm or risky jokes.
        - Avoid romantic, emotional, or overly informal language.
        - Avoid exaggerated praise or slang.

        3. MESSAGE STRUCTURE
        Opening:
            Provide a warm birthday greeting addressing the recipient by name. and tell them how they are importangt to techsync group
        
        Body:
            Acknowledge the person's qualities, contributions, teamwork, leadership, or professionalism.
        
        Closing:
               Always end the message with:
              "Best wishes,    Divya from Techsync Group"

        4. RESTRICTIONS
        - No emojis.
        - No romantic or overly personal content.
        - No religious or political references unless explicitly requested.
        - Keep the message moderate in length and workplace-appropriate.

        5. OUTPUT FORMAT
        - Produce only the final birthday message.
        - Do not output explanations, notes, or bullet points.
        When the user asks any of the following:
         "whose birthday today"
       - "any birthday today"
       - "today birthday"
       - "show birthdays"
       - "list birthdays"
       - "who all have birthday today"
       -  "is there any birthday"
       ALWAYS call the tool `run_today_birthday_greetings` OR `load_birthday_file`
        and return the results.

         Never ask the user for a name in these cases.

        only ask for a name when:
        - the user wants to generate a personal greeting for a specific person.

    """,
    #   tools=[
    #     run_today_birthday_greetings_sync,
    #     load_birthday_file
    # ],# Pass the function directly
    tools =[load_today_birthdays],
)
# run_today_birthday_greetings_tool = AgentTool(
#     func=run_today_birthday_greetings, 
#     name="run_today_birthday_greetings",
#     description="Load today's birthday list and generate greetings."
# )

# load_birthday_file_tool = AgentTool(
#     func=load_birthday_file,
#     name="load_birthday_file",
#     description="Load birthday JSON entries for today."
# )
birthday_tool = AgentTool(birthday_agent)
# birthday_agent = LlmAgent(
#     name="birthday_agent",
#     model=Gemini(model_name="gemini-2.5-flash"),
#     tools=[],
# )

rss_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="rss_agent",
    description="Reads RSS feeds and summarises them for posting to groups.",
    instruction=(
        "You specialise in summarising RSS feeds for a WhatsApp/Telegram group.\n"
        "Use the tool `fetch_rss_feed` to actually fetch the feed content.\n"
        "Then summarise the top items in a short, clear, bullet-style update. "
        "Keep it friendly, under 5 bullets, and mention the feed title."
         "Whenever RSS data is provided by the fetch_rss() tool, ALWAYS output:\n"
        "• Title\n• Link\n• Very short summary\n\n"
        "Never skip the link. Never omit fields."
    ),
    tools=[fetch_rss_feed],
)

rss_tool = AgentTool(rss_agent)


poll_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="poll_agent",
    description="Manages daily polls: questions, answers, and explanations.",
    instruction=(
        "You are in charge of daily MCQ-style polls.\n"
        "- Use `get_today_poll1_question` and `get_today_poll2_question` "
        "  to fetch today's questions from JSON files.\n"
        "- Use `get_today_poll1_answer` and `get_today_poll2_answer` "
        "  to reveal the correct answer and explanation.\n"
        "- When the user asks for the poll question, respond ONLY with the MCQ: "
        "  question + options labelled A/B/C/D.\n"
        "- When the user asks for the answer, respond with: "
        "  'Correct Answer: <option>' and then the explanation.\n"
    ),
    tools=[
        get_today_poll1_question,
        get_today_poll2_question,
        get_today_poll1_answer,
        get_today_poll2_answer,
        submit_poll_answer,
        get_poll_answer_stats,
    ],
)

poll_tool = AgentTool(poll_agent)


fun_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="fun_agent",
    description="Agent that tells short, clever technical / programming jokes.",
    instruction=(
        "You are a witty technical comedian.\n\n"
        "Your job:\n"
        "- Always tell a short, clever joke related to technology, programming, data, AI, networking, or similar topics.\n"
        "- If the user gives a topic (e.g. 'Python', 'C')"
        "  make the joke about that topic.\n"
        "- If no topic is given, choose any popular tech theme (coding bugs, deployments, version control, etc.).\n"
        "- Make the joke genuinely humorous and a bit playful, with a clear punchline.\n"
        "- Keep it within 1–3 lines, suitable for an office or professional WhatsApp group.\n"
        "- No dark humor, no insults, no offensive content, no sensitive topics.\n"
        "- Return ONLY the joke text, no explanation or extra comments."
    ),
    tools=[],  
)

fun_tool = AgentTool(fun_agent)


search_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="search_agent",
    description="Answers factual questions using Google search.",
    instruction=(
        "You answer factual technical questions. "
        "Always use the `google_search` tool to get up-to-date information "
        "before answering. Then summarise clearly in 3–6 bullet points."
    ),
    tools=[google_search],
)

search_tool = AgentTool(search_agent)


blog_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="blog_agent",
    description="Fetches information from internal blogs / knowledge base.",
    instruction=(
        "You answer questions by searching our internal blogs.\n"
        "Use the `search_blog` tool to find relevant posts.\n"
        "Then summarise 1–3 posts that best match the query and include "
        "their titles and URLs in the answer."
    ),
    tools=[search_blog],
)

blog_tool = AgentTool(blog_agent)

def _load_birthday_entries() -> list[dict]:
    """Load birthday JSON from birthdays/DD-MM.json."""
    today_prefix = datetime.now().strftime("%d-%m")
    filename = f"{today_prefix}.json"
    filepath = Path(BIRTHDAY_DIR) / filename
    #filepath = os.path.join(BIRTHDAY_DIR, filename)

    print(f"[BIRTHDAY_AGENT] Looking for file: {filepath}")

    if not os.path.exists(filepath):
        print(f"[BIRTHDAY_AGENT] No file for today ({today_prefix}).")
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[BIRTHDAY_AGENT] Error reading {filepath}: {e}")
        return []

    
    if isinstance(data, list):
        print(f"[BIRTHDAY_AGENT] Loaded {len(data)} birthday entries.")
        return data

    print(f"[BIRTHDAY_AGENT] Invalid JSON format in {filename}. Expected array.")
    return []

def _today_dd_mm() -> str:
    """Return today's date as 'DD-MM' (matches JSON format)."""
    return date.today().strftime("%d-%m")



def _find_today_birthday_entries() -> list[dict]:
    """Filter birthday entries whose 'date' matches today."""
    all_entries = _load_birthday_entries()
    today = _today_dd_mm()
    return [e for e in all_entries if e.get("date") == today]


def _build_birthday_promptold(entry: dict) -> str:
    """
    Build the prompt that will be sent to the LLM (birthday_agent).
    """
    name = entry.get("name", "the person")
    today_str = date.today().strftime("%d %B")  

    relation = entry.get("relation", "Techsync Friends")
    context = entry.get(
        "context",
        "They are part of our extended professional and learning network."
    )

    return (
        f"Today is {today_str}, and it's {name}'s birthday.\n\n"
        f"Relation: {relation}\n"
        f"Context: {context}\n\n"
        "Write a warm, respectful, and slightly informal birthday message "
        "that could be posted in a WhatsApp/Telegram group.\n"
        "- Mention the person's name.\n"
        "- Keep it 2–4 lines.\n"
        "- Focus on positivity, learning, growth, and gratitude.\n"
        "- Do NOT include emojis (we will add them ourselves if needed).\n"
        "- Keep it generic enough that it can be sent by the whole group, "
        "not just one individual.\n"
    )




def run_today_birthday_greetings1() -> list[str]:
    """
    Synchronous wrapper around run_today_birthday_greetings_async.

    Can be called from a scheduler (e.g., `schedule` or cron).
    """
    try:
        return asyncio.run(run_today_birthday_greetings_async())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            coro = run_today_birthday_greetings_async()
            return loop.run_until_complete(coro)  
        raise



tech_conversation_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="tech_conversation_agent",
    description="Tech-only conversational agent. Restricted to technology topics.",
    instruction=(
        "You are a friendly technical assistant.\n\n"
        "Rules:\n"
        "- You must only discuss technology: programming, data, cloud, DevOps, AI, "
        "  security, networking, architecture, tools, frameworks, etc.\n"
        "- If the user asks anything non-technical, politely refuse and explain that "
        "you are restricted to tech topics, then gently steer back to something tech.\n"
        "- Address the user by name if it is provided in the prompt.\n"
        "- Keep explanations clear, structured, and not too long.\n"
        "- Use bullet points or short paragraphs when helpful.\n"
    ),
    tools=[],
)


def tech_chat(name: str, query: str) -> str:
    """
    Conversational helper:
    - Takes user's name and query
    - Sends to tech_conversation_agent
    - Returns the reply as plain text
    """
    prompt = (
        f"The user's name is {name}.\n"
        f"Respond to them directly using their name at least once.\n\n"
        f"User question: {query}"
    )

    content = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )

    runner = InMemoryRunner(tech_conversation_agent)
    final_text_parts: List[str] = []

    for event in runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_text_parts.append(part.text)

    return "".join(final_text_parts) if final_text_parts else "No response received."






hub_agent = Agent(
    model="gemini-2.0-flash",
    name="hub_agent",
    description=(
        "Multi-utility assistant that can handle RSS feeds, polls, "
        "general questions, jokes, birthdays, and blog information."
    ),
    instruction=(
        "You are the main assistant and router.\n\n"
        "Routing rules:\n"
        "- If the user asks for news, RSS feeds, or 'post updates', "
        "  use the `rss_agent` tool.\n"
        "- If the user wants poll questions, to vote, or see results, "
        "  use the `poll_agent` tool.\n"
        "- If the user has factual or up-to-date web questions, "
        "  use the `search_agent` tool.\n"
        "- If the user wants information from our blogs, "
        "  use the `blog_agent` tool.\n"
        "- If the user wants jokes or light conversation, "
        "  use the `fun_agent` tool.\n"
        "- For birthday greetings, call `birthday_agent` only if the user asks "
        "  specifically for birthday wishes.\n"
        "- For general technology-only chat, you can directly answer, but keep it technical.\n"
        "\n"
        "When answering, never show raw JSON. Always give clean, formatted text."
    ),
    tools=[
        rss_tool,
        poll_tool,
        fun_tool,
        search_tool,
        blog_tool,
        birthday_tool,
        
    ],
)



_session_service = InMemorySessionService()
_runner = None

def _get_runner() -> Runner:
    global _runner
    if _runner is None:
        _runner = Runner(
            agent=hub_agent,               
            session_service=_session_service,
            app_name=APP_NAME              
        )
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


async def _setup_runner_for_cli() -> Runner:
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    runner = Runner(agent=hub_agent, app_name=APP_NAME, session_service=session_service)
    return runner


async def chat_once(runner: Runner, user_text: str) -> None:
    if not user_text.strip():
        return

    user_content = types.Content(
        role="user",
        parts=[types.Part(text=user_text)],
    )

    final_text_parts: List[str] = []

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=user_content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_text_parts.append(part.text)

    if final_text_parts:
        print("\nAssistant:\n", "".join(final_text_parts), "\n")
    else:
        print("\nAssistant: (no final response received)\n")


def _safe_health_ping(agent_obj, test_prompt: str) -> str:
    """
    Generic helper to ping an LlmAgent/Agent with a tiny prompt
    using InMemoryRunner. If anything explodes, we catch and return
    the exception name.
    """
    try:
        runner = InMemoryRunner(agent_obj)
        content = types.Content(
            role="user",
            parts=[types.Part(text=test_prompt)],
        )
        text_chunks: list[str] = []
        
        for event in runner.run(
            new_message=content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        text_chunks.append(part.text)
        if "".join(text_chunks).strip():
            return "OK"
        return "NO_OUTPUT"
    except Exception as e:
        return f"ERROR: {e.__class__.__name__}"
    


def _check_rss_agent() -> str:
    return _safe_health_ping(rss_agent, "Health check: give one-line RSS summary.")


def _check_poll_agents() -> str:
    try:
        _ = get_today_poll1_question()
        _ = get_today_poll2_question()
        return "OK"
    except Exception as e:
        return f"ERROR: {e.__class__.__name__}"


def _check_fun_agent() -> str:
    return _safe_health_ping(fun_agent, "Health check: tell 1 short programming joke.")


def _check_search_agent() -> str:
    return _safe_health_ping(
        search_agent,
        "Health check: short summary of 'What is Google ADK?'.",
    )

def _check_birthday_agent() -> str:
    """
    Health check for birthday agent.
    If no birthdays exist today, it should still return OK.
    Only actual failures in prompt-building should return ERROR.
    """
    try:
        entries = _find_today_birthday_entries()

        
        if not entries:
            return "OK"

        
        first = entries[0]
        _build_birthday_prompt(first)

        return "OK"

    except Exception as e:
        return f"ERROR: {e.__class__.__name__}"
 
def _check_tech_conversation_agent() -> str:
    return _safe_health_ping(
        tech_conversation_agent,
        "Health check: explain what ADK is in one sentence.",
    )


def check_agents_health() -> dict:
    """
    Run lightweight health checks for all agents.
    Ensures consistent OK / ERROR / WARNING classification.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    raw = {
        "rss_agent": _check_rss_agent(),
        "poll_agents": _check_poll_agents(),
        "fun_agent": _check_fun_agent(),
        "search_agent": _check_search_agent(),
        "birthday_agent": _check_birthday_agent(),
        "tech_conversation_agent": _check_tech_conversation_agent(),
    }

    
    normalized = {}
    for name, status in raw.items():
        if status == "OK":
            normalized[name] = "OK"
        elif status.startswith("ERROR"):
            normalized[name] = status
        else:
            
            normalized[name] = "WARNING"

    healthy = sum(1 for v in normalized.values() if v == "OK")
    error = sum(1 for v in normalized.values() if v.startswith("ERROR"))
    warning = sum(1 for v in normalized.values() if v == "WARNING")

    return {
        "timestamp": timestamp,
        "agents": normalized,
        "healthy": healthy,
        "warning": warning,
        "error": error,
    }


def format_agents_health_report(system_name: str = "Multi-Agent System") -> str:
    """
    Format the health check dict as a WhatsApp/Telegram-ready message.
    """
    status = check_agents_health()

    lines: list[str] = []
    lines.append("*🩺 Agent Health Update*")
    lines.append("")
    lines.append(f"*System:* {system_name}")
    lines.append(f"*Time:* {status['timestamp']}")
    lines.append("")
    lines.append(f"*Agents Healthy:* {status['healthy']} ✅")
    lines.append(f"*Agents Warning:* {status['warning']} ⚠️")
    lines.append(f"*Agents Error:* {status['error']} ❌")
    lines.append("")
    lines.append("_Details:_")

    for name, val in status["agents"].items():
        if val == "OK":
            lines.append(f"- {name}: ✅ OK")
        elif val.startswith("ERROR"):
            lines.append(f"- {name}: ❌ {val}")
        else:
            lines.append(f"- {name}: ⚠️ {val}")

    lines.append("")
    lines.append("*Next Health Check:* 09:20 tomorrow 🕘")

    return "\n".join(lines)

def check_agents_health_via_hub() -> dict:
    """
    Generate agent health by calling each agent through the hub
    instead of pinging them directly.
    This matches real execution and avoids LLM TypeErrors.
    """

    tests = {
        "rss_agent": "post latest news",
        "poll_agents": "give today's poll question",
        "fun_agent": "tell a tech joke",
        "search_agent": "search what is ADK",
        "blog_agent": "get information about blogs",
        "birthday_agent": "generate birthday wishes for today",
        "tech_conversation_agent": "explain cloud computing",
    }

    results = {}
    for agent_name, query in tests.items():
        try:
            output = call_hub_sync(query).strip()
            if output and "sorry" not in output.lower():
                results[agent_name] = "OK"
            else:
                results[agent_name] = f"WARNING: Unexpected output"
        except Exception as e:
            results[agent_name] = f"ERROR: {type(e).__name__}"

    healthy = sum(1 for x in results.values() if x == "OK")
    error = sum(1 for x in results.values() if x.startswith("ERROR"))
    warning = sum(1 for x in results.values() if x.startswith("WARNING"))

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "agents": results,
        "healthy": healthy,
        "warning": warning,
        "error": error,
    }

def format_agents_health_report_via_hub():
    status = check_agents_health_via_hub()
    lines = []
    lines.append("*🩺 Agent Health (Hub-Based)*")
    lines.append(f"*Time:* {status['timestamp']}")
    lines.append("")
    lines.append(f"*Healthy:* {status['healthy']}  ✅")
    lines.append(f"*Warning:* {status['warning']} ⚠️")
    lines.append(f"*Error:* {status['error']} ❌")
    lines.append("")
    lines.append("_Details:_")
    for agent, stat in status["agents"].items():
        if stat == "OK":
            lines.append(f"- {agent}: ✅ OK")
        else:
            lines.append(f"- {agent}: ❌ {stat}")
    return "\n".join(lines)

async def main_cli():
    print("Starting multi-content hub agent CLI. Type 'exit' to quit.\n")

    runner = await _setup_runner_for_cli()

    while True:
        try:
            user_text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if user_text.lower() in {"exit", "quit"}:
            print("Bye!")
            break

        await chat_once(runner, user_text)


if __name__ == "__main__":
    asyncio.run(main_cli())

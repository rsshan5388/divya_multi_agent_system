# divya_multi_agent_system
The Divya Multi-Agent Avatar System is a robust, fully-automated, hub-and-spoke multi-agent architecture built on Google’s Agent Development Kit  across multiple communication channels. The system blends structured tool-based agents, LLM-only agents, and time-driven schedulers to create a unified, extensible AI assistant for daily operational use.

Below is a **professional, GitHub-ready README.md** tailored specifically for your **Divya Multi-Agent System** using Google ADK, with birthday/poll/RSS/search/blog/fun agents and a hub-and-spoke architecture.

A fully modular, hub-and-spoke multi-agent architecture built on **Google’s Agent Development Kit (ADK)**.
This system enables intelligent automation of **daily workflows**, including:

* 🎉 Birthday message generation
* 📊 Automated polls (questions + answers)
* 📰 RSS feed summarisation
* 🔍 Web & internal blog search
* 🤖 Tech-only conversational chatbot
* 😂 Fun/joke generator
* 🧠 Central hub agent for routing
* 🛠 Extensible tool ecosystem
* 🗂 Data-driven content via JSON files
* 💬 CLI interactive chat

---

# 🔥 **Features**

## 🧠 1. Hub-and-Spoke Multi-Agent Architecture

A single **hub_agent** intelligently routes user queries to specialised agents:

| Agent                       | Purpose                                          |
| --------------------------- | ------------------------------------------------ |
| **rss_agent**               | Fetch & summarise RSS feeds                      |
| **poll_agent**              | Provide daily poll questions & answers           |
| **birthday_agent**          | List today’s birthdays & generate greetings      |
| **search_agent**            | Perform factual queries using Google search tool |
| **blog_agent**              | Query internal blogs (stubbed for now)           |
| **fun_agent**               | Tell short technical jokes                       |
| **tech_conversation_agent** | Tech-only conversational support                 |

The hub_agent ensures clean routing, extensibility, and system coherence.

---

## 🎉 2. Birthday Automation

* JSON files stored as: `data/birthdays/DD-MM.json`
* Each file contains a list of birthday entries:

```json
[
  { "name": "Sudarshan" },
  { "name": "Sneha" }
]
```

* Asking:

```
whose birthday today
any birthday today
today birthday
```

→ Automatically invokes `load_today_birthdays()`
→ birthday_agent generates a human-friendly response.

---

## 📊 3. Poll Management System

Polls are stored under:

* `data/polls_1/001.json` … `365.json`
* `data/polls_2/001.json` … `365.json`

The poll_agent handles:

* Today’s poll 1 question
* Today’s poll 2 question
* Today’s poll answers
* Explanation
* User voting & memory tracking

---

## 📰 4. RSS Feed Summaries

rss_agent uses `fetch_rss_feed()` to:

* Fetch top RSS articles
* Produce summarised bullet points
* Include links and titles

---

## 🔍 5. Search and Blog Tools

* **search_agent** wraps `google_search()`
* **blog_agent** wraps `search_blog()`
  (stubbed with sample data for now)

---

## 💬 6. Interactive CLI

Run:

```bash
python main.py
```

You get an interactive chat:

```
You: whose birthday today
Assistant: Today's birthdays:
• Sudarshan
• Sneha
```

---

# 📁 **Project Structure**

```
divya_multi_agent_system_full/
│
├── agents/
│   ├── hub_agent.py
│   ├── birthday_agent.py
│   ├── poll_agent.py
│   ├── rss_agent.py
│   ├── fun_agent.py
│   ├── search_agent.py
│   ├── blog_agent.py
│   └── tech_conversation_agent.py
│
├── core/
│   ├── full_code_reference.py   # All tools & helpers
│   ├── hub_runner.py            # Hub sync/async wrappers
│   └── health_check.py          # Agent health diagnostics
│
├── data/
│   ├── birthdays/
│   │   └── 27-11.json
│   ├── polls_1/
│   │   └── 331.json
│   └── polls_2/
│       └── 331.json
│
├── main.py                      # CLI interactive entry point
└── README.md
```

---

# ⚙️ **Installation**

### 1. Clone the repo

```bash
git clone https://github.com/rsshan5388/divya-multi-agent-system.git
cd divya-multi-agent-system
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

```env
GOOGLE_API_KEY=your_api_key_here
GEMINI_API_KEY=optional_if_applicable
```

---

# ▶️ **How to Run**

### **Start CLI**

```bash
python main.py
```

### **Sample queries**

```
whose birthday today
any birthday today
give today's poll question
post latest news
tell a tech joke
search what is ADK
```

---

# 🧩 **How to Add a New Agent**

1. Create a new agent file under `agents/`
2. Define a tool or function under `core/full_code_reference.py`
3. Register it inside `hub_agent.tools`
4. Add routing rules in hub instruction

Instantly live.

---

# 🧪 **Health Checks**

Run:

```python
from core.full_code_reference import format_agents_health_report
print(format_agents_health_report())
```

Produces a WhatsApp-friendly formatted report:

```
🩺 Agent Health Update
System: Multi-Agent System
Time: 2025-11-27

Agents Healthy: 6
Agents Warning: 0
Agents Error: 0
```

---

# 🚀 **Key Design Highlights**

* Uses Google ADK for agent session management & orchestration
* File-driven automation for birthday/poll ingestion
* All tools are **pure Python**, fully ADK-compliant
* Highly extensible modular architecture
* Clean separation between business logic + agents + hub routing
* Works entirely offline except for LLM calls

---

# 🛡 License

MIT License.
Feel free to modify, extend, or use for your own agentic projects.

---

# 👩‍💻 Author

**R Sudarshan**




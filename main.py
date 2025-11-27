
# ===========================
# Interactive Multi-Agent CLI
# ===========================

import sys
from core.hub_runner import call_hub_sync

BANNER = """
===========================================
   🧠 Divya Multi-Agent Interactive System
===========================================

Ask me anything, for example:
 • whose birthday today
 • give me today's poll questions
 • what is poll 1 answer
 • post latest news
 • search what is ADK
 • tell me a tech joke
 • generate birthday wish for Sneha
 • get information about blogs
 • explain cloud computing

Type 'exit', 'quit', or 'bye' to stop.
-------------------------------------------
"""

def main():
    print(BANNER)

    while True:
        try:
            user_input = input("You: ").strip()

            # Exit conditions
            if user_input.lower() in ("exit", "quit", "bye"):
                print("\nAgent: Goodbye! Have a great day! 👋\n")
                break

            if not user_input:
                continue

            # Pass user query to the hub agent
            try:
                response = call_hub_sync(user_input)
            except Exception as e:
                response = f"[ERROR] Something went wrong: {e}"

            print(f"\nAgent: {response}\n")

        except KeyboardInterrupt:
            print("\n\nAgent: Session closed. Goodbye! 👋\n")
            sys.exit(0)

if __name__ == "__main__":
    main()

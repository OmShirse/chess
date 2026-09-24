import asyncio
import sys
import subprocess

def ensure_dependencies():
    try:
        import google.antigravity
    except ImportError:
        print("[INFO] 'google-antigravity' not found. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-antigravity", "--break-system-packages"])

ensure_dependencies()

from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig

async def run_daily_update():
    """
    Runs the daily update using the Antigravity Python SDK.
    The agent is instructed to check project state, research scope, update a report, and push to git.
    """
    # Configure the agent with capabilities enabled (allows running commands, writing files)
    config = LocalAgentConfig(
        system_instructions="You are an autonomous project manager and AI developer.",
        capabilities=CapabilitiesConfig(),
    )

    prompt = """
    Perform the following daily maintenance tasks for this project:
    1. Check the current state of the project (e.g., git status, recent commits, current files).
    2. Research further scope of the project and suggest next steps or improvements.
    3. Document your findings and the current state in a file named `daily_project_scope.md`.
    4. Commit the changes to git with the message "chore: daily project state and scope update" and push them to the remote repository.
    """

    while True:
        print("Starting daily Antigravity project update...")
        try:
            async with Agent(config) as agent:
                # Send the prompt to the agent
                response = await agent.chat(prompt)

                # Stream the agent's response to the console
                async for token in response:
                    sys.stdout.write(token)
                    sys.stdout.flush()
                print("\n\n[SUCCESS] Daily update task completed.")
        except Exception as e:
            print(f"\n[ERROR] An error occurred during the update: {e}")

        print("[INFO] Sleeping for 24 hours (86400 seconds) before the next update...")
        # Wait for 24 hours without relying on external cron/schedulers
        await asyncio.sleep(86400)

if __name__ == "__main__":
    print("Initializing Antigravity Daily Updater Script...")
    try:
        asyncio.run(run_daily_update())
    except KeyboardInterrupt:
        print("\n[INFO] Updater stopped by user.")


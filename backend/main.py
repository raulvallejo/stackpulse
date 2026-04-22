from dotenv import load_dotenv
load_dotenv()

from agents.orchestrator import run_pipeline

run_pipeline()
print("Pipeline complete")

from dotenv import load_dotenv
load_dotenv(override=True)

from policy_rag.server import run_server


if __name__ == "__main__":
    run_server()

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional in bundled test/runtime environments
    def load_dotenv(*args, **kwargs):  # type: ignore[override]
        return False

load_dotenv(override=True)

import os
from policy_rag.server import run_server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(host="0.0.0.0", port=port)

import sys
import os
import glob
import uvicorn

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Auto-detect local virtualenv site-packages if not already active
venv_win = os.path.join(backend_dir, ".venv", "Lib", "site-packages")
venv_nix = glob.glob(os.path.join(backend_dir, ".venv", "lib", "python*", "site-packages"))
if os.path.exists(venv_win) and venv_win not in sys.path:
    sys.path.insert(0, venv_win)
elif venv_nix and venv_nix[0] not in sys.path:
    sys.path.insert(0, venv_nix[0])

if __name__ == "__main__":
    env_file = os.path.join(backend_dir, ".env")
    if os.path.exists(env_file):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file, override=True)
        except Exception:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip("'\"")

    port = int(os.getenv("PORT", 5052))
    print("\n============================================================")
    print("TRAVELOGIX FASTAPI BACKEND SERVER - Chatbot (Web / API)")
    print("Host     : 0.0.0.0")
    print(f"Port     : {port}")
    print(f"Docs URL : http://localhost:{port}/docs")
    print(f"Health   : http://localhost:{port}/health")
    print("============================================================\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("UVICORN_RELOAD", "false").lower() == "true",
        log_level="info"
    )



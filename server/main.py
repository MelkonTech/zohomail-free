"""Entry point — run with: uvicorn server.main:app or python main.py"""
import uvicorn
from server.api import app  # noqa: F401


def main():
    uvicorn.run("server.api:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()

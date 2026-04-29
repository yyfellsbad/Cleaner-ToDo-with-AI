from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def build_client() -> ChatOpenAI:
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0") or 0)
    api_key_value = os.getenv("OPENAI_API_KEY")

    if not api_key_value:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")

    kwargs = {"model": model_name, "temperature": temperature, "api_key": api_key_value}
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)


def main() -> int:
    client = build_client()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a connectivity test. Reply with a short friendly greeting.",
            ),
            ("human", "Say hello in one short sentence."),
        ]
    )
    chain = prompt | client
    response = chain.invoke({})
    print(response.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

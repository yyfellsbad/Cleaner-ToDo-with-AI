from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.constants.defaults import LLM_DEFAULTS
from ui.i18n import t

if TYPE_CHECKING:
    from storage.setting_repo import SettingRepo

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

_KEYS = ("llm_api_key", "llm_base_url", "llm_model", "llm_chat_prompt")


class LLMConfigManager:
    _instance: LLMConfigManager | None = None

    @classmethod
    def instance(cls) -> LLMConfigManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._repo: SettingRepo | None = None
        self._on_changed: Callable[[], None] | None = None
        self.api_key: str = ""
        self.base_url: str = ""
        self.model: str = ""
        self.chat_prompt: str = ""

    # ── load / save ────────────────────────────────────────

    def load(self, repo: SettingRepo, on_changed: Callable[[], None] | None = None) -> None:
        self._repo = repo
        self._on_changed = on_changed
        self.api_key = repo.get("llm_api_key") or os.getenv("OPENAI_API_KEY", LLM_DEFAULTS["llm_api_key"])
        self.base_url = repo.get("llm_base_url") or os.getenv("OPENAI_BASE_URL", LLM_DEFAULTS["llm_base_url"])
        self.model = repo.get("llm_model") or os.getenv("OPENAI_MODEL", LLM_DEFAULTS["llm_model"])
        self.chat_prompt = repo.get("llm_chat_prompt") or LLM_DEFAULTS["llm_chat_prompt"]

    def _save(self) -> None:
        if not self._repo:
            return
        self._repo.set("llm_api_key", self.api_key)
        self._repo.set("llm_base_url", self.base_url)
        self._repo.set("llm_model", self.model)
        self._repo.set("llm_chat_prompt", self.chat_prompt)

    def _notify(self) -> None:
        if self._on_changed:
            self._on_changed()

    # ── setters ────────────────────────────────────────────

    def set_api_key(self, value: str) -> None:
        self.api_key = value.strip()
        self._save()
        self._notify()

    def set_base_url(self, value: str) -> None:
        url = value.strip()
        if url and not url.startswith(("http://", "https://")):
            return
        self.base_url = url.rstrip("/")
        self._save()
        self._notify()

    def set_model(self, value: str) -> None:
        v = value.strip()
        if not v:
            return
        self.model = v
        self._save()
        self._notify()

    def set_chat_prompt(self, value: str) -> None:
        v = value.strip()
        if not v or len(v) > 2000:
            return
        self.chat_prompt = v
        self._save()
        self._notify()

    # ── test connection ────────────────────────────────────

    def test_connection(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, t("test.no_key")
        try:
            kwargs: dict = {"model": self.model, "temperature": 0, "api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            llm = ChatOpenAI(**kwargs)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Reply with exactly: OK"),
                ("human", "ping"),
            ])
            chain = prompt | llm
            response = chain.invoke({})
            content = getattr(response, "content", "")
            if content:
                return True, t("test.success", content.strip()[:50])
            return False, t("test.empty")
        except Exception as ex:
            return False, t("test.fail", str(ex)[:100])

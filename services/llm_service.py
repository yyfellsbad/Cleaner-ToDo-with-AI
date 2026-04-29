from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict, Field

from core.constants.enums import TaskActionType
from core.models.task import TaskRecord
from services.task_service import TaskService


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


@dataclass(slots=True)
class ToolDefinition:
    name: str
    description: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class PendingAction:
    token: str
    intent: "PlannedTaskIntent"
    matched_task_ids: list[int] = field(default_factory=list)


@dataclass(slots=True)
class AssistantResult:
    message: str
    action: TaskActionType = TaskActionType.UNKNOWN
    tasks: list[TaskRecord] = field(default_factory=list)
    pending_confirmation: bool = False
    confirmation_token: str | None = None
    suggested_actions: list[str] = field(default_factory=list)


TaskActionName = Literal[
    "create",
    "list",
    "update",
    "delete",
    "complete",
    "uncomplete",
    "help",
    "unknown",
]

ToolName = Literal[
    "create_task",
    "list_tasks",
    "update_task",
    "delete_task",
    "complete_task",
    "uncomplete_task",
    "help",
    "unknown",
]


class TaskPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tool: ToolName = Field(description="The tool to execute")
    action: TaskActionName = Field(description="Normalized action name")
    task_name: str | None = Field(
        default=None, description="Core task title for create, 1-15 chars"
    )
    target_text: str | None = Field(
        default=None, description="Target task text for update/delete/complete"
    )
    new_text: str | None = Field(default=None, description="New task title when updating")
    date_text: str | None = Field(
        default=None, description="Date text such as 明天 or 2026-04-28"
    )
    status: str = Field(default="all", description="all, active, or completed")
    completed: bool | None = Field(
        default=None, description="Whether the task should be completed"
    )
    keyword: str | None = Field(default=None, description="Search keyword for listing")
    batch_count: int = Field(default=1, description="How many tasks to create")
    delete_scope: str = Field(default="matched", description="matched, all, or current")
    complete_scope: str = Field(default="matched", description="matched, all, or current")
    confirmation_required: bool = Field(
        default=False, description="Whether delete requires confirmation"
    )
    reply: str | None = Field(
        default=None, description="Optional short reply when the tool is unknown or chat-like"
    )


@dataclass(slots=True)
class PlannedTaskIntent:
    action: TaskActionType
    raw_text: str
    task_name: str | None = None
    target_text: str | None = None
    new_text: str | None = None
    task_date: date | None = None
    completed: bool | None = None
    status: str = "all"
    keyword: str | None = None
    batch_count: int = 1
    delete_scope: str = "matched"
    complete_scope: str = "matched"
    confidence: float = 0.0


class LLMService:
    def __init__(self, task_service: TaskService | None = None):
        self.task_service = task_service or TaskService()
        self._pending_actions: dict[str, PendingAction] = {}
        self._planner = self._build_planner()
        self._chat_model = self._build_chat_model()

    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="create_task",
                description="Create a new task from user language.",
                arguments={
                    "task_name": "string",
                    "date_text": "optional string",
                },
            ),
            ToolDefinition(
                name="list_tasks",
                description="List tasks or search existing tasks.",
                arguments={
                    "status": "all|active|completed",
                    "keyword": "optional string",
                },
            ),
            ToolDefinition(
                name="update_task",
                description="Rename, reschedule, or toggle a task.",
                arguments={
                    "target_text": "string",
                    "new_text": "optional string",
                    "date_text": "optional string",
                    "completed": "optional bool",
                },
            ),
            ToolDefinition(
                name="delete_task",
                description="Delete a task. Always requires confirmation.",
                arguments={"target_text": "string"},
            ),
        ]

    def system_prompt(self) -> str:
        tool_list = "\n".join(
            f"- {tool.name}: {tool.description}" for tool in self.tools()
        )
        return (
            "你是一个待办任务结构化提取器，只输出符合 schema 的 JSON，不要解释，不要 Markdown。\n\n"
            "## 输出要求\n"
            "- 必须输出 tool 和 action 字段\n"
            "- tool 必须是：create_task, list_tasks, update_task, delete_task, complete_task, uncomplete_task, help, unknown\n"
            "- action 必须是：create, list, update, delete, complete, uncomplete, help, unknown\n"
            "- task_name 只保留核心任务名，不包含前缀、日期、数量、尾部修饰词\n"
            "- date_text 只提日期词或标准日期文本，不要把整句塞进去\n"
            "- batch_count 是整数；没有明确数量时填 1\n"
            "- 删除操作要设置 confirmation_required=true\n"
            "- 如果不是任务操作，tool/action 都输出 unknown\n\n"
            "## 示例\n"
            "输入：为我增加明天开会的命令\n"
            "输出：{\"tool\":\"create_task\",\"action\":\"create\",\"task_name\":\"开会\",\"date_text\":\"明天\",\"batch_count\":1,\"delete_scope\":\"matched\",\"complete_scope\":\"matched\",\"confirmation_required\":false}\n\n"
            "输入：帮我加5条待办\n"
            "输出：{\"tool\":\"create_task\",\"action\":\"create\",\"task_name\":null,\"batch_count\":5,\"delete_scope\":\"matched\",\"complete_scope\":\"matched\",\"confirmation_required\":false}\n\n"
            "输入：完成所有任务\n"
            "输出：{\"tool\":\"complete_task\",\"action\":\"complete\",\"target_text\":null,\"complete_scope\":\"all\",\"confirmation_required\":false}\n\n"
            "输入：删除待办A\n"
            "输出：{\"tool\":\"delete_task\",\"action\":\"delete\",\"target_text\":\"待办A\",\"delete_scope\":\"matched\",\"confirmation_required\":true}\n\n"
            "## 当前工具\n"
            f"{tool_list}"
        )

    def plan(self, text: str) -> PlannedTaskIntent:
        if self._planner is None:
            return self._unknown_intent(text)

        try:
            response = self._planner.invoke(
                {
                    "system_prompt": self.system_prompt(),
                    "user_input": text,
                    "today": self.task_service.resolve_date(None).isoformat(),
                }
            )
            payload = getattr(response, "content", response)
            return self._plan_to_intent(text, self._decode_plan_payload(payload))
        except Exception:
            return self._unknown_intent(text)

    def process(
        self,
        text: str,
        confirmed: bool = False,
        confirmation_token: str | None = None,
        current_status: str = "all",
    ) -> AssistantResult:
        intent = self.plan(text)
        if intent.action == TaskActionType.UNKNOWN:
            chat_reply = self.chat(text)
            if chat_reply and "不可用" not in chat_reply:
                return AssistantResult(
                    message=chat_reply,
                    action=intent.action,
                    suggested_actions=[tool.name for tool in self.tools()],
                )
            return AssistantResult(
                message="我暂时没有识别出具体任务操作。你可以试试：帮我添加一个待办、帮我把开会改成周五、删除待办xxx。",
                action=intent.action,
                suggested_actions=[tool.name for tool in self.tools()],
            )

        if intent.action == TaskActionType.HELP:
            return AssistantResult(
                message="我可以帮你新增、查看、修改、完成、取消完成和删除任务。删除前会先确认。",
                action=intent.action,
                suggested_actions=[tool.name for tool in self.tools()],
            )

        if intent.action == TaskActionType.LIST:
            tasks = self.task_service.list_tasks(
                status=intent.status,
                keyword=intent.keyword or intent.target_text,
            )
            return AssistantResult(
                message=self._format_task_list(tasks),
                action=intent.action,
                tasks=tasks,
            )

        if intent.action == TaskActionType.CREATE:
            if not intent.task_name:
                return AssistantResult(
                    message="我识别到的是新增任务，但还缺少任务内容。比如：帮我添加一个待办：明天开会。",
                    action=intent.action,
                )
            created = self.task_service.create_tasks(
                intent.task_name,
                max(1, intent.batch_count),
                intent.task_date,
            )
            if len(created) == 1:
                return AssistantResult(
                    message=f"已添加待办：{created[0].name}",
                    action=intent.action,
                    tasks=created,
                )
            return AssistantResult(
                message=f"已批量添加 {len(created)} 条待办。",
                action=intent.action,
                tasks=created,
            )

        if intent.action == TaskActionType.UPDATE:
            matched = self._resolve_matches(intent.target_text)
            if not matched:
                return AssistantResult(
                    message="没有找到匹配的任务。你可以补充更准确的名字。",
                    action=intent.action,
                )
            if len(matched) > 1:
                return AssistantResult(
                    message=self._format_ambiguity(matched),
                    action=intent.action,
                    tasks=matched,
                )
            task = matched[0]
            updated = self.task_service.update_task(
                task.id,
                name=intent.new_text,
                task_date=intent.task_date,
                completed=intent.completed,
            )
            return AssistantResult(
                message=f"已更新任务：{updated.name}",
                action=intent.action,
                tasks=[updated],
            )

        if intent.action in {TaskActionType.COMPLETE, TaskActionType.UNCOMPLETE}:
            if intent.complete_scope == "all":
                matched = self.task_service.list_tasks(status="all")
            elif intent.complete_scope == "current":
                matched = self.task_service.list_tasks(status=current_status)
            else:
                matched = self._resolve_matches(intent.target_text)

            if not matched:
                return AssistantResult(
                    message="没有找到需要更新完成状态的任务。",
                    action=intent.action,
                )

            if len(matched) > 1 and intent.complete_scope == "matched":
                return AssistantResult(
                    message=self._format_ambiguity(matched),
                    action=intent.action,
                    tasks=matched,
                )

            completed = intent.action == TaskActionType.COMPLETE
            updated_tasks: list[TaskRecord] = []
            for task in matched:
                if task.id is None:
                    continue
                updated_tasks.append(
                    self.task_service.mark_complete(task.id, completed)
                )

            status_text = "完成" if completed else "未完成"
            if len(updated_tasks) == 1:
                return AssistantResult(
                    message=f"已标记为{status_text}：{updated_tasks[0].name}",
                    action=intent.action,
                    tasks=updated_tasks,
                )
            return AssistantResult(
                message=f"已将 {len(updated_tasks)} 条任务标记为{status_text}。",
                action=intent.action,
                tasks=updated_tasks,
            )

        if intent.action == TaskActionType.DELETE:
            if intent.delete_scope == "all":
                matched = self.task_service.list_tasks(status="all")
            elif intent.delete_scope == "current":
                matched = self.task_service.list_tasks(status=current_status)
            else:
                matched = self._resolve_matches(intent.target_text)
            if not matched:
                return AssistantResult(
                    message="没有找到要删除的任务。",
                    action=intent.action,
                )
            if len(matched) > 1 and intent.delete_scope == "matched":
                return AssistantResult(
                    message=self._format_ambiguity(matched),
                    action=intent.action,
                    tasks=matched,
                )

            if not confirmed or not confirmation_token:
                token = str(uuid4())
                self._pending_actions[token] = PendingAction(
                    token=token,
                    intent=intent,
                    matched_task_ids=[
                        task.id for task in matched if task.id is not None
                    ],
                )
                if intent.delete_scope == "all":
                    prompt = f"请确认删除全部任务（共 {len(matched)} 条）。"
                elif intent.delete_scope == "current":
                    prompt = f"请确认删除当前筛选中的任务（共 {len(matched)} 条）。"
                else:
                    prompt = f"请确认删除：{matched[0].name}"
                return AssistantResult(
                    message=prompt,
                    action=intent.action,
                    tasks=matched,
                    pending_confirmation=True,
                    confirmation_token=token,
                )

            pending = self._pending_actions.get(confirmation_token)
            if pending is None:
                return AssistantResult(
                    message="确认令牌已失效，请重新发起删除请求。",
                    action=intent.action,
                )
            deleted_tasks = self.task_service.delete_tasks(pending.matched_task_ids)
            self._pending_actions.pop(confirmation_token, None)
            deleted_name = (
                deleted_tasks[0].name
                if len(deleted_tasks) == 1
                else f"{len(deleted_tasks)} 条任务"
            )
            return AssistantResult(
                message=f"已删除任务：{deleted_name}",
                action=intent.action,
                tasks=deleted_tasks,
            )

        return AssistantResult(
            message="我已收到指令，但还无法执行这类操作。",
            action=intent.action,
        )

    def confirm_delete(self, confirmation_token: str) -> AssistantResult:
        pending = self._pending_actions.get(confirmation_token)
        if pending is None:
            return AssistantResult(message="没有找到待确认的删除操作。")

        deleted_tasks = self.task_service.delete_tasks(pending.matched_task_ids)
        self._pending_actions.pop(confirmation_token, None)
        return AssistantResult(
            message=f"已删除 {len(deleted_tasks)} 条任务。",
            action=TaskActionType.DELETE,
            tasks=deleted_tasks,
        )

    def chat(self, text: str) -> str:
        if self._chat_model is None:
            return "聊天模型当前不可用。请先配置 OPENAI_API_KEY，或稍后再试。"

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一个简洁友好的中文助手。可以正常聊天；如果用户问到待办操作，也可以先解释再建议他用任务指令。",
                ),
                ("human", "{user_input}"),
            ]
        )
        chain = prompt | self._chat_model
        try:
            response = chain.invoke({"user_input": text})
            return getattr(response, "content", "") or "我暂时没有生成回复。"
        except Exception:
            return "聊天服务暂时不可用，请稍后再试。"

    def _build_planner(self):
        if ChatOpenAI is None or ChatPromptTemplate is None:
            return None

        model_name = self._env("OPENAI_MODEL", "gpt-4o-mini")
        base_url = self._env("OPENAI_BASE_URL")
        temperature = float(self._env("OPENAI_TEMPERATURE", "0") or 0)
        api_key = self._env("OPENAI_API_KEY")
        if not api_key:
            return None

        llm_kwargs: dict[str, Any] = {"model": model_name, "temperature": temperature}
        if base_url:
            llm_kwargs["base_url"] = base_url

        llm = ChatOpenAI(**llm_kwargs).bind(response_format={"type": "json_object"})
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                (
                    "human",
                    "当前日期：{today}\n\n用户输入：{user_input}\n\n请严格只输出一个 JSON 对象，禁止 Markdown、解释和多余文本。",
                ),
            ]
        )
        return prompt | llm

    def _build_chat_model(self):
        if ChatOpenAI is None:
            return None

        model_name = self._env("OPENAI_MODEL", "gpt-4o-mini")
        base_url = self._env("OPENAI_BASE_URL")
        temperature = float(self._env("OPENAI_TEMPERATURE", "0.4") or 0.4)
        api_key = self._env("OPENAI_API_KEY")
        if not api_key:
            return None

        llm_kwargs: dict[str, Any] = {"model": model_name, "temperature": temperature}
        if base_url:
            llm_kwargs["base_url"] = base_url
        return ChatOpenAI(**llm_kwargs)

    def _plan_to_intent(self, raw_text: str, plan: TaskPlan) -> PlannedTaskIntent:
        action = self._action_from_plan(plan.tool, plan.action)
        task_date = None
        if plan.date_text:
            task_date = self.task_service.resolve_date(plan.date_text)

        return PlannedTaskIntent(
            action=action,
            raw_text=raw_text,
            task_name=(plan.task_name or "").strip() or None,
            target_text=plan.target_text or plan.task_name,
            new_text=plan.new_text,
            task_date=task_date,
            completed=plan.completed,
            status=plan.status,
            keyword=plan.keyword,
            batch_count=max(1, plan.batch_count) if plan.batch_count else 1,
            delete_scope=plan.delete_scope,
            complete_scope=plan.complete_scope,
            confidence=0.99,
        )

    def _action_from_plan(
        self, tool_value: str | None, action_value: str | None
    ) -> TaskActionType:
        tool_mapping: dict[str, TaskActionType] = {
            "create_task": TaskActionType.CREATE,
            "list_tasks": TaskActionType.LIST,
            "update_task": TaskActionType.UPDATE,
            "delete_task": TaskActionType.DELETE,
            "complete_task": TaskActionType.COMPLETE,
            "uncomplete_task": TaskActionType.UNCOMPLETE,
            "help": TaskActionType.HELP,
            "unknown": TaskActionType.UNKNOWN,
        }
        action_mapping: dict[str, TaskActionType] = {
            "create": TaskActionType.CREATE,
            "list": TaskActionType.LIST,
            "update": TaskActionType.UPDATE,
            "delete": TaskActionType.DELETE,
            "complete": TaskActionType.COMPLETE,
            "uncomplete": TaskActionType.UNCOMPLETE,
            "help": TaskActionType.HELP,
            "unknown": TaskActionType.UNKNOWN,
        }
        tool_normalized = (tool_value or "unknown").strip().lower()
        action_normalized = (action_value or "unknown").strip().lower()
        return tool_mapping.get(
            tool_normalized,
            action_mapping.get(action_normalized, TaskActionType.UNKNOWN),
        )

    def _unknown_intent(self, raw_text: str) -> PlannedTaskIntent:
        return PlannedTaskIntent(action=TaskActionType.UNKNOWN, raw_text=raw_text)

    def _decode_plan_payload(self, payload: Any) -> TaskPlan:
        if isinstance(payload, TaskPlan):
            return payload

        if isinstance(payload, str):
            text = payload.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
                text = re.sub(r"\s*```$", "", text)
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                text = text[start : end + 1]
            data = json.loads(text)
        elif isinstance(payload, dict):
            data = payload
        else:
            data = json.loads(str(payload))

        if not isinstance(data, dict):
            raise ValueError("LLM plan payload must be a JSON object")

        return TaskPlan.model_validate(data)

    def _resolve_matches(self, target_text: str | None) -> list[TaskRecord]:
        if not target_text:
            return []
        target = target_text.strip()
        if not target:
            return []
        exact = [task for task in self.task_service.list_tasks() if task.name == target]
        if exact:
            return exact
        return self.task_service.search_tasks(target)

    def _format_task_list(self, tasks: list[TaskRecord]) -> str:
        if not tasks:
            return "当前没有待办任务。"
        lines = ["当前任务列表："]
        for index, task in enumerate(tasks, start=1):
            status = "完成" if task.completed else "未完成"
            lines.append(f"{index}. {task.name} [{status}] {task.date.isoformat()}")
        return "\n".join(lines)

    def _format_ambiguity(self, tasks: list[TaskRecord]) -> str:
        lines = ["我找到了多个可能匹配的任务，请再明确一点："]
        for task in tasks[:5]:
            lines.append(f"- {task.name}")
        return "\n".join(lines)

    def _env(self, key: str, default: str | None = None) -> str | None:
        from os import getenv

        value = getenv(key)
        if value is None or value == "":
            return default
        return value

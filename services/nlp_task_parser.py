from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from core.constants.enums import TaskActionType


@dataclass(slots=True)
class ParsedTaskIntent:
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


_CREATE_KEYWORDS = (
    "添加",
    "新增",
    "增加",
    "创建",
    "加一个",
    "帮我加",
    "记一个",
    "建立",
    "加",
)
_DELETE_KEYWORDS = ("删除", "移除", "删掉", "取消", "清除")
_UPDATE_KEYWORDS = ("修改", "编辑", "改成", "改为", "更新", "调整")
_LIST_KEYWORDS = (
    "查看",
    "查询",
    "列出",
    "显示",
    "有哪些",
    "剩下什么",
    "待办有哪些",
    "任务有哪些",
)
_COMPLETE_KEYWORDS = ("完成", "标记完成", "设为完成", "已完成", "勾选")
_UNCOMPLETE_KEYWORDS = ("未完成", "取消完成", "设为未完成", "取消勾选")
_CREATE_PREFIX_PATTERN = re.compile(
    r"^(?:(?:今天|明天|后天|本周|下周|接下来\d+天|接下来\d+日|接下来)(?:\s*)?)?"
    r"(?:帮我|请|麻烦)?(?:\s*)?"
    r"(?:添加|新增|增加|创建|加一个|加|记一个|建立|安排|提醒)?(?:\s*)?"
    r"(?:一个|一条|个|条)?(?:\s*)?"
    r"(?:待办|任务|事情)?(?:\s*)?"
)
_CN_NUM_MAP = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _extract_quoted(text: str) -> str | None:
    patterns = (
        r'"([^"]+)"',
        r"'([^']+)'",
        r"“([^”]+)”",
        r"‘([^’]+)’",
        r"《([^》]+)》",
        r"【([^】]+)】",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def _strip_prefix(text: str) -> str:
    prefixes = ("帮我", "请", "麻烦", "你能", "能不能", "我想", "我需要")
    stripped = text.strip()
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if stripped.startswith(prefix):
                stripped = stripped[len(prefix) :].strip()
                changed = True
    return stripped


def _contains_date_signal(text: str) -> bool:
    if any(
        keyword in text for keyword in ("今天", "明天", "后天", "today", "tomorrow")
    ):
        return True
    return bool(re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}", text))


def _parse_date(text: str) -> date | None:
    today = date.today()
    if "明天" in text or "tomorrow" in text.lower():
        return today.fromordinal(today.toordinal() + 1)
    if "后天" in text:
        return today.fromordinal(today.toordinal() + 2)
    if "今天" in text or "today" in text.lower():
        return today

    for pattern in (
        r"(\d{4}-\d{1,2}-\d{1,2})",
        r"(\d{4}/\d{1,2}/\d{1,2})",
        r"(\d{1,2}/\d{1,2})",
        r"(\d{1,2}-\d{1,2})",
    ):
        match = re.search(pattern, text)
        if not match:
            continue
        value = match.group(1)
        if "/" in value:
            parts = value.split("/")
            if len(parts) == 3:
                year, month, day = parts
                return date(int(year), int(month), int(day))
            month, day = parts
            return date(today.year, int(month), int(day))
        parts = value.split("-")
        if len(parts) == 3:
            year, month, day = parts
            return date(int(year), int(month), int(day))
        month, day = parts
        return date(today.year, int(month), int(day))

    return None


def _extract_count(text: str) -> int:
    match = re.search(r"(\d+)\s*(?:条|个|项|件|task|tasks)", text, flags=re.IGNORECASE)
    if match:
        return max(1, int(match.group(1)))

    day_match = re.search(r"(?:接下来)?\s*(\d+)\s*天", text)
    if day_match:
        return max(1, int(day_match.group(1)))

    cn_day_match = re.search(r"(?:接下来)?\s*([一二两三四五六七八九十])\s*天", text)
    if cn_day_match:
        return _CN_NUM_MAP.get(cn_day_match.group(1), 1)

    return 1


def _extract_create_name(text: str) -> str:
    """
    从用户输入中提取核心任务名。
    策略：逐步移除修饰词、语气词、时间词等，保留核心任务内容。
    """
    value = text.strip()
    
    # 第一步：移除所有创建动作前缀（帮我、请、麻烦等）
    value = _CREATE_PREFIX_PATTERN.sub("", value)
    
    # 第二步：移除日期相关词汇（明天、后天、今天等）
    value = re.sub(r"(?:明天|后天|今天|这?周|下?周|接下来\d+天|接下来\d+日)", "", value).strip()
    
    # 第三步：移除数量词（5条、3个等）
    value = re.sub(r"^\d+\s*(?:条|个|项|件)[\s的]*", "", value).strip()
    value = re.sub(r"\d+\s*(?:条|个|项|件)$", "", value).strip()
    
    # 第四步：移除通用词汇（任务、待办、事情、命令等）
    value = re.sub(r"^(?:待办|任务|事情|提醒|命令|备忘|日程|安排|的?)", "", value).strip()
    value = re.sub(r"(?:待办|任务|事情|提醒|命令|备忘|日程|安排)$", "", value).strip()
    
    # 第五步：按"的"分割，优先取前面的部分（"明天开会的命令" → "开会"）
    if "的" in value:
        # 如果有"的"字，通常"的"前面是核心任务，"的"后面是修饰
        before_de = value.split("的")[0].strip()
        after_de = value.split("的")[-1].strip()
        
        # 优先用前面部分
        if 1 <= len(before_de) <= 20:
            value = before_de
        elif 1 <= len(after_de) <= 20:
            value = after_de
    
    # 第六步：再次清理剩余的虚词（把、将、请等）
    value = re.sub(r"^(?:把|将|请|麻烦|帮我|我想|我需要|能不能|你能)", "", value).strip()
    
    # 第七步：如果还是太长（>15字），可能包含了多个任务，取第一个句子或词组
    if len(value) > 15:
        # 尝试按标点分割
        for sep in ("，", "、", " ", "和"):
            if sep in value:
                value = value.split(sep)[0].strip()
                if 1 <= len(value) <= 15:
                    break
    
    # 最后再清一遍特殊字符
    value = re.sub(r"^[，、：；\s]+|[，、：；\s]+$", "", value).strip()
    
    return value


def _is_implicit_create(text: str) -> bool:
    signals = ("接下来", "记得", "提醒", "安排", "待办", "任务")
    return any(signal in text for signal in signals)


def _has_explicit_non_create_action(text: str) -> bool:
    action_keywords = (
        *_DELETE_KEYWORDS,
        *_UPDATE_KEYWORDS,
        *_LIST_KEYWORDS,
        *_COMPLETE_KEYWORDS,
        *_UNCOMPLETE_KEYWORDS,
    )
    return any(keyword in text for keyword in action_keywords)


def parse_task_intent(text: str) -> ParsedTaskIntent:
    normalized = _clean_text(text)
    body = _strip_prefix(normalized)

    if any(keyword in body for keyword in _DELETE_KEYWORDS) and not any(
        keyword in body for keyword in _UNCOMPLETE_KEYWORDS
    ):
        delete_scope = "matched"
        if any(flag in body for flag in ("所有", "全部", "all")):
            delete_scope = "all"
        elif "当前" in body or "current" in body:
            delete_scope = "current"

        target = _extract_quoted(body)
        if target is None:
            target = re.sub(
                r"^(?:把|将)?(?:删除|移除|删掉|取消|清除)(?:一下|掉|掉了)?", "", body
            ).strip()
        if delete_scope in {"all", "current"}:
            target = None
        return ParsedTaskIntent(
            action=TaskActionType.DELETE,
            raw_text=text,
            target_text=target or None,
            delete_scope=delete_scope,
            confidence=0.86,
        )

    if any(keyword in body for keyword in _UPDATE_KEYWORDS):
        rename_match = re.search(
            r"(?:把|将)?(.+?)(?:改成|改为|更新为|修改为)(.+)", body
        )
        if rename_match:
            target_text = rename_match.group(1).strip()
            new_text = rename_match.group(2).strip()
            return ParsedTaskIntent(
                action=TaskActionType.UPDATE,
                raw_text=text,
                target_text=target_text,
                new_text=new_text,
                confidence=0.88,
            )

        target = _extract_quoted(body)
        new_text = None
        if target:
            remainder = body.split(target, 1)[-1]
            new_text = remainder.strip() or None
        return ParsedTaskIntent(
            action=TaskActionType.UPDATE,
            raw_text=text,
            target_text=target or body,
            new_text=new_text,
            task_date=_parse_date(body) if _contains_date_signal(body) else None,
            confidence=0.72,
        )

    if (
        any(keyword in body for keyword in _COMPLETE_KEYWORDS)
        and not any(keyword in body for keyword in _UNCOMPLETE_KEYWORDS)
        and any(keyword in body for keyword in ("完成", "标记", "设为", "勾选"))
    ):
        complete_scope = "matched"
        if any(flag in body for flag in ("所有", "全部", "all")):
            complete_scope = "all"
        elif "当前" in body or "current" in body:
            complete_scope = "current"

        target = _extract_quoted(body)
        if target is None:
            target = re.sub(
                r"^(?:帮我)?(?:把)?(?:任务|待办)?(?:都)?(?:标记)?(?:设为)?(?:勾选为)?(?:已)?完成",
                "",
                body,
            ).strip()
        if complete_scope in {"all", "current"}:
            target = None
        return ParsedTaskIntent(
            action=TaskActionType.COMPLETE,
            raw_text=text,
            target_text=target or None,
            completed=True,
            complete_scope=complete_scope,
            confidence=0.82,
        )

    if any(keyword in body for keyword in _UNCOMPLETE_KEYWORDS):
        complete_scope = "matched"
        if any(flag in body for flag in ("所有", "全部", "all")):
            complete_scope = "all"
        elif "当前" in body or "current" in body:
            complete_scope = "current"

        target = _extract_quoted(body)
        if target is None:
            target = re.sub(
                r"^(?:帮我)?(?:把)?(?:任务|待办)?(?:都)?(?:标记)?(?:设为)?(?:取消)?(?:勾选)?(?:为)?(?:未)?完成",
                "",
                body,
            ).strip()
        if complete_scope in {"all", "current"}:
            target = None
        return ParsedTaskIntent(
            action=TaskActionType.UNCOMPLETE,
            raw_text=text,
            target_text=target or None,
            completed=False,
            complete_scope=complete_scope,
            confidence=0.82,
        )

    if any(keyword in body for keyword in _LIST_KEYWORDS):
        status = "all"
        if "未完成" in body or "待办" in body or "active" in body:
            status = "active"
        if "已完成" in body or "完成" in body or "completed" in body:
            status = "completed"
        return ParsedTaskIntent(
            action=TaskActionType.LIST,
            raw_text=text,
            status=status,
            keyword=_extract_quoted(body),
            confidence=0.91,
        )

    if any(keyword in body for keyword in _CREATE_KEYWORDS):
        count = _extract_count(body)
        task_name = _extract_quoted(body)
        if task_name is None:
            task_name = _extract_create_name(body)
        task_name = re.sub(r"\d+\s*(?:条|个|项|件)", "", task_name or "").strip()
        return ParsedTaskIntent(
            action=TaskActionType.CREATE,
            raw_text=text,
            task_name=task_name or None,
            task_date=_parse_date(body) if _contains_date_signal(body) else None,
            batch_count=count,
            confidence=0.9,
        )

    if _is_implicit_create(body):
        count = _extract_count(body)
        inferred_name = _extract_create_name(body)
        if inferred_name:
            return ParsedTaskIntent(
                action=TaskActionType.CREATE,
                raw_text=text,
                task_name=inferred_name,
                task_date=_parse_date(body) if _contains_date_signal(body) else None,
                batch_count=count,
                confidence=0.65,
            )

    if _contains_date_signal(body) and not _has_explicit_non_create_action(body):
        inferred_name = _extract_create_name(body)
        if inferred_name:
            return ParsedTaskIntent(
                action=TaskActionType.CREATE,
                raw_text=text,
                task_name=inferred_name,
                task_date=_parse_date(body),
                batch_count=_extract_count(body),
                confidence=0.62,
            )

    if body.lower().startswith("help") or "帮助" in body or "怎么" in body:
        return ParsedTaskIntent(
            action=TaskActionType.HELP,
            raw_text=text,
            confidence=0.6,
        )

    return ParsedTaskIntent(
        action=TaskActionType.UNKNOWN,
        raw_text=text,
        confidence=0.1,
    )

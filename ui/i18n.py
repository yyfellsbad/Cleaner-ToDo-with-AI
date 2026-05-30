from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    # ── Settings nav ───────────────────────────────────────
    "nav.appearance": {"zh": "外观", "en": "Appearance"},
    "nav.language": {"zh": "语言", "en": "Language"},
    "nav.assistant": {"zh": "助手设置", "en": "Assistant"},

    # ── Settings: appearance ───────────────────────────────
    "settings.appearance.title": {"zh": "外观设置", "en": "Appearance"},
    "settings.appearance.mode": {"zh": "主题模式", "en": "Theme Mode"},
    "settings.appearance.light": {"zh": "浅色", "en": "Light"},
    "settings.appearance.dark": {"zh": "深色", "en": "Dark"},
    "settings.appearance.system": {"zh": "跟随系统", "en": "System"},
    "settings.appearance.seed": {"zh": "主题色", "en": "Accent Color"},
    "settings.appearance.hint": {"zh": "设置会自动保存，下次打开时恢复。", "en": "Settings are saved automatically."},

    # ── Theme seed labels ──────────────────────────────────
    "seed.blue": {"zh": "蓝色", "en": "Blue"},
    "seed.indigo": {"zh": "靛蓝", "en": "Indigo"},
    "seed.purple": {"zh": "紫色", "en": "Purple"},
    "seed.teal": {"zh": "青色", "en": "Teal"},
    "seed.orange": {"zh": "橙色", "en": "Orange"},
    "seed.pink": {"zh": "粉色", "en": "Pink"},

    # ── Settings: language ─────────────────────────────────
    "settings.language.title": {"zh": "语言设置", "en": "Language"},
    "settings.language.label": {"zh": "界面语言", "en": "Display Language"},
    "settings.language.hint": {"zh": "切换语言后需要重启应用生效。", "en": "Language changes apply immediately."},

    # ── Settings: assistant ────────────────────────────────
    "settings.assistant.title": {"zh": "助手设置", "en": "Assistant Settings"},
    "settings.assistant.api_config": {"zh": "API 配置", "en": "API Configuration"},
    "settings.assistant.api_key": {"zh": "API 密钥", "en": "API Key"},
    "settings.assistant.model": {"zh": "模型名称", "en": "Model Name"},
    "settings.assistant.chat_prompt": {"zh": "聊天人设 / 系统提示", "en": "Chat Persona / System Prompt"},
    "settings.assistant.persona": {"zh": "聊天人设", "en": "Chat Persona"},
    "settings.assistant.save_prompt": {"zh": "保存人设", "en": "Save Persona"},
    "settings.assistant.test": {"zh": "测试连接", "en": "Test Connection"},
    "settings.assistant.hint": {"zh": "API 设置会自动保存；聊天人设需手动确认。", "en": "API settings auto-save; persona requires confirmation."},
    "settings.assistant.presets": {"zh": "预设性格", "en": "Persona presets"},
    "settings.assistant.not_loaded": {"zh": "配置管理器未加载。", "en": "Config manager not loaded."},

    # ── Test connection results ────────────────────────────
    "test.no_key": {"zh": "API 密钥未配置", "en": "API key not configured"},
    "test.success": {"zh": "连接成功：{}", "en": "Connected: {}"},
    "test.empty": {"zh": "模型返回了空响应", "en": "Model returned empty response"},
    "test.fail": {"zh": "连接失败：{}", "en": "Connection failed: {}"},

    # ── Todo: chat drawer ──────────────────────────────────
    "chat.title": {"zh": "智能助手", "en": "AI Assistant"},
    "chat.input_hint": {"zh": "输入内容可聊天，也可执行任务指令", "en": "Chat or enter task commands"},
    "chat.confirm_delete": {"zh": "确认删除", "en": "Confirm Delete"},
    "chat.thinking": {"zh": "思考中", "en": "Thinking"},
    "chat.cancelled": {"zh": "已取消删除操作。", "en": "Delete cancelled."},
    "chat.no_pending": {"zh": "没有待确认的删除操作。", "en": "No pending delete operation."},
    "chat.chip_7day_plan": {"zh": "最近七天计划", "en": "7-day plan"},
    "chat.chip_what_next": {"zh": "我接下来该做什么", "en": "What should I do next"},
    "chat.chip_all_tasks": {"zh": "查看所有待办", "en": "Show all tasks"},
    "chat.chip_clear_done": {"zh": "清除已完成", "en": "Clear completed"},

    # ── Todo: new task input ───────────────────────────────
    "task.add_hint": {"zh": "添加新任务", "en": "Add new task"},
    "task.desc_hint": {"zh": "添加描述（可选）", "en": "Add description (optional)"},
    "task.close": {"zh": "关闭", "en": "Close"},

    # ── Todo: filters ──────────────────────────────────────
    "filter.all": {"zh": "全部", "en": "All"},
    "filter.active": {"zh": "未完成", "en": "Active"},
    "filter.completed": {"zh": "已完成", "en": "Completed"},
    "filter.expired": {"zh": "已过期", "en": "Expired"},

    # ── Todo: sort options ─────────────────────────────────
    "sort.urgency": {"zh": "紧迫程度", "en": "Urgency"},
    "sort.date_desc": {"zh": "日期 ↓", "en": "Date ↓"},
    "sort.date_asc": {"zh": "日期 ↑", "en": "Date ↑"},
    "sort.name_asc": {"zh": "名称 A-Z", "en": "Name A-Z"},
    "sort.name_desc": {"zh": "名称 Z-A", "en": "Name Z-A"},
    "sort.duration_desc": {"zh": "持续时间 ↓", "en": "Duration ↓"},
    "sort.duration_asc": {"zh": "持续时间 ↑", "en": "Duration ↑"},

    # ── Todo: status bar ───────────────────────────────────
    "status.items_left": {"zh": "{} 项未完成", "en": "{} items left"},
    "status.expired_count": {"zh": "，{} 项已过期", "en": ", {} expired"},

    # ── Todo: buttons ──────────────────────────────────────
    "btn.clear_completed": {"zh": "清除已完成", "en": "Clear Completed"},
    "btn.undo": {"zh": "撤销", "en": "Undo"},

    # ── Sidebar tooltips ───────────────────────────────────
    "sidebar.chat": {"zh": "智能助手", "en": "AI Assistant"},
    "sidebar.stats": {"zh": "统计", "en": "Statistics"},
    "sidebar.calendar": {"zh": "日历", "en": "Calendar"},
    "sidebar.settings": {"zh": "设置", "en": "Settings"},

    # ── Greetings ──────────────────────────────────────────
    "greet.morning": {"zh": "早上好", "en": "Good morning"},
    "greet.late_morning": {"zh": "上午好", "en": "Good morning"},
    "greet.noon_eat": {"zh": "中午好，吃饭了吗？", "en": "Good noon! Had lunch?"},
    "greet.noon_rest": {"zh": "中午好，休息一下吧", "en": "Good noon! Take a break"},
    "greet.afternoon": {"zh": "下午好", "en": "Good afternoon"},
    "greet.evening": {"zh": "晚上好", "en": "Good evening"},
    "greet.night": {"zh": "夜深了，注意休息", "en": "Late night — take care"},
    "greet.hello": {"zh": "你好", "en": "Hello"},

    # ── Holiday greetings ──────────────────────────────────
    "holiday.new_year": {"zh": "新年快乐", "en": "Happy New Year"},
    "holiday.valentine": {"zh": "情人节快乐", "en": "Happy Valentine's Day"},
    "holiday.womens_day": {"zh": "女神节快乐", "en": "Happy Women's Day"},
    "holiday.april_fool": {"zh": "愚人节快乐", "en": "Happy April Fools' Day"},
    "holiday.labor_day": {"zh": "劳动节快乐", "en": "Happy Labor Day"},
    "holiday.youth_day": {"zh": "青年节快乐", "en": "Happy Youth Day"},
    "holiday.children_day": {"zh": "儿童节快乐", "en": "Happy Children's Day"},
    "holiday.mid_autumn": {"zh": "中秋节快乐", "en": "Happy Mid-Autumn Festival"},
    "holiday.teacher_day": {"zh": "教师节快乐", "en": "Happy Teachers' Day"},
    "holiday.national_day": {"zh": "国庆节快乐", "en": "Happy National Day"},
    "holiday.christmas": {"zh": "圣诞节快乐", "en": "Merry Christmas"},
    "holiday.new_year_eve": {"zh": "跨年快乐", "en": "Happy New Year's Eve"},
    "holiday.spring_festival": {"zh": "春节快乐", "en": "Happy Spring Festival"},
    "holiday.lantern": {"zh": "元宵节快乐", "en": "Happy Lantern Festival"},
    "holiday.dragon_boat": {"zh": "端午节快乐", "en": "Happy Dragon Boat Festival"},
    "holiday.qixi": {"zh": "七夕快乐", "en": "Happy Qixi Festival"},
    "holiday.ghost": {"zh": "中元节快乐", "en": "Happy Ghost Festival"},
    "holiday.chongyang": {"zh": "重阳节快乐", "en": "Happy Chongyang Festival"},
    "holiday.weekend": {"zh": "周末愉快", "en": "Have a nice weekend"},

    # ── Welcome dialog ─────────────────────────────────────
    "welcome.no_urgent": {"zh": "当前没有紧要任务", "en": "No urgent tasks"},
    "welcome.all_done": {"zh": "全部搞定！", "en": "All done!"},
    "welcome.nice": {"zh": "干得漂亮！", "en": "Nice work!"},
    "welcome.go": {"zh": "加油", "en": "Go!"},
    "welcome.header": {"zh": "智能助手提醒您：", "en": "AI Assistant:"},
    "welcome.expired_days": {"zh": "（已过期 {} 天）", "en": " ({} days overdue)"},
    "welcome.due_today": {"zh": "（今日到期）", "en": " (due today)"},
    "welcome.expired_footer": {"zh": "{}条已过期，请及时处理", "en": "{} overdue — please handle"},
    "welcome.got_it": {"zh": "知道了", "en": "Got it"},

    # ── Date labels ────────────────────────────────────────
    "date.today": {"zh": "今天", "en": "Today"},
    "date.tomorrow": {"zh": "明天", "en": "Tomorrow"},
    "date.day_after": {"zh": "后天", "en": "Day after"},

    # ── Delete dialog ──────────────────────────────────────
    "dialog.delete_title": {"zh": "确认删除", "en": "Confirm Delete"},
    "dialog.delete_content": {"zh": "确定要删除「{}」吗？", "en": 'Delete "{}"?'},
    "dialog.cancel": {"zh": "取消", "en": "Cancel"},
    "dialog.delete": {"zh": "删除", "en": "Delete"},

    # ── Task item ──────────────────────────────────────────
    "task.edit": {"zh": "编辑", "en": "Edit"},
    "task.delete": {"zh": "删除", "en": "Delete"},
    "task.confirm": {"zh": "确认", "en": "Confirm"},
    "task.cancel": {"zh": "取消", "en": "Cancel"},
    "task.completed_tag": {"zh": "完成", "en": "Done"},
    "task.expired_tag": {"zh": "过期", "en": "Expired"},
    "task.repeat": {"zh": "重复", "en": "Repeat"},
    "task.repeat_days_unit": {"zh": "天", "en": "days"},
    "task.repeat_mode_label": {"zh": "模式", "en": "Mode"},

    # ── Date picker ────────────────────────────────────────
    "picker.weekdays": {"zh": "一二三四五六日", "en": "MTWTFSS"},
    "picker.months": {
        "zh": "1月,2月,3月,4月,5月,6月,7月,8月,9月,10月,11月,12月",
        "en": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
    },
    "picker.input_hint": {"zh": "YYYY-MM-DD / 今天 / 明天 / 527", "en": "YYYY-MM-DD / today / tomorrow / 527"},
    "picker.range_hint": {"zh": "点击选择日期，再点另一个变为持续", "en": "Click a date, then another for a range"},
    "picker.prev_month": {"zh": "上个月", "en": "Previous month"},
    "picker.next_month": {"zh": "下个月", "en": "Next month"},
    "picker.start": {"zh": "开始", "en": "Start"},
    "picker.end": {"zh": "结束", "en": "End"},
    "picker.time": {"zh": "时间", "en": "Time"},
    "picker.or": {"zh": "或", "en": "or"},
    "picker.confirm": {"zh": "确认", "en": "Confirm"},
    "picker.err_hhmm": {"zh": "格式：HH:MM", "en": "Format: HH:MM"},
    "picker.err_range": {"zh": "格式：开始日期 ~ 结束日期", "en": "Format: start ~ end"},
    "picker.err_invalid": {"zh": "日期格式无效", "en": "Invalid date format"},
    "picker.month_label": {"zh": "{}年 {}", "en": "{} {}"},

    # ── Stats ──────────────────────────────────────────────
    "stats.title": {"zh": "数据统计", "en": "Statistics"},
    "stats.refresh": {"zh": "刷新", "en": "Refresh"},
    "stats.today_tasks": {"zh": "今日待办", "en": "Today's Tasks"},
    "stats.total": {"zh": "总任务", "en": "Total"},
    "stats.completed": {"zh": "已完成", "en": "Completed"},
    "stats.rate": {"zh": "完成率", "en": "Rate"},
    "stats.expired": {"zh": "已过期", "en": "Expired"},
    "stats.in_progress": {"zh": "进行中", "en": "In Progress"},
    "stats.not_started": {"zh": "未开始", "en": "Not Started"},
    "stats.sum": {"zh": "总计", "en": "Total"},
    "stats.no_today": {"zh": "今日无待办", "en": "No tasks today"},
    "stats.today_tag": {"zh": "今日", "en": "Today"},
    "stats.pending_tag": {"zh": "待办", "en": "Pending"},
    "stats.trend_added": {"zh": "新增", "en": "Added"},
    "stats.trend_completed": {"zh": "完成", "en": "Completed"},
    "stats.trend_expired": {"zh": "过期", "en": "Expired"},
    "stats.trend_title": {"zh": "近 7 天趋势", "en": "7-Day Trend"},

    # ── Calendar view ───────────────────────────────────────
    "calendar.title": {"zh": "日历", "en": "Calendar"},
    "calendar.today": {"zh": "今天", "en": "Today"},
    "calendar.no_tasks": {"zh": "当日无待办", "en": "No tasks this day"},
    "calendar.task_count": {"zh": "{} 个待办", "en": "{} tasks"},

    # ── Repeat / recurring tasks ────────────────────────────
    "repeat.not_repeat": {"zh": "不重复", "en": "No repeat"},
    "repeat.every_day": {"zh": "每天", "en": "Daily"},
    "repeat.every_2_days": {"zh": "隔天", "en": "Every 2 days"},
    "repeat.every_3_days": {"zh": "每3天", "en": "Every 3 days"},
    "repeat.every_7_days": {"zh": "每7天", "en": "Every 7 days"},
    "repeat.custom": {"zh": "自定义", "en": "Custom"},
    "repeat.every_n_days": {"zh": "每{}天", "en": "Every {} days"},
    "repeat.once_mode": {"zh": "只需一次", "en": "Just once"},
    "repeat.each_mode": {"zh": "每次都要", "en": "Every time"},
    "repeat.once_desc": {"zh": "整个周期只需完成一次", "en": "Complete once in the period"},
    "repeat.each_desc": {"zh": "每个实例独立完成", "en": "Complete each occurrence"},
    "repeat.progress": {"zh": "{}/{} 已打卡", "en": "{}/{} done"},

    # ── LLM service messages ───────────────────────────────
    "llm.unknown_intent": {
        "zh": "我暂时没有识别出具体任务操作。你可以试试：帮我添加一个待办、帮我把开会改成周五、删除待办xxx。",
        "en": "I didn't catch that. Try: add a task, change meeting to Friday, delete task xxx.",
    },
    "llm.help": {
        "zh": "我可以帮你新增、查看、修改、完成、取消完成和删除任务，还可以帮你规划接下来该做什么。删除前会先确认。",
        "en": "I can add, list, update, complete, uncomplete, and delete tasks, plus plan next steps. Deletes require confirmation.",
    },
    "llm.missing_name": {
        "zh": "我识别到的是新增任务，但还缺少任务内容。比如：帮我添加一个待办：明天开会。",
        "en": "I detected a create action but missing task name. Example: add a task: meeting tomorrow.",
    },
    "llm.created": {"zh": "已添加待办：{}", "en": "Task added: {}"},
    "llm.batch_created": {"zh": "已批量添加 {} 条待办。", "en": "Batch added {} tasks."},
    "llm.update_no_match": {"zh": "没有找到匹配的任务。你可以补充更准确的名字。", "en": "No matching task found. Try a more specific name."},
    "llm.updated": {"zh": "已更新任务：{}", "en": "Task updated: {}"},
    "llm.complete_no_match": {"zh": "没有找到需要更新完成状态的任务。", "en": "No matching task to update status."},
    "llm.status_done": {"zh": "完成", "en": "completed"},
    "llm.status_undone": {"zh": "未完成", "en": "uncompleted"},
    "llm.marked_single": {"zh": "已标记为{}：{}", "en": "Marked as {}: {}"},
    "llm.marked_batch": {"zh": "已将 {} 条任务标记为{}。", "en": "Marked {} tasks as {}."},
    "llm.delete_no_match": {"zh": "没有找到要删除的任务。", "en": "No matching task to delete."},
    "llm.confirm_all": {"zh": "请确认删除全部任务（共 {} 条）。", "en": "Confirm delete all tasks ({} total)?"},
    "llm.confirm_filtered": {"zh": "请确认删除当前筛选中的任务（共 {} 条）。", "en": "Confirm delete filtered tasks ({} total)?"},
    "llm.confirm_one": {"zh": "请确认删除：{}", "en": "Confirm delete: {}"},
    "llm.token_expired": {"zh": "确认令牌已失效，请重新发起删除请求。", "en": "Confirmation token expired. Please re-issue the delete."},
    "llm.task_count": {"zh": "{} 条任务", "en": "{} tasks"},
    "llm.deleted": {"zh": "已删除任务：{}", "en": "Task deleted: {}"},
    "llm.unsupported": {"zh": "我已收到指令，但还无法执行这类操作。", "en": "Command received but not supported."},
    "llm.confirm_not_found": {"zh": "没有找到待确认的删除操作。", "en": "No pending delete operation found."},
    "llm.deleted_batch": {"zh": "已删除 {} 条任务。", "en": "Deleted {} tasks."},
    "llm.memory_intro": {"zh": "以下是最近的对话记录，供你参考：", "en": "Recent conversation for reference:"},
    "llm.memory_user": {"zh": "用户：{}", "en": "User: {}"},
    "llm.memory_assistant": {"zh": "助手：{}", "en": "Assistant: {}"},
    "llm.chat_unavailable": {
        "zh": "聊天模型当前不可用。请先配置 OPENAI_API_KEY，或稍后再试。",
        "en": "Chat model unavailable. Configure API key or try later.",
    },
    "llm.empty_reply": {"zh": "我暂时没有生成回复。", "en": "No response generated."},
    "llm.chat_error": {"zh": "聊天服务暂时不可用，请稍后再试。", "en": "Chat service unavailable. Try later."},
    "llm.plan_empty": {
        "zh": "当前没有未完成的任务，你可以先添加一些待办。",
        "en": "No active tasks. Add some tasks first.",
    },
    "llm.plan_overdue": {"zh": "已过期 {} 天", "en": "{} days overdue"},
    "llm.plan_today": {"zh": "今天到期", "en": "Due today"},
    "llm.plan_tomorrow": {"zh": "明天到期", "en": "Due tomorrow"},
    "llm.plan_soon": {"zh": "{} 天后到期", "en": "Due in {} days"},
    "llm.plan_duration": {"zh": "[持续 {} 天]", "en": "[{} days]"},
    "llm.plan_advice_header": {"zh": "任务规划建议：", "en": "Planning advice:"},
    "llm.plan_overdue_section": {"zh": "以下任务已过期，建议优先处理：", "en": "Overdue tasks — handle first:"},
    "llm.plan_today_section": {"zh": "以下任务今天到期：", "en": "Due today:"},
    "llm.plan_soon_section": {"zh": "近期任务（3天内）：", "en": "Upcoming (within 3 days):"},
    "llm.plan_no_urgent": {"zh": "没有紧急任务，可以按计划推进。", "en": "No urgent tasks. Proceed as planned."},
    "llm.plan_failed": {"zh": "无法生成规划建议。", "en": "Unable to generate plan."},
    "llm.list_empty": {"zh": "当前没有待办任务。", "en": "No tasks."},
    "llm.list_header": {"zh": "当前任务列表：", "en": "Current tasks:"},
    "llm.list_status_done": {"zh": "完成", "en": "done"},
    "llm.list_status_undone": {"zh": "未完成", "en": "active"},
    "llm.ambiguous": {"zh": "我找到了多个可能匹配的任务，请再明确一点：", "en": "Multiple matches found. Be more specific:"},
}


def t(key: str, *args) -> str:
    from ui.theme import ThemeManager

    lang = ThemeManager.instance().language
    entry = MESSAGES.get(key)
    if not entry:
        return key
    text = entry.get(lang, entry.get("zh", key))
    if args:
        return text.format(*args)
    return text

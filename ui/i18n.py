from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    # ── Settings nav ───────────────────────────────────────
    "nav.appearance": {"zh": "外观", "en": "Appearance"},
    "nav.language": {"zh": "语言", "en": "Language"},
    "nav.assistant": {"zh": "助手设置", "en": "Assistant"},
    "nav.notifications": {"zh": "通知", "en": "Notifications"},
    "nav.tutorial": {"zh": "教程", "en": "Tutorial"},
    "nav.settings": {"zh": "设置", "en": "Settings"},

    # ── Settings: title ────────────────────────────────────
    "settings.title": {"zh": "设置", "en": "Settings"},

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
    "task.remind_time": {"zh": "定时提醒", "en": "Scheduled Reminder"},
    "task.remind_time_label": {"zh": "提醒时间", "en": "Remind at"},

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

    # ── Heatmap ─────────────────────────────────────────────
    "stats.heatmap_title": {"zh": "任务活动", "en": "Activity"},
    "stats.heatmap_weekdays": {"zh": "一,二,三,四,五,六,日", "en": "Mon,Tue,Wed,Thu,Fri,Sat,Sun"},
    "stats.heatmap_month": {"zh": "{}月", "en": "{}"},
    "stats.assess_title": {"zh": "{} 完成度评估", "en": "{} Completion"},
    "stats.assess_hint": {"zh": "选择当天的完成情况：", "en": "Select completion level:"},
    "stats.assess_0": {"zh": "未完成", "en": "None"},
    "stats.assess_1": {"zh": "25%", "en": "25%"},
    "stats.assess_2": {"zh": "50%", "en": "50%"},
    "stats.assess_3": {"zh": "75%", "en": "75%"},
    "stats.assess_4": {"zh": "全部完成", "en": "100%"},
    "stats.assess_today_title": {"zh": "今日完成度", "en": "Today's Completion"},
    "stats.assess_today_hint": {"zh": "点击评估今天的完成情况：", "en": "Tap to assess today:"},
    "stats.assess_today_done": {"zh": "已评估 ✓", "en": "Assessed ✓"},

    # ── Calendar view ───────────────────────────────────────
    "calendar.title": {"zh": "日历", "en": "Calendar"},
    "calendar.today": {"zh": "今天", "en": "Today"},
    "calendar.no_tasks": {"zh": "当日无待办", "en": "No tasks this day"},
    "calendar.task_count": {"zh": "{} 个待办", "en": "{} tasks"},

    # ── Settings: notifications ─────────────────────────────
    "settings.notifications.title": {"zh": "通知设置", "en": "Notification Settings"},
    "settings.notifications.enabled": {"zh": "启用通知", "en": "Enable Notifications"},
    "settings.notifications.advance": {"zh": "提前提醒时间", "en": "Advance Reminder"},
    "settings.notifications.advance_hint": {"zh": "任务到期前多久发送提醒", "en": "How long before deadline to remind"},
    "settings.notifications.dnd": {"zh": "免打扰", "en": "Do Not Disturb"},
    "settings.notifications.dnd_enabled": {"zh": "启用免打扰时段", "en": "Enable DND Period"},
    "settings.notifications.dnd_start": {"zh": "开始时间", "en": "Start Time"},
    "settings.notifications.dnd_end": {"zh": "结束时间", "en": "End Time"},
    "settings.notifications.test": {"zh": "发送测试通知", "en": "Send Test Notification"},
    "settings.notifications.test_ok": {"zh": "测试通知已发送", "en": "Test notification sent"},
    "settings.notifications.hint": {"zh": "通知将在任务到期、需要打卡时弹出系统通知。", "en": "System notifications for task deadlines and check-ins."},

    # ── Notification bodies ─────────────────────────────────
    "notif.checkin": {"zh": "打卡提醒", "en": "Check-in"},
    "notif.ongoing": {"zh": "进行中", "en": "Ongoing"},
    "notif.expiring": {"zh": "即将过期", "en": "Expiring Soon"},
    "notif.expired": {"zh": "已过期", "en": "Expired"},
    "notif.body.checkin": {"zh": "今天需要打卡：{}", "en": "Check in today: {}"},
    "notif.body.ongoing": {"zh": "任务进行中：{}", "en": "Ongoing: {}"},
    "notif.body.expiring": {"zh": "即将到期：{}", "en": "Expiring soon: {}"},
    "notif.body.expired": {"zh": "已过期：{}", "en": "Expired: {}"},
    "notif.scheduled": {"zh": "定时提醒", "en": "Reminder"},
    "notif.body.scheduled": {"zh": "提醒您：{}", "en": "Reminder: {}"},

    # ── Toast notifications ─────────────────────────────────
    "toast.task_added": {"zh": "已添加任务：{}", "en": "Task added: {}"},
    "toast.task_deleted": {"zh": "已删除任务：{}", "en": "Task deleted: {}"},
    "toast.tasks_cleared": {"zh": "已清除 {} 个已完成任务", "en": "Cleared {} completed tasks"},

    # ── Empty state ─────────────────────────────────────────
    "empty.no_tasks": {"zh": "暂无待办任务", "en": "No tasks yet"},
    "empty.add_hint": {"zh": "在上方输入框添加新任务", "en": "Add a new task using the input above"},

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

    # ── Onboarding ─────────────────────────────────────────
    "onboarding.title": {"zh": "欢迎使用 Cleaner", "en": "Welcome to Cleaner"},
    "onboarding.step_welcome": {"zh": "欢迎", "en": "Welcome"},
    "onboarding.step_features": {"zh": "功能概览", "en": "Features"},
    "onboarding.step_api": {"zh": "AI 设置", "en": "AI Setup"},
    "onboarding.step_done": {"zh": "完成", "en": "Done"},
    "onboarding.welcome_title": {"zh": "欢迎使用 Cleaner", "en": "Welcome to Cleaner"},
    "onboarding.welcome_desc": {"zh": "一个简洁优雅的待办管理工具，支持 AI 智能助手，让你的生活更有条理。", "en": "A clean and elegant to-do app with AI assistant to keep you organized."},
    "onboarding.feature_ai_title": {"zh": "AI 智能助手", "en": "AI Assistant"},
    "onboarding.feature_ai_desc": {"zh": "用自然语言管理任务，说一句话就能添加、修改、查询任务", "en": "Manage tasks with natural language. Add, update, or query tasks by speaking."},
    "onboarding.feature_calendar_title": {"zh": "日历视图", "en": "Calendar View"},
    "onboarding.feature_calendar_desc": {"zh": "月历展示任务分布，一目了然掌握日程", "en": "Monthly calendar showing task distribution at a glance."},
    "onboarding.feature_stats_title": {"zh": "数据统计", "en": "Statistics"},
    "onboarding.feature_stats_desc": {"zh": "追踪任务完成情况，热力图展示活动趋势", "en": "Track task completion with activity heatmaps."},
    "onboarding.feature_repeat_title": {"zh": "重复任务", "en": "Recurring Tasks"},
    "onboarding.feature_repeat_desc": {"zh": "支持每日、隔天、自定义重复，适配各种场景", "en": "Daily, every-N-days, or custom repeat for any scenario."},
    "onboarding.api_title": {"zh": "配置 AI 助手", "en": "Configure AI Assistant"},
    "onboarding.api_desc": {"zh": "输入 DeepSeek API 密钥解锁 AI 功能（可选）", "en": "Enter DeepSeek API key to enable AI features (optional)"},
    "onboarding.api_key_label": {"zh": "API 密钥", "en": "API Key"},
    "onboarding.api_key_hint": {"zh": "sk-xxxxxxxx", "en": "sk-xxxxxxxx"},
    "onboarding.api_skip": {"zh": "暂时跳过", "en": "Skip for now"},
    "onboarding.api_skip_hint": {"zh": "（可暂时跳过）", "en": "(Can skip for now)"},
    "onboarding.api_test": {"zh": "测试连接", "en": "Test Connection"},
    "onboarding.api_save": {"zh": "保存", "en": "Save"},
    "onboarding.save_success": {"zh": "保存成功", "en": "Saved successfully"},
    "onboarding.save_empty": {"zh": "请输入 API 密钥", "en": "Please enter API key"},
    "onboarding.done_title": {"zh": "准备就绪！", "en": "You're All Set!"},
    "onboarding.done_desc": {"zh": "开始使用 Cleaner 管理你的待办事项吧。", "en": "Start using Cleaner to manage your tasks."},
    "onboarding.done_hint": {"zh": "随时可以通过侧边栏的设置图标调整偏好。", "en": "You can adjust preferences anytime via the settings icon."},
    "onboarding.btn_next": {"zh": "下一步", "en": "Next"},
    "onboarding.btn_prev": {"zh": "上一步", "en": "Back"},
    "onboarding.btn_start": {"zh": "开始使用", "en": "Get Started"},
    "onboarding.btn_save": {"zh": "保存并继续", "en": "Save & Continue"},
    "onboarding.dots_hint": {"zh": "第 {} 步，共 {} 步", "en": "Step {} of {}"},
    "onboarding.btn_skip": {"zh": "跳过教程", "en": "Skip Tutorial"},
    # ── AI 教程 ──
    "onboarding.ai_tutorial": {"zh": "AI 助手使用指南", "en": "AI Assistant Guide"},
    "onboarding.ai_intro": {"zh": "用自然语言和 AI 对话，一句话就能管理任务。打开左侧聊天面板试试：", "en": "Chat with AI in natural language to manage tasks. Open the left chat panel and try:"},
    "onboarding.ai_ex_add": {"zh": "明天下午三点开会", "en": "Meeting tomorrow at 3pm"},
    "onboarding.ai_ex_add_resp": {"zh": "好的，已创建任务「开会」，时间为明天 15:00", "en": "Done! Created task 'Meeting' for tomorrow 3:00 PM"},
    "onboarding.ai_ex_query": {"zh": "这周有什么任务？", "en": "What tasks this week?"},
    "onboarding.ai_ex_query_resp": {"zh": "本周你有 3 个任务...", "en": "You have 3 tasks this week..."},
    "onboarding.ai_ex_plan": {"zh": "我接下来该做什么？", "en": "What should I do next?"},
    "onboarding.ai_ex_plan_resp": {"zh": "建议优先处理「报告」，明天就到期了", "en": "I suggest working on 'Report' — it's due tomorrow"},
    "onboarding.ai_tip": {"zh": "提示：也可以手动添加和编辑任务", "en": "Tip: You can also add and edit tasks manually"},
    # ── 任务管理教程 ──
    "onboarding.tasks_tutorial": {"zh": "任务管理", "en": "Task Management"},
    "onboarding.tasks_add": {"zh": "添加任务", "en": "Add Tasks"},
    "onboarding.tasks_add_desc": {"zh": "在顶部输入框输入任务名称，点击日历图标设置日期和时间", "en": "Type a task name in the top input, click the calendar icon to set date & time"},
    "onboarding.tasks_edit": {"zh": "编辑任务", "en": "Edit Tasks"},
    "onboarding.tasks_edit_desc": {"zh": "点击卡片上的编辑按钮修改名称、描述、日期和重复设置", "en": "Click the edit button on a card to modify name, description, date & repeat"},
    "onboarding.tasks_complete": {"zh": "完成任务", "en": "Complete Tasks"},
    "onboarding.tasks_complete_desc": {"zh": "勾选左侧复选框标记完成，重复任务支持逐日打卡", "en": "Check the left checkbox to mark done — recurring tasks support daily check-in"},
    "onboarding.tasks_drag": {"zh": "拖拽排序", "en": "Drag & Sort"},
    "onboarding.tasks_drag_desc": {"zh": "长按任务卡片拖动调整顺序，也可用排序按钮自动排列", "en": "Long-press a card to drag, or use the sort button to auto-arrange"},
    "onboarding.tasks_filter": {"zh": "筛选与排序", "en": "Filter & Sort"},
    "onboarding.tasks_filter_desc": {"zh": "按全部/未完成/已完成/已过期筛选，支持按日期、名称、紧迫度排序", "en": "Filter by all/active/completed/expired; sort by date, name, or urgency"},
    "onboarding.tasks_shortcuts": {"zh": "快捷键", "en": "Keyboard Shortcuts"},
    "onboarding.tasks_shortcuts_desc": {"zh": "Ctrl+Z 撤销 · Ctrl+N 新建任务 · Esc 关闭面板", "en": "Ctrl+Z undo · Ctrl+N new task · Esc close panel"},
    # ── 视图教程 ──
    "onboarding.views_tutorial": {"zh": "多视图与通知", "en": "Views & Notifications"},
    "onboarding.views_calendar": {"zh": "日历视图", "en": "Calendar View"},
    "onboarding.views_calendar_desc": {"zh": "点击侧边栏日历图标，月网格展示任务分布，点击日期查看详情", "en": "Click the calendar icon — month grid shows task dots, click a day for details"},
    "onboarding.views_stats": {"zh": "数据统计", "en": "Statistics"},
    "onboarding.views_stats_desc": {"zh": "点击侧边栏图表图标，查看任务分布、7 天趋势、GitHub 风格热力图", "en": "Click the chart icon — see task distribution, 7-day trends, and GitHub-style heatmap"},
    "onboarding.views_notif": {"zh": "系统通知", "en": "Notifications"},
    "onboarding.views_notif_desc": {"zh": "任务到期、重复打卡时弹出系统通知，可在设置中配置免打扰时段", "en": "System toast for deadlines & check-ins; configure DND in Settings"},
    "onboarding.views_recurring": {"zh": "重复任务", "en": "Recurring Tasks"},
    "onboarding.views_recurring_desc": {"zh": "设置每天/隔天/自定义间隔重复，支持「每期独立完成」和「一次即完成」两种模式", "en": "Set daily/custom interval repeats with 'each occurrence' or 'once' modes"},
    # ── 设置教程入口 ──
    "settings.tutorial.title": {"zh": "使用教程", "en": "Usage Tutorial"},
    "settings.tutorial.desc": {"zh": "重新查看功能介绍和使用指南", "en": "Review feature introduction and usage guide"},
    "settings.tutorial.btn": {"zh": "查看教程", "en": "View Tutorial"},
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

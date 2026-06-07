from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta

from core.models.task import TaskRecord
from services.notification_service import NotificationService
from storage.task_repo import TaskRepository


class NotificationScheduler:
    """后台调度器：每 60 秒检查任务，触发系统通知。"""

    @staticmethod
    def start(
        notif_svc: NotificationService,
        task_repo: TaskRepository,
    ) -> None:
        """启动后台通知检查循环（幂等，重复调用安全）。"""
        if hasattr(NotificationScheduler, "_task") and not NotificationScheduler._task.done():
            return

        async def _loop() -> None:
            while True:
                try:
                    NotificationScheduler._check(notif_svc, task_repo)
                except Exception:
                    pass
                await asyncio.sleep(60)

        NotificationScheduler._task = asyncio.ensure_future(_loop())

    @staticmethod
    def stop() -> None:
        """停止后台通知检查循环。"""
        if hasattr(NotificationScheduler, "_task") and not NotificationScheduler._task.done():
            try:
                NotificationScheduler._task.cancel()
            except Exception:
                pass  # 忽略取消时的异常

    @staticmethod
    def _check(
        notif_svc: NotificationService,
        task_repo: TaskRepository,
    ) -> None:
        if not notif_svc.enabled:
            return

        today = date.today()
        now = datetime.now()
        advance = timedelta(minutes=notif_svc.advance_min)
        tasks = task_repo.list_tasks()

        for task in tasks:
            if task.completed:
                continue
            NotificationScheduler._check_task(notif_svc, task, today, now, advance)

    @staticmethod
    def _check_task(
        notif_svc: NotificationService,
        task: TaskRecord,
        today: date,
        now: datetime,
        advance: timedelta,
    ) -> None:
        from ui.i18n import t

        tid = task.id

        # ── 重复任务（each 模式）：今日需打卡 ──
        if task.is_recurring and task.repeat_mode == "each":
            if task.repeat_days <= 0 or not task.end_date:
                return
            start_d = task.date.date()
            end_d = task.end_date.date()
            if not (start_d <= today <= end_d):
                return
            # 检查 today 是否是打卡日
            occ = start_d
            is_occurrence = False
            while occ <= end_d:
                if occ == today:
                    is_occurrence = True
                    break
                occ = date.fromordinal(occ.toordinal() + task.repeat_days)
            if not is_occurrence:
                return
            if task.occurrence_done(today):
                return
            tag = f"task_{tid}_{today.isoformat()}_checkin"
            notif_svc.send(
                t("notif.checkin"),
                t("notif.body.checkin", task.name),
                tag,
            )
            return

        # ── 重复任务（once 模式）：今日在范围内 ──
        if task.is_recurring and task.repeat_mode == "once":
            if task.end_date and task.date.date() <= today <= task.end_date.date():
                tag = f"task_{tid}_{today.isoformat()}_ongoing"
                notif_svc.send(
                    t("notif.ongoing"),
                    t("notif.body.ongoing", task.name),
                    tag,
                )
            return

        # ── 单次任务：即将过期 ──
        deadline = task.end_date or task.date
        if task.end_date:
            time_left = deadline - now
            if timedelta(0) < time_left <= advance:
                tag = f"task_{tid}_{today.isoformat()}_expiring"
                notif_svc.send(
                    t("notif.expiring"),
                    t("notif.body.expiring", task.name),
                    tag,
                )
                return

        # ── 单次任务：已过期 ──
        if deadline.date() < today:
            tag = f"task_{tid}_{today.isoformat()}_expired"
            notif_svc.send(
                t("notif.expired"),
                t("notif.body.expired", task.name),
                tag,
            )
            return

        # ── 无 end_date 的单次任务：到期提醒 ──
        if not task.end_date:
            time_left = task.date - now
            if timedelta(0) < time_left <= advance:
                tag = f"task_{tid}_{today.isoformat()}_reminder"
                notif_svc.send(
                    t("notif.expiring"),
                    t("notif.body.expiring", task.name),
                    tag,
                )

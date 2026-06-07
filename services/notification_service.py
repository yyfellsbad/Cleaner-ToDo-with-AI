from __future__ import annotations

from datetime import date, datetime, time

from storage.setting_repo import SettingRepo


class NotificationService:
    """Windows 系统通知服务（单例）。

    职责：通过 winotify 发送 toast 通知，管理免打扰时段，去重。
    """

    _instance: NotificationService | None = None

    @classmethod
    def instance(cls) -> NotificationService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._repo: SettingRepo | None = None
        self._enabled = True
        self._advance_min = 30
        self._dnd_enabled = False
        self._dnd_start = "23:00"
        self._dnd_end = "08:00"
        self._default_end_time = "23:00"
        self._sent_tags: set[str] = set()
        self._last_clear_date: date | None = None

    # ── Load / Save ──────────────────────────────────────────

    def load(self, repo: SettingRepo) -> None:
        self._repo = repo
        self._enabled = repo.get("notif.enabled", "1") == "1"
        self._advance_min = int(repo.get("notif.advance_min", "30"))
        self._dnd_enabled = repo.get("notif.dnd_enabled", "0") == "1"
        self._dnd_start = repo.get("notif.dnd_start", "23:00")
        self._dnd_end = repo.get("notif.dnd_end", "08:00")
        # 默认到期时间，默认使用免打扰开始时间
        self._default_end_time = repo.get("notif.default_end_time", self._dnd_start)

    def _save(self, key: str, value: str) -> None:
        if self._repo:
            self._repo.set(key, value)

    # ── Properties ───────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, v: bool) -> None:
        self._enabled = v
        self._save("notif.enabled", "1" if v else "0")

    @property
    def advance_min(self) -> int:
        return self._advance_min

    @advance_min.setter
    def advance_min(self, v: int) -> None:
        self._advance_min = v
        self._save("notif.advance_min", str(v))

    @property
    def dnd_enabled(self) -> bool:
        return self._dnd_enabled

    @dnd_enabled.setter
    def dnd_enabled(self, v: bool) -> None:
        self._dnd_enabled = v
        self._save("notif.dnd_enabled", "1" if v else "0")

    @property
    def dnd_start(self) -> str:
        return self._dnd_start

    @dnd_start.setter
    def dnd_start(self, v: str) -> None:
        self._dnd_start = v
        self._save("notif.dnd_start", v)

    @property
    def dnd_end(self) -> str:
        return self._dnd_end

    @dnd_end.setter
    def dnd_end(self, v: str) -> None:
        self._dnd_end = v
        self._save("notif.dnd_end", v)

    @property
    def default_end_time(self) -> str:
        return self._default_end_time

    @default_end_time.setter
    def default_end_time(self, v: str) -> None:
        self._default_end_time = v
        self._save("notif.default_end_time", v)

    # ── DND check ────────────────────────────────────────────

    @staticmethod
    def _parse_hm(hm: str) -> time:
        parts = hm.split(":")
        return time(int(parts[0]), int(parts[1]))

    def _is_dnd(self) -> bool:
        if not self._dnd_enabled:
            return False
        now = datetime.now().time()
        start = self._parse_hm(self._dnd_start)
        end = self._parse_hm(self._dnd_end)
        if start <= end:
            return start <= now < end
        # 跨午夜：23:00–08:00 → now >= 23:00 OR now < 08:00
        return now >= start or now < end

    # ── Dedup ────────────────────────────────────────────────

    def _clear_stale_tags(self) -> None:
        today = date.today()
        if self._last_clear_date != today:
            self._sent_tags.clear()
            self._last_clear_date = today

    # ── Send ─────────────────────────────────────────────────

    def send(self, title: str, body: str, tag: str) -> bool:
        """发送系统通知。返回是否实际发送。"""
        if not self._enabled:
            return False
        if self._is_dnd():
            return False
        self._clear_stale_tags()
        if tag in self._sent_tags:
            return False
        self._sent_tags.add(tag)
        return self._do_send(title, body)

    def send_test(self) -> bool:
        """开发者测试：发送测试通知，忽略 DND 和去重。"""
        return self._do_send("Cleaner · 测试通知", "通知系统工作正常 ✓")

    @staticmethod
    def _do_send(title: str, body: str) -> bool:
        try:
            from winotify import Notification, audio

            toast = Notification(
                app_id="Cleaner",
                title=title,
                msg=body,
                duration="short",
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
            return True
        except Exception:
            return False

import os
import io
import html
import json
import sqlite3
import threading
import time as _time
import builtins as _builtins
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

# File gốc của user: đặt cùng thư mục với file bot này trên Render.
CORE_FILE = os.getenv("VBTOOL_CORE_FILE", "vbtoolvip2k999_final213.py")

# Import file tool. Nó có cài dependency lúc import và KHÔNG gọi main() khi import.
import importlib.util
spec = importlib.util.spec_from_file_location("vbtool_core", CORE_FILE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Không thể load file tool: {CORE_FILE}")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
KEY_SERVER_URL = os.getenv("KEY_SERVER_URL", getattr(core, "KEY_SERVER_URL", "")).strip().rstrip("/")
TELEGRAPH_ACCESS_TOKEN = os.getenv("TELEGRAPH_ACCESS_TOKEN", getattr(core, "ACCESS_TOKEN", "")).strip()
LINK4M_TOKEN = os.getenv("LINK4M_TOKEN", getattr(core, "LINK4M_TOKEN", "")).strip()
VUOTNHANH_TOKEN = os.getenv("VUOTNHANH_TOKEN", getattr(core, "VUOTNHANH_TOKEN", "")).strip()
LINK4M_API = os.getenv("LINK4M_API", getattr(core, "LINK4M_API", "https://link4m.co/api-shorten/v2"))
VUOTNHANH_API = os.getenv("VUOTNHANH_API", getattr(core, "VUOTNHANH_API", "https://vuotnhanh.com/api"))
DB_FILE = os.getenv("VBTOOL_DB_FILE", "vbtool_telegram.db")

if not BOT_TOKEN:
    raise RuntimeError("Thiếu BOT_TOKEN trong Environment Variables của Render.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)

# -----------------------------------------------------------------------------
# SQLite: key/account/config theo Telegram user
# -----------------------------------------------------------------------------
DB_LOCK = threading.RLock()

def db():
    con = sqlite3.connect(DB_FILE, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

with db() as con:
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            key TEXT,
            key_type TEXT,
            activated_at TEXT,
            expires_at TEXT,
            is_forever INTEGER DEFAULT 0,
            account_link TEXT,
            hilo_payload TEXT,
            updated_at TEXT
        )
    """)
    con.commit()


def now_utc():
    return datetime.now(timezone.utc)


def get_user(tg_id):
    with DB_LOCK, db() as con:
        row = con.execute("SELECT * FROM users WHERE telegram_id=?", (int(tg_id),)).fetchone()
        return dict(row) if row else None


def put_user(tg_id, **fields):
    existing = get_user(tg_id) or {"telegram_id": int(tg_id)}
    existing.update(fields)
    existing["telegram_id"] = int(tg_id)
    existing["updated_at"] = now_utc().isoformat()
    cols = [k for k in existing.keys() if k != "telegram_id"]
    vals = [existing[k] for k in cols]
    with DB_LOCK, db() as con:
        exists = con.execute("SELECT 1 FROM users WHERE telegram_id=?", (int(tg_id),)).fetchone()
        if exists:
            sets = ",".join(f"{c}=?" for c in cols)
            con.execute(f"UPDATE users SET {sets} WHERE telegram_id=?", vals + [int(tg_id)])
        else:
            csql = ",".join(["telegram_id"] + cols)
            q = ",".join(["?"] * (1 + len(cols)))
            con.execute(f"INSERT INTO users ({csql}) VALUES ({q})", [int(tg_id)] + vals)
        con.commit()


def tg_device_id(tg_id):
    # Không dùng device_id của Android nữa; mỗi Telegram tài khoản có một ID ổn định.
    return f"telegram:{int(tg_id)}"


def parse_expiry(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def activation_for(tg_id):
    row = get_user(tg_id)
    if not row or not row.get("key") or not row.get("key_type"):
        return None
    exp = parse_expiry(row.get("expires_at"))
    if row.get("is_forever"):
        exp = None
    return {
        "telegram_id": int(tg_id),
        "device_id": tg_device_id(tg_id),
        "key": row.get("key"),
        "key_type": str(row.get("key_type") or "FREE").upper(),
        "is_vip": str(row.get("key_type") or "FREE").upper() == "VIP",
        "activation_time": row.get("activated_at"),
        "expiry_time": row.get("expires_at"),
        "expires_at": row.get("expires_at"),
        "is_forever": bool(row.get("is_forever")),
    }


def activation_valid(tg_id, refresh_vip=True):
    act = activation_for(tg_id)
    if not act:
        return False, "Chưa kích hoạt", False

    if act["is_forever"]:
        return True, "Vĩnh viễn", True

    exp = parse_expiry(act["expiry_time"])
    if exp is None:
        return False, "Ngày hết hạn không hợp lệ", act["is_vip"]

    if now_utc() >= exp:
        put_user(tg_id, key=None, key_type=None, activated_at=None, expires_at=None, is_forever=0)
        return False, "KEY ĐÃ HẾT HẠN", False

    # VIP: xác nhận server khi vào tool. Lỗi mạng tạm thời không tự xóa key.
    if refresh_vip and act["is_vip"] and act["key"] and KEY_SERVER_URL:
        try:
            import requests
            r = requests.post(
                f"{KEY_SERVER_URL}/api/verify_key",
                json={"device_id": tg_device_id(tg_id), "key": act["key"]},
                timeout=15,
            )
            if r.ok:
                data = r.json() if r.content else {}
                status = str(data.get("status", "")).upper()
                if not data.get("success"):
                    if status in {"REVOKED", "EXPIRED", "DEVICE_MISMATCH"}:
                        put_user(tg_id, key=None, key_type=None, activated_at=None, expires_at=None, is_forever=0)
                        return False, status, False
        except Exception:
            pass

    remain = exp - now_utc()
    hours = remain.total_seconds() / 3600
    return True, f"Còn {hours:.1f} giờ", act["is_vip"]


def verify_vip_remote(tg_id, key):
    import requests
    if not KEY_SERVER_URL:
        return None, "Chưa cấu hình KEY_SERVER_URL"
    try:
        r = requests.post(
            f"{KEY_SERVER_URL}/api/verify_key",
            json={"device_id": tg_device_id(tg_id), "key": str(key).strip()},
            timeout=15,
        )
        data = r.json() if r.content else {}
    except Exception as exc:
        return None, f"Lỗi kết nối server key: {exc}"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    return data, None


def create_free_link(tg_id):
    """Tái tạo flow Free của tool nhưng lưu trạng thái theo Telegram user."""
    if not (TELEGRAPH_ACCESS_TOKEN and LINK4M_TOKEN and VUOTNHANH_TOKEN):
        return None, "Thiếu TELEGRAPH_ACCESS_TOKEN/LINK4M_TOKEN/VUOTNHANH_TOKEN trên Render."
    import json as _json
    import secrets
    import requests

    key = secrets.token_hex(4)
    device_id = tg_device_id(tg_id)
    content = _json.dumps([
        {"tag": "p", "children": ["🔑 VBTOOL KEY"]},
        {"tag": "p", "children": [f"📱 Device ID: {device_id}"]},
        {"tag": "p", "children": [f"🔑 Key: {key}"]},
        {"tag": "p", "children": ["⚠️ Key chỉ dùng cho tài khoản Telegram này."]},
    ])
    try:
        r = requests.post(
            "https://api.telegra.ph/createPage",
            data={
                "access_token": TELEGRAPH_ACCESS_TOKEN,
                "title": "KEY 24H",
                "author_name": "VBTOOL",
                "content": content,
                "return_content": False,
            },
            timeout=15,
        )
        if r.status_code != 200 or not r.json().get("ok"):
            return None, "Không thể tạo trang Telegraph."
        telegraph_url = r.json()["result"]["url"]

        r1 = requests.get(LINK4M_API, params={"api": LINK4M_TOKEN, "url": telegraph_url}, timeout=15)
        if r1.status_code != 200:
            return None, "Lỗi Link4M."
        d1 = r1.json()
        if d1.get("status") != "success":
            return None, "API Link4M trả về lỗi."
        link4m_url = d1.get("shortenedUrl")

        r2 = requests.get(VUOTNHANH_API, params={"api": VUOTNHANH_TOKEN, "url": link4m_url}, timeout=15)
        if r2.status_code != 200:
            return None, "Lỗi Vượt Nhanh."
        d2 = r2.json()
        if d2.get("status") != "success":
            return None, "API Vượt Nhanh trả về lỗi."
        final_url = d2.get("shortenedUrl")
        if not final_url:
            return None, "Không nhận được link lấy key."

        FREE_PENDING[int(tg_id)] = key
        return final_url, None
    except Exception as exc:
        return None, str(exc)


FREE_PENDING = {}


def activate_free(tg_id, supplied_key):
    expected = FREE_PENDING.get(int(tg_id))
    if not expected:
        return False, "Bạn chưa tạo link lấy key Free hoặc link đã được dùng."
    if str(supplied_key).strip() != expected:
        FREE_PENDING.pop(int(tg_id), None)
        return False, "Key Free không khớp. Hãy tạo link mới."
    start = now_utc()
    exp = start + timedelta(hours=24)
    put_user(tg_id,
             key=str(supplied_key).strip(),
             key_type="FREE",
             activated_at=start.isoformat(),
             expires_at=exp.isoformat(),
             is_forever=0)
    FREE_PENDING.pop(int(tg_id), None)
    return True, "FREE"


# -----------------------------------------------------------------------------
# Runtime bridge: nhập/xuất terminal -> Telegram
# -----------------------------------------------------------------------------
class StopTool(Exception):
    pass

@dataclass
class JobContext:
    telegram_id: int
    tool_name: str
    answers: list = field(default_factory=list)
    answer_event: threading.Event = field(default_factory=threading.Event)
    stop_event: threading.Event = field(default_factory=threading.Event)
    waiting_prompt: str = ""
    message_id: int | None = None
    last_render: str = ""
    last_sent_at: float = 0.0
    thread: threading.Thread | None = None

JOB_LOCK = threading.RLock()
ACTIVE_JOB: JobContext | None = None
CURRENT = threading.local()
ORIG_TIME = _time
ORIG_PRINT = _builtins.print
ORIG_INPUT = _builtins.input
REAL_CONSOLE = getattr(core, "Console", None)() if getattr(core, "Console", None) else None


def ctx():
    return getattr(CURRENT, "ctx", None)


def render_text(obj):
    """Chuyển Rich renderable thành text Telegram, bỏ ANSI/markup dư thừa."""
    try:
        from rich.console import Console
        out = io.StringIO()
        c = Console(file=out, force_terminal=False, color_system=None, width=100, soft_wrap=True)
        c.print(obj)
        text = out.getvalue().replace("\x1b", "")
        return text.strip()
    except Exception:
        return str(obj).strip()


def send_text(tg_id, text, *, edit_message_id=None, force=False):
    text = str(text or "").strip()
    if not text:
        return None
    if len(text) > 3900:
        text = text[-3900:]
    try:
        if edit_message_id:
            try:
                bot.edit_message_text(text, tg_id, edit_message_id, parse_mode="HTML")
                return edit_message_id
            except Exception:
                pass
        m = bot.send_message(tg_id, text, disable_web_page_preview=True)
        return m.message_id
    except Exception:
        return None


def bot_print(*args, **kwargs):
    c = ctx()
    if c is None:
        return ORIG_PRINT(*args, **kwargs)
    text = html.escape(" ".join(render_text(x) for x in args))
    if kwargs.get("end") == "" and not text:
        return
    send_text(c.telegram_id, text)


def bot_input(prompt=""):
    c = ctx()
    if c is None:
        return ORIG_INPUT(prompt)
    prompt = render_text(prompt)
    c.waiting_prompt = prompt
    send_text(c.telegram_id, f"<b>⌨️ Nhập dữ liệu</b>\n{prompt}" if prompt else "<b>⌨️ Nhập dữ liệu</b>")
    c.answer_event.clear()
    while not c.stop_event.is_set():
        if c.answer_event.wait(0.5):
            if c.stop_event.is_set():
                raise StopTool()
            value = c.answers.pop(0) if c.answers else ""
            c.waiting_prompt = ""
            return value
    raise StopTool()


class BotPrompt:
    @staticmethod
    def ask(prompt="", default=None, *args, **kwargs):
        raw = bot_input(prompt)
        if raw == "" and default is not None:
            return default
        return raw


class BotIntPrompt(BotPrompt):
    @staticmethod
    def ask(prompt="", default=None, *args, **kwargs):
        raw = bot_input(prompt)
        if raw == "" and default is not None:
            return default
        return int(raw)


class BotFloatPrompt(BotPrompt):
    @staticmethod
    def ask(prompt="", default=None, *args, **kwargs):
        raw = bot_input(prompt)
        if raw == "" and default is not None:
            return default
        return float(raw)


class BotConsole:
    def print(self, *args, **kwargs):
        bot_print(*args, **kwargs)
    def clear(self):
        # Telegram không có clear màn hình; chỉ gửi separator khi tool đổi màn.
        return None


class TimeProxy:
    def __getattr__(self, name):
        return getattr(ORIG_TIME, name)
    def sleep(self, seconds):
        c = ctx()
        if c is None:
            return ORIG_TIME.sleep(seconds)
        end = ORIG_TIME.time() + max(0.0, float(seconds))
        while ORIG_TIME.time() < end:
            if c.stop_event.is_set():
                raise StopTool()
            ORIG_TIME.sleep(min(0.25, max(0.01, end - ORIG_TIME.time())))


class BotLive:
    def __init__(self, renderable=None, console=None, refresh_per_second=4, screen=False, *args, **kwargs):
        self.renderable = renderable
        self.interval = 1.0 / max(1, float(refresh_per_second or 1))
        self._last = 0.0
        self._message_id = None
    def __enter__(self):
        self.update(self.renderable)
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def update(self, renderable, *args, **kwargs):
        self.renderable = renderable
        c = ctx()
        if c is None:
            return
        now = ORIG_TIME.time()
        if now - self._last < self.interval and not c.stop_event.is_set():
            return
        self._last = now
        text = html.escape(render_text(renderable))
        # Telegram không cần gửi hàng trăm message: cập nhật 1 message.
        mid = self._message_id or c.message_id
        if text == c.last_render and not kwargs.get("force"):
            return
        c.last_render = text
        new_mid = send_text(c.telegram_id, text, edit_message_id=mid)
        if new_mid:
            self._message_id = new_mid
            c.message_id = new_mid


# Không sửa source gốc; thay các điểm giao tiếp terminal bằng adapter.
core.console = BotConsole()
core.Prompt = BotPrompt
core.IntPrompt = BotIntPrompt
core.FloatPrompt = BotFloatPrompt
core.Live = BotLive
core.time = TimeProxy()
core.input = bot_input
core.print = bot_print

# Các hàm thoát của bản desktop không được phép kill cả worker Render.
core.force_exit_vbtool = lambda code=0: (_ for _ in ()).throw(StopTool())

# -----------------------------------------------------------------------------
# Key bridge mà file gốc gọi trong main_vth/main_lotto/main_cdtd/xw_main/HILO.
# Chuyển tất cả sang session Telegram hiện tại.
# -----------------------------------------------------------------------------
def bot_load_activation():
    c = ctx()
    return activation_for(c.telegram_id) if c else None


def bot_get_device_id():
    c = ctx()
    return tg_device_id(c.telegram_id) if c else "render-worker"


def bot_save_activation(device_id, key, activation_time, duration_hours, key_type="FREE"):
    c = ctx()
    if c is None:
        return False
    try:
        act_time = activation_time
        if act_time.tzinfo is None:
            act_time = act_time.replace(tzinfo=timezone.utc)
        forever = str(key_type).upper() == "VIP" and float(duration_hours or 0) >= 24 * 365 * 9
        expiry = None if forever else (act_time + timedelta(hours=float(duration_hours or 24))).isoformat()
        put_user(c.telegram_id,
                 key=str(key),
                 key_type=str(key_type).upper(),
                 activated_at=act_time.isoformat(),
                 expires_at=expiry,
                 is_forever=1 if forever else 0)
        return True
    except Exception:
        return False


def bot_check_activation_valid(exit_on_expired=True):
    c = ctx()
    if c is None:
        return False, "Chưa có Telegram context", False
    ok, reason, is_vip = activation_valid(c.telegram_id, refresh_vip=True)
    if not ok and reason == "KEY ĐÃ HẾT HẠN":
        send_text(c.telegram_id, "❌ <b>KEY ĐÃ HẾT HẠN!</b>")
        if exit_on_expired:
            raise StopTool()
    return ok, reason, is_vip


def bot_is_vip():
    c = ctx()
    return bool(c and activation_for(c.telegram_id) and activation_for(c.telegram_id).get("is_vip"))


def bot_remove_local_activation(revoked=False):
    c = ctx()
    if c:
        put_user(c.telegram_id, key=None, key_type=None, activated_at=None, expires_at=None, is_forever=0)

core.load_activation = bot_load_activation
core.get_device_id = bot_get_device_id
core.save_activation = bot_save_activation
core.check_activation_valid = bot_check_activation_valid
core.is_vip_activated = bot_is_vip
core.remove_local_activation = bot_remove_local_activation
core.start_key_expiry_monitor = lambda: None

# Prevent accidental process-level exit in XWorld/main logic.
class SysProxy:
    def __getattr__(self, name):
        return getattr(__import__("sys"), name)
    def exit(self, code=0):
        raise StopTool()
core.sys = SysProxy()

# -----------------------------------------------------------------------------
# Telegram UI
# -----------------------------------------------------------------------------
def main_menu(tg_id):
    ok, reason, vip = activation_valid(tg_id, refresh_vip=False)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔑 Kích hoạt Key", callback_data="key_menu"),
        types.InlineKeyboardButton("🎮 Chọn Tool", callback_data="games"),
    )
    kb.add(
        types.InlineKeyboardButton("▶️ Chạy bot", callback_data="run_current"),
        types.InlineKeyboardButton("🛑 Dừng bot", callback_data="stop"),
    )
    kb.add(types.InlineKeyboardButton("ℹ️ Trạng thái", callback_data="status"))
    status = "❌ Chưa kích hoạt"
    if ok:
        status = f"💎 {'VIP' if vip else 'FREE'} • {reason}"
    current = CURRENT_SELECTION.get(tg_id, "Chưa chọn")
    text = (
        "<b>💠 VBTOOL TELEGRAM</b>\n\n"
        f"🔐 Key: {status}\n"
        f"🎮 Tool hiện tại: <b>{current}</b>\n\n"
        "Chọn chức năng bên dưới:"
    )
    return text, kb


CURRENT_SELECTION = {}
PENDING_SETTINGS = {}

TOOL_LABELS = {
    "1": "VUA THOÁT HIỂM",
    "2": "LOTTO",
    "3": "CHẠY ĐUA TỐC ĐỘ",
    "4": "CANH CODE XWORLD",
    "5": "HILO",
}


def games_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for k, label in TOOL_LABELS.items():
        kb.add(types.InlineKeyboardButton(f"{k}. {label}", callback_data=f"game:{k}"))
    kb.add(types.InlineKeyboardButton("⬅️ Quay lại", callback_data="home"))
    return "<b>🎮 CHỌN GAME / TOOL</b>\n\nChọn tool muốn chạy:", kb


def key_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🆓 Lấy Key FREE", callback_data="free_link"),
        types.InlineKeyboardButton("💎 Nhập Key VIP", callback_data="vip_input"),
    )
    kb.add(types.InlineKeyboardButton("⬅️ Quay lại", callback_data="home"))
    return "<b>🔑 QUẢN LÝ KEY</b>", kb


def running_job_for(tg_id):
    with JOB_LOCK:
        return ACTIVE_JOB if ACTIVE_JOB and ACTIVE_JOB.telegram_id == int(tg_id) else None


def start_job(tg_id, tool_key):
    global ACTIVE_JOB
    with JOB_LOCK:
        if ACTIVE_JOB is not None and ACTIVE_JOB.thread and ACTIVE_JOB.thread.is_alive():
            return False, "Đang có một tool khác chạy. Hãy bấm Dừng bot trước."
        job = JobContext(int(tg_id), TOOL_LABELS[tool_key])
        ACTIVE_JOB = job
        CURRENT_SELECTION[int(tg_id)] = TOOL_LABELS[tool_key]

    target = {
        "1": core.main_vth,
        "2": core.main_lotto,
        "3": core.main_cdtd,
        "4": core.xw_main,
        "5": core.hilo_main,
    }[tool_key]

    def runner():
        global ACTIVE_JOB
        CURRENT.ctx = job
        try:
            send_text(tg_id, f"▶️ <b>Bắt đầu {job.tool_name}</b>\nBot đang chờ dữ liệu cấu hình từ bạn.")
            target()
            if not job.stop_event.is_set():
                send_text(tg_id, f"✅ <b>{job.tool_name} đã dừng.</b>")
        except StopTool:
            send_text(tg_id, f"🛑 <b>Đã dừng {job.tool_name}.</b>")
        except Exception as exc:
            send_text(tg_id, f"❌ <b>Lỗi {job.tool_name}</b>\n<code>{str(exc)[:3000]}</code>")
        finally:
            with JOB_LOCK:
                if ACTIVE_JOB is job:
                    ACTIVE_JOB = None
            with suppress(Exception):
                del CURRENT.ctx

    job.thread = threading.Thread(target=runner, name=f"vbtool-{tg_id}-{tool_key}", daemon=True)
    job.thread.start()
    return True, None


def stop_job(tg_id):
    global ACTIVE_JOB
    with JOB_LOCK:
        job = ACTIVE_JOB
        if not job or job.telegram_id != int(tg_id):
            return False, "Không có tool nào đang chạy."
        job.stop_event.set()
        job.answer_event.set()
    return True, "Đã gửi lệnh dừng."


# -----------------------------------------------------------------------------
# Telegram handlers
# -----------------------------------------------------------------------------
@bot.message_handler(commands=["start", "menu"])
def cmd_start(message):
    text, kb = main_menu(message.from_user.id)
    bot.send_message(message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    tg_id = call.from_user.id
    data = call.data or ""
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if data == "home":
        text, kb = main_menu(tg_id)
        bot.edit_message_text(text, tg_id, call.message.message_id, reply_markup=kb)
        return

    if data == "games":
        text, kb = games_menu()
        bot.edit_message_text(text, tg_id, call.message.message_id, reply_markup=kb)
        return

    if data == "key_menu":
        text, kb = key_menu()
        bot.edit_message_text(text, tg_id, call.message.message_id, reply_markup=kb)
        return

    if data == "free_link":
        ok, reason, _ = activation_valid(tg_id, refresh_vip=False)
        if ok:
            bot.send_message(tg_id, f"🔐 Bạn đã có key đang hoạt động: <b>{reason}</b>")
            return
        bot.send_message(tg_id, "⏳ Đang tạo link lấy Key FREE...")
        link, err = create_free_link(tg_id)
        if err:
            bot.send_message(tg_id, f"❌ {err}")
        else:
            bot.send_message(tg_id, f"🔗 <b>Link lấy Key FREE:</b>\n{link}\n\nSau khi vượt link, hãy gửi Key cho bot.")
        return

    if data == "vip_input":
        bot.send_message(tg_id, "💎 Hãy gửi Key VIP bằng một tin nhắn riêng.")
        PENDING_SETTINGS[tg_id] = {"mode": "vip_key"}
        return

    if data == "status":
        ok, reason, vip = activation_valid(tg_id, refresh_vip=True)
        text = "❌ Key chưa hợp lệ" if not ok else f"✅ {'VIP' if vip else 'FREE'} • {reason}"
        job = running_job_for(tg_id)
        running = job.tool_name if job else "Không"
        bot.send_message(tg_id, f"<b>📊 TRẠNG THÁI</b>\n🔐 {text}\n▶️ Đang chạy: {running}")
        return

    if data == "stop":
        ok, msg = stop_job(tg_id)
        bot.send_message(tg_id, ("🛑 " + msg) if ok else ("ℹ️ " + msg))
        return

    if data.startswith("game:"):
        key = data.split(":", 1)[1]
        if key not in TOOL_LABELS:
            return
        ok, reason, vip = activation_valid(tg_id, refresh_vip=True)
        if not ok:
            bot.send_message(tg_id, f"❌ Chưa thể chọn tool: {reason}")
            return
        if key == "4" and not vip:
            bot.send_message(tg_id, "❌ CANH CODE XWORLD chỉ dành cho Key VIP.")
            return
        CURRENT_SELECTION[tg_id] = TOOL_LABELS[key]
        PENDING_SETTINGS[tg_id] = {"mode": "selected_tool", "tool_key": key}
        bot.send_message(tg_id, f"✅ Đã chọn <b>{TOOL_LABELS[key]}</b>.\nBấm <b>▶️ Chạy bot</b> để bắt đầu.")
        return

    if data == "run_current":
        selected = None
        label = CURRENT_SELECTION.get(tg_id)
        for k, v in TOOL_LABELS.items():
            if v == label:
                selected = k
                break
        if not selected:
            bot.send_message(tg_id, "❌ Hãy chọn tool trước.")
            return
        ok, reason, vip = activation_valid(tg_id, refresh_vip=True)
        if not ok:
            bot.send_message(tg_id, f"❌ Key không hợp lệ: {reason}")
            return
        if selected == "4" and not vip:
            bot.send_message(tg_id, "❌ CANH CODE XWORLD chỉ dành cho Key VIP.")
            return
        started, err = start_job(tg_id, selected)
        bot.send_message(tg_id, "✅ Đã khởi động." if started else f"❌ {err}")
        return


@bot.message_handler(content_types=["text"])
def all_text(message):
    tg_id = message.from_user.id
    text = (message.text or "").strip()

    # 1) Nếu đang có tool chờ input, đẩy dữ liệu vào queue.
    job = running_job_for(tg_id)
    if job and job.waiting_prompt:
        job.answers.append(text)
        job.answer_event.set()
        return

    # 2) Key VIP nhập qua chat.
    pending = PENDING_SETTINGS.get(tg_id, {})
    if pending.get("mode") == "vip_key":
        PENDING_SETTINGS.pop(tg_id, None)
        bot.send_message(tg_id, "⏳ Đang xác thực Key VIP...")
        data, err = verify_vip_remote(tg_id, text)
        if err:
            bot.send_message(tg_id, f"❌ {err}")
            return
        status = str(data.get("status", "")).upper()
        if not data.get("success"):
            bot.send_message(tg_id, f"❌ Key VIP không hợp lệ: {data.get('message') or status or 'INVALID'}")
            return
        duration = float(data.get("duration", 24) or 24)
        key_type = str(data.get("key_type", "VIP") or "VIP").upper()
        forever = bool(data.get("is_forever"))
        start = now_utc()
        expiry = None if forever else (start + timedelta(hours=duration)).isoformat()
        put_user(tg_id, key=text, key_type=key_type, activated_at=start.isoformat(), expires_at=expiry, is_forever=1 if forever else 0)
        bot.send_message(tg_id, "✅ <b>Đã kích hoạt Key VIP thành công.</b>")
        return

    # 3) Key FREE sau khi vượt link.
    if len(text) >= 6 and tg_id in FREE_PENDING:
        ok, msg = activate_free(tg_id, text)
        if ok:
            bot.send_message(tg_id, "✅ <b>Đã kích hoạt Key FREE 24 giờ.</b>")
        else:
            bot.send_message(tg_id, f"❌ {msg}")
        return

    # 4) Lệnh chọn tool bằng số nhanh.
    if text in TOOL_LABELS:
        label = TOOL_LABELS[text]
        CURRENT_SELECTION[tg_id] = label
        bot.send_message(tg_id, f"✅ Đã chọn <b>{label}</b>.\nNhấn <b>▶️ Chạy bot</b> trong /menu để chạy.")
        return

    if text.lower() in {"stop", "dung", "dừng"}:
        ok, msg = stop_job(tg_id)
        bot.send_message(tg_id, ("🛑 " + msg) if ok else ("ℹ️ " + msg))
        return

    bot.send_message(tg_id, "ℹ️ Dùng /menu để mở menu Telegram.")


# Polling worker cho Render Background Worker.
def main():
    ORIG_PRINT("VBTOOL Telegram bot starting...")
    # Telegram có thể báo 409 nếu còn process polling khác dùng cùng BOT_TOKEN.
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
        except Exception as exc:
            ORIG_PRINT(f"Polling error: {exc}")
            _time.sleep(5)


if __name__ == "__main__":
    main()

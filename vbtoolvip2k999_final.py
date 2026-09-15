import sys
import subprocess
import importlib

REQUIRED_PACKAGES = {
    "requests": "requests",
    "rich": "rich",
    "pytz": "pytz",
    "websocket": "websocket-client",
    "colorama": "colorama",
}


def install_missing_packages():
    missing = []

    for module, package in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)

    if not missing:
        return

    print("")

    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                *missing,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


install_missing_packages()

import base64
import hashlib
import io
import json
import logging
import math
import os
import platform
import random
import re
import secrets
import threading
import time
import uuid
import webbrowser

from collections import Counter, defaultdict, deque
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
    wait,
    FIRST_COMPLETED,
)
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import pytz
import requests
import urllib3
import websocket

from colorama import Fore, Style, init

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, FloatPrompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

init(autoreset=True)

console = Console()

tool_start_time = time.time()

processed_issue_ids = set()

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
except Exception:
    pass

console = Console()

def force_exit_vbtool(code: int = 0):
    try:
        if threading.current_thread() is threading.main_thread():
            raise SystemExit(code)
        os._exit(code)
    except SystemExit:
        raise
    except Exception:
        try:
            os._exit(code)
        except Exception:
            raise

def show_key_expired_message_and_exit(delay: float = 2.0):
    try:
        console.print("\n[bold red]❌ KEY ĐÃ HẾT HẠN![/bold red]")
        console.print("[bold yellow]⚠️ Vui lòng nhập key khác để được sử dụng.[/bold yellow]")

    except Exception:
        pass

    try:
        time.sleep(delay)
    except Exception:
        pass

    force_exit_vbtool(0)

tz = pytz.timezone("Asia/Ho_Chi_Minh")

# ================== GIAO DIỆN VBTOOL ULTIMATE ==================

VBTOOL_COLORS = {"gold":"#FFD700","gold_dark":"#B8860B","platinum":"#E5E4E2","diamond":"#B9F2FF","ruby":"#E0115F","emerald":"#50C878","sapphire":"#0F52BA","amethyst":"#9966CC","onyx":"#353839","rose":"#FF007F","history_blue":"#3B5BDB","neon_pink":"#FF00E5","neon_green":"#39FF14","neon_orange":"#FF5E00","crimson":"#DC143C","turquoise":"#40E0D0","lavender":"#E6E6FA","bright_blue":"#5555FF","dark_blue":"#3B5BDB","bright_cyan":"#55FFFF","bold_cyan":"#00FFFF","neon_blue":"#00AEEF","white":"#FFFFFF","bright_green":"#00FF00","yellow":"#FFFF00","red":"#FF0000","green":"#008000","bold_green":"#00FF00"}

ICONS = {"crown":"👑","diamond":"💎","star":"⭐","fire":"🔥","lightning":"⚡","target":"🎯","shield":"🛡️","sword":"⚔️","brain":"🧠","robot":"🤖","rocket":"🚀","trophy":"🏆","medal":"🏅","gem":"💠","sparkle":"✨","settings":"⚙️","user":"👤","key":"🔑","lock":"🔒","unlock":"🔓","check":"✅","cross":"❌","warning":"⚠️","info":"ℹ️","money":"💰","chart":"📊","clock":"⏰","lotto":"🎲","dice":"🎯","plus":"➕","minus":"➖","arrow":"➡️","heart":"❤️","bell":"🔔","gift":"🎁","magic":"🔮","phone":"📞","vip":"💎","game":"🎮","Skull":"💀"}

LOGO_ULTIMATE = """
██╗   ██╗██████╗     ████████╗ ██████╗  ██████╗ ██╗
██║   ██║██╔══██╗    ╚══██╔══╝██╔═══██╗██╔═══██╗██║
██║   ██║██████╔╝       ██║   ██║   ██║██║   ██║██║
╚██╗ ██╔╝██╔══██╗       ██║   ██║   ██║██║   ██║██║
 ╚████╔╝ ██████╔╝       ██║   ╚██████╔╝╚██████╔╝███████╗
  ╚═══╝  ╚═════╝        ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
"""
LOGO_VBTOOL = LOGO_ULTIMATE
LOGO_SMALL = LOGO_ULTIMATE

# ================== HỆ THỐNG KEY ==================

DEVICE_ID_FILE = "device_id.txt"
SALT = "VBTOOLKEY"
TEMP_KEY_FILE = ".temp_key.txt"
ACTIVATION_FILE = "activation.dat"
LINK_HISTORY_FILE = "link_history.json"

VUOTNHANH_API = "https://vuotnhanh.com/api"
LINK4M_API = "https://link4m.co/api-shorten/v2"
LINK4M_TOKEN = "6a2391ae3f35952ad60cb3cf" 
ACCESS_TOKEN = "fd9a7822bac3990bd0e7e86de2317df0ded0c419ba6a4588baffbedecd06"
VUOTNHANH_TOKEN = "2e82a116-da12-4344-8eb0-936c9274a2f1"

ENCRYPTION_KEY = hashlib.sha256(b"VBTool_VIP").digest()

#========Telegaph================
def create_telegraph_page(key, device_id):
    url = "https://api.telegra.ph/createPage"

    content = json.dumps([
        {
            "tag": "p",
            "children": [
                "🔑 VBTOOL KEY"
            ]
        },
        {
            "tag": "p",
            "children": [
                f"📱 Device ID: {device_id}"
            ]
        },
        {
            "tag": "p",
            "children": [
                f"🔑 Key: {key}"
            ]
        },
        {
            "tag": "p",
            "children": [
                "⚠️ Key chỉ sử dụng trên thiết bị này."
            ]
        },
        {
            "tag": "p",
            "children": [
                "⚠️ Key chỉ được kích hoạt 1 lần, 1 thiết bị duy nhất."
            ]
        }
    ])

    data = {
        "access_token": ACCESS_TOKEN,
        "title": "KEY 24H",
        "author_name": "VBTOOL",
        "content": content,
        "return_content": False
    }

    r = requests.post(url, data=data)

    if r.status_code == 200:
        result = r.json()
        if result["ok"]:
            return result["result"]["url"]

    return None
    
# ================== KEY SERVER ==================
KEY_SERVER_URL = "https://keyvip-sever1.onrender.com"

# ================== HÀM MÃ HÓA ==================

def simple_encrypt(data: dict) -> str:
    try:
        json_str = json.dumps(data, sort_keys=True)
        key = ENCRYPTION_KEY
        encrypted = bytearray()
        for i, char in enumerate(json_str.encode('utf-8')):
            encrypted.append(char ^ key[i % len(key)])
        checksum = hashlib.sha256(json_str.encode()).hexdigest()
        result = base64.b64encode(bytes(encrypted)).decode()
        return f"{checksum}:{result}"
    except Exception:
        return ""

def simple_decrypt(encrypted_str: str) -> Optional[dict]:
    try:
        if not encrypted_str:
            return None
        parts = encrypted_str.split(':', 1)
        if len(parts) != 2:
            return None
        stored_checksum, encrypted_data = parts
        key = ENCRYPTION_KEY
        encrypted = base64.b64decode(encrypted_data.encode())
        decrypted = bytearray()
        for i, char in enumerate(encrypted):
            decrypted.append(char ^ key[i % len(key)])
        json_str = decrypted.decode('utf-8')
        if hashlib.sha256(json_str.encode()).hexdigest() != stored_checksum:
            return None
        return json.loads(json_str)
    except Exception:
        return None

# ================== QUẢN LÝ KEY ==================

def get_device_id() -> str:
    if Path(DEVICE_ID_FILE).exists():
        try:
            with open(DEVICE_ID_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    new_id = str(uuid.uuid4()).replace("-", "")[:32]
    try:
        with open(DEVICE_ID_FILE, "w", encoding="utf-8") as f:
            f.write(new_id)
    except Exception:
        pass
    return new_id

def encrypt_key(device_id: str, key: str) -> str:
    raw = f"{device_id}:{key}:{SALT}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

def check_internet_connection() -> bool:
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except Exception:
        return False
def is_vip_activated() -> bool:
    """Kiểm tra user có đang dùng key VIP không"""
    activation = load_activation()
    if not activation:
        return False
    key_type = activation.get("key_type", "FREE")
    return key_type == "VIP"

def verify_vip_key_from_server(device_id: str, key: str, quiet: bool = False) -> Optional[Dict]:
    """Kiểm tra key VIP trên server.

    quiet=True dùng cho background monitor để không chen thông báo vào
    Prompt/Setting của người dùng. Chỉ luồng nhập key trực tiếp mới in lỗi.
    """
    if not check_internet_connection():
        if not quiet:
            console.print("[bold red]❌ Không có kết nối internet![/bold red]")
        return None

    try:
        payload = {"device_id": device_id, "key": key}
        url = f"{KEY_SERVER_URL}/api/verify_key"
        resp = requests.post(url, json=payload, timeout=15)

        if resp.status_code != 200:
            if not quiet:
                console.print(f"[bold red]❌ HTTP Lỗi: {resp.status_code}[/bold red]")
            return None

        data = resp.json() if resp.content else {}
        if not isinstance(data, dict):
            return None

        status = str(data.get("status", "")).strip().upper()
        if data.get("success"):
            return {
                "status": status or "ACTIVE",
                "duration_hours": data.get("duration", 24),
                "key_type": data.get("key_type", "VIP"),
                "server_time": data.get("server_time", datetime.now().isoformat()),
                "is_vip": True,
                "is_forever": bool(data.get("is_forever", False)),
                "expires_at": data.get("expires_at"),
            }

        result = {
            "status": status or "INVALID",
            "message": data.get("message"),
            "duration_hours": data.get("duration"),
            "key_type": data.get("key_type"),
            "expires_at": data.get("expires_at"),
            "is_forever": bool(data.get("is_forever", False)),
        }

        # Chỉ in các trạng thái do người dùng chủ động kiểm tra.
        # Background monitor gọi quiet=True nên tuyệt đối không in "Key không tồn tại".
        if not quiet:
            if status == "REVOKED":
                console.print("[bold red]❌ KEY ĐÃ BỊ THU HỒI![/bold red]")
            elif status == "EXPIRED":
                console.print("[bold yellow]❌ KEY ĐÃ HẾT HẠN![/bold yellow]")
            elif status == "DEVICE_MISMATCH":
                console.print("[bold red]❌ KEY ĐÃ ĐƯỢC KÍCH HOẠT TRÊN THIẾT BỊ KHÁC![/bold red]")
            else:
                console.print(f"[bold red]❌ {data.get('message', 'Key không hợp lệ')}[/bold red]")
        return result

    except requests.exceptions.Timeout:
        if not quiet:
            console.print("[bold red]❌ Hết thời gian kiểm tra key.[/bold red]")
        return None
    except Exception as e:
        if not quiet:
            console.print(f"[bold red]❌ Lỗi kiểm tra key: {e}[/bold red]")
        else:
            log_debug(f"VIP verify background error: {e}")
        return None


def check_current_vip_key_server_status() -> Optional[str]:
    """Kiểm tra key đang lưu trên máy với server.

    Trả về ACTIVE / REVOKED / EXPIRED / DEVICE_MISMATCH / INVALID.
    None nghĩa là không thể kết nối/kiểm tra server.
    """
    activation = load_activation()
    if not activation or activation.get("key_type") != "VIP":
        return None

    key = str(activation.get("key", "")).strip()
    device_id = get_device_id()
    if not key:
        return "INVALID"

    result = verify_vip_key_from_server(device_id, key, quiet=True)
    if not result:
        return None
    return str(result.get("status", "INVALID")).upper()


def remove_local_activation(revoked: bool = False):
    """Xóa thông tin kích hoạt cục bộ khi key hết hạn/thu hồi."""
    try:
        if Path(ACTIVATION_FILE).exists():
            os.remove(ACTIVATION_FILE)
    except Exception:
        pass

    # Chỉ dọn dữ liệu link tạm nếu đó là key FREE.
    if not revoked:
        try:
            clear_link_history()
            if Path(TEMP_KEY_FILE).exists():
                os.remove(TEMP_KEY_FILE)
        except Exception:
            pass
        
def load_link_history() -> dict:
    if Path(LINK_HISTORY_FILE).exists():
        try:
            with open(LINK_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"link": None, "key": None, "device_id": None, "created_at": None}  

def save_link_history(link: str, key: str, device_id: str):
    data = {"link": link, "key": key, "device_id": device_id, "created_at": datetime.now().isoformat()}
    try:
        with open(LINK_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def clear_link_history():
    try:
        if Path(LINK_HISTORY_FILE).exists():
            os.remove(LINK_HISTORY_FILE)
    except Exception:
        pass

def create_free_key_link(device_id: str) -> Optional[str]:
    history = load_link_history()

    if history.get("link") and Path(TEMP_KEY_FILE).exists():
        console.print("[yellow][<>] Link lấy key free:[/yellow]")
        console.print(f"[bold cyan]🔗 {history['link']}[/bold cyan]")

        return history["link"]

    if history.get("link") and not Path(TEMP_KEY_FILE).exists():
        clear_link_history()

    secret_key = secrets.token_hex(4)
    encrypted = encrypt_key(device_id, secret_key)

    telegraph_url = create_telegraph_page(secret_key ,device_id)
    if not telegraph_url:
        console.print("[bold red]❌ Không thể tạo trang Telegraph![/bold red]")
        return None

    try:
        # Tạo link Link4m
        params_4m = {
            "api": LINK4M_TOKEN,
            "url": telegraph_url
        }

        r1 = requests.get(LINK4M_API, params=params_4m, timeout=10)
        if r1.status_code != 200:
            console.print("[bold red]❌ Lỗi Link4m.[/bold red]")
            return None

        data1 = r1.json()
        if data1.get("status") != "success":
            console.print("[bold red]❌ Lỗi API Link4m.[/bold red]")
            return None

        link4m_url = data1.get("shortenedUrl")

        # Tạo link Vượt Nhanh
        params_vn = {
            "api": VUOTNHANH_TOKEN,
            "url": link4m_url
        }

        r2 = requests.get(VUOTNHANH_API, params=params_vn, timeout=10)
        if r2.status_code != 200:
            console.print("[bold red]❌ Lỗi Vuotnhanh.[/bold red]")
            return None

        data2 = r2.json()
        if data2.get("status") != "success":
            console.print("[bold red]❌ Lỗi API Vuotnhanh.[/bold red]")
            return None

        final_url = data2.get("shortenedUrl")

        with open(TEMP_KEY_FILE, "w", encoding="utf-8") as f:
            f.write(f"{encrypted}\n{final_url}")

        save_link_history(final_url, secret_key, device_id)
        return final_url

    except Exception as e:
        console.print(f"[red]❌ Lỗi: {e}[/red]")
        return None

# ================== HÀM ACTIVATION ==================

def save_activation(device_id: str, key: str, activation_time: datetime, duration_hours: int, key_type: str = "FREE"):
    is_vip = (key_type == "VIP")
    data = {
        "device_id": device_id,
        "key": key,
        "key_type": key_type,
        "activation_time": activation_time.isoformat(),
        "expiry_time": (activation_time + timedelta(hours=duration_hours)).isoformat(),
        "duration_hours": duration_hours,
        "is_vip": is_vip,

        "checksum": hashlib.sha256(f"{device_id}:{key}:{activation_time.isoformat()}:{SALT}".encode()).hexdigest()
    }
    encrypted_data = simple_encrypt(data)
    if encrypted_data:
        try:
            with open(ACTIVATION_FILE, "w", encoding="utf-8") as f:
                f.write(encrypted_data)
            return True
        except Exception:
            pass
    return False

def load_activation() -> Optional[Dict]:
    if not Path(ACTIVATION_FILE).exists():
        return None
    try:
        with open(ACTIVATION_FILE, "r", encoding="utf-8") as f:
            encrypted_data = f.read().strip()
        if not encrypted_data:
            return None
        data = simple_decrypt(encrypted_data)
        if not data:
            try:
                os.remove(ACTIVATION_FILE)
            except Exception:
                pass
            return None
        expected_checksum = hashlib.sha256(
            f"{data.get('device_id', '')}:{data.get('key', '')}:{data.get('activation_time', '')}:{SALT}".encode()
        ).hexdigest()
        if data.get("checksum") != expected_checksum:
            try:
                os.remove(ACTIVATION_FILE)
            except Exception:
                pass
            return None
        return data
    except Exception:
        return None

def check_activation_valid(exit_on_expired: bool = True) -> Tuple[bool, Optional[str], bool]:
    activation = load_activation()
    if not activation:
        return False, "Chưa kích hoạt", False
    try:
        current_device = get_device_id()
        if activation.get("device_id") != current_device:
            try:
                os.remove(ACTIVATION_FILE)
                console.print("[bold red]❌ Device ID không khớp! Key đã dùng trên máy khác.[/bold red]")
            except Exception:
                pass
            return False, "Device ID không khớp", False
        key_type = activation.get("key_type", "FREE")
        expiry_time = datetime.fromisoformat(activation["expiry_time"])
        now = datetime.now()
        if key_type == "FREE":
            tomorrow = now + timedelta(days=1)
            next_midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            if now >= next_midnight:
                try:
                    os.remove(ACTIVATION_FILE)
                    clear_link_history()
                    if Path(TEMP_KEY_FILE).exists():
                        os.remove(TEMP_KEY_FILE)
                    console.print("[bold yellow] [<>] Key free đã reset lúc 00h! Nhập key mới.[/bold yellow]")
                except Exception:
                    pass
                return False, "Key free đã reset", False
        if now > expiry_time:
            try:
                os.remove(ACTIVATION_FILE)

                if key_type == "FREE":
                    clear_link_history()
                    if Path(TEMP_KEY_FILE).exists():
                        os.remove(TEMP_KEY_FILE)
            except Exception:
                pass

            if exit_on_expired:
                show_key_expired_message_and_exit(2)
            return False, "KEY ĐÃ HẾT HẠN", False
        remaining = expiry_time - now
        days = remaining.total_seconds() / 86400
        hours = remaining.total_seconds() / 3600
        is_vip = activation.get("is_vip", False)

        if days >= 1:
            return True, f"Còn {days:.1f} ngày", is_vip
        else:
            return True, f"Còn {hours:.1f} giờ", is_vip
    except Exception as e:
        try:
            os.remove(ACTIVATION_FILE)
        except Exception:
            pass
        return False, f"Lỗi: {e}", False

_key_monitor_started = False

def start_key_expiry_monitor():
    global _key_monitor_started
    if _key_monitor_started:
        return
    _key_monitor_started = True
    threading.Thread(target=key_expiry_monitor, daemon=True).start()

def _activation_is_expired_or_reset() -> bool:
    activation = load_activation()
    if not activation:
        return False
    try:
        expiry_time = datetime.fromisoformat(activation["expiry_time"])
        now = datetime.now()
        if now > expiry_time:
            return True
        if activation.get("key_type", "FREE") == "FREE":
            tomorrow = now + timedelta(days=1)
            next_midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            if now >= next_midnight:
                return True
    except Exception:
        return False
    return False

def key_expiry_monitor():
    """Theo dõi key nền nhưng không làm nhiễu giao diện.

    Chỉ xử lý khi server xác nhận rõ trạng thái terminal liên tiếp 2 lần.
    Lỗi mạng/HTTP/INVALID tạm thời sẽ bị bỏ qua, không tự xóa key.
    """
    server_check_interval = 10.0
    last_server_check = 0.0
    terminal_seen = {"REVOKED": 0, "EXPIRED": 0, "DEVICE_MISMATCH": 0}

    while True:
        try:
            if _activation_is_expired_or_reset():
                try:
                    check_activation_valid(exit_on_expired=False)
                except Exception:
                    pass
                try:
                    _shutdown_vth_runtime("[bold yellow][<>] Key đã hết hạn[/bold yellow]")
                except Exception:
                    pass
                return

            now = time.time()
            if now - last_server_check >= server_check_interval:
                last_server_check = now
                activation = load_activation()
                if activation and activation.get("key_type") == "VIP":
                    key = str(activation.get("key", "")).strip()
                    device_id = get_device_id()
                    result = verify_vip_key_from_server(device_id, key, quiet=True) if key else None
                    status = str((result or {}).get("status", "")).upper()

                    if status in terminal_seen:
                        for other in terminal_seen:
                            if other != status:
                                terminal_seen[other] = 0
                        terminal_seen[status] += 1
                    else:
                        for other in terminal_seen:
                            terminal_seen[other] = 0

                    if status == "REVOKED" and terminal_seen[status] >= 2:
                        remove_local_activation(revoked=True)
                        _shutdown_vth_runtime("[bold red]❌ KEY ĐÃ BỊ THU HỒI![/bold red]")
                        return

                    if status == "EXPIRED" and terminal_seen[status] >= 2:
                        remove_local_activation(revoked=False)
                        _shutdown_vth_runtime("[bold yellow]❌ KEY ĐÃ HẾT HẠN![/bold yellow]")
                        return

                    if status == "DEVICE_MISMATCH" and terminal_seen[status] >= 2:
                        remove_local_activation(revoked=True)
                        _shutdown_vth_runtime("[bold red]❌ KEY KHÔNG THUỘC THIẾT BỊ NÀY![/bold red]")
                        return
        except Exception as e:
            log_debug(f"key_expiry_monitor error: {e}")

        time.sleep(1)
# ================== GIAO DIỆN CHÍNH ==================

def build_logo_with_gradient(logo_text: str) -> Text:
    lines = logo_text.strip("\n").split("\n")
    result = Text()
    start_rgb=(180,255,255)
    end_rgb=(0,60,255)
    for line in lines:
        length=max(len(line)-1,1)
        for i,ch in enumerate(line):
            if ch==" ":
                result.append(" ")
            else:
                t=i/length
                r=int(start_rgb[0]+(end_rgb[0]-start_rgb[0])*t)
                g=int(start_rgb[1]+(end_rgb[1]-start_rgb[1])*t)
                b=int(start_rgb[2]+(end_rgb[2]-start_rgb[2])*t)
                result.append(ch,style=f"bold rgb({r},{g},{b})")
        result.append("\n")
    return result
    
def show_ultimate_header():
    logo = build_logo_with_gradient(LOGO_ULTIMATE)

    activation = load_activation()
    key_type = ""
    key_color = "bold white"    
    key_time = "   ⏰ Không có"

    if activation:
        try:
            if activation.get("key_type") == "VIP":
                key_type = "VIP"
                key_color = "bold red"
            else:
                key_type = "FREE"
                key_color = "bold green"

            expiry_time = datetime.fromisoformat(activation["expiry_time"])
            remaining = expiry_time - datetime.now()

            if remaining.total_seconds() > 0:
                days = remaining.days
                hours = (remaining.seconds % 86400) // 3600
                minutes = (remaining.seconds % 3600) // 60

                if days > 0:
                    key_time = f"⏰ Còn {days} Ngày {hours} Giờ"
                elif hours > 0:
                    key_time = f"⏰ Còn {hours} Giờ {minutes} Phút"
                else:
                    key_time = f"⏰ Còn {minutes} Phút"
            else:
                key_time = "❌ Đã hết hạn"

        except Exception:
            key_type = "Không xác định"
            key_color = "bold red"
            key_time = "❌ Không xác định"

    info = Text.assemble(
        ("\n", ""),
        (f"{ICONS['user']} Admin : ", "bold magenta"),
        ("Nguyễn Văn Bảo", "bold cyan"),
        ("              ", ""),
        (f"{ICONS['phone']} ", "bold gold"),
        ("Zalo : ", "bold orange1"),
        ("0797676482", "bold white"),
        ("\n", ""),
        ("💎 Loại Key : ", "bold deepsky_blue1"),
        (key_type, key_color),
        ("                      ", ""),
        (key_time, "bold bright_green"),
        ("\n", ""),
        ("━" * 60 + "\n", f"dim {VBTOOL_COLORS['gold']}"),
    )

    return Group(
        Align.center(logo),
        Align.center(info),
    )

def show_key_menu() -> Tuple[bool, Optional[str], bool]:
    check_activation_valid()

    console.clear()
    console.print(show_ultimate_header())

    console.print(f"[dim {VBTOOL_COLORS['white']}]" + "━" * 53 + "[/]")

    console.print(
        "[bold green][<>] Nhập 1 - Lấy Key miễn phí (Vượt link lấy key)[/bold green]")

    console.print(    
        "[bold red][<>] Nhập 2 - Nhập Key VIP (Mở khoá tài khoản VIP)[/bold red]")

    console.print(f"[dim {VBTOOL_COLORS['white']}]" + "━" * 53 + "[/]")

    while True:
        choice = Prompt.ask(f"[bold {VBTOOL_COLORS['history_blue']}][<>] Nhập lựa chọn [1/2][/bold {VBTOOL_COLORS['history_blue']}]"
        ).strip()

        if choice in ("1", "2"):
            break

        console.print(f"[bold red]❌ Lựa chọn không hợp lệ![/bold red]")
        time.sleep(1)

    if choice == "1":
        device_id = get_device_id()

        # Nếu FREE còn hạn thì vào tool luôn
        activation = load_activation()
        if activation and activation.get("key_type") == "FREE":
            try:
                expiry = datetime.fromisoformat(activation["expiry_time"])
                if datetime.now() < expiry:
                    console.print("[bold green][<>] Key FREE còn hạn - Đang mở Tool...[/bold green]")
                    time.sleep(1)
                    return True, activation["key"], False
            except Exception:
                pass

        history = load_link_history()
        temp_key_exists = Path(TEMP_KEY_FILE).exists()

        if history.get("link") and temp_key_exists:
            console.print(f"[bold green][<>] Link lấy key free: [bold green]{history['link']}[/bold green]")

            webbrowser.open(history["link"])
        else:
            if history.get("link") and not temp_key_exists:
                console.print("[yellow][<>] Phát hiện link cũ nhưng thiếu file key. Tạo lại link mới...[/yellow]")
                clear_link_history()

            console.print("[bold green][<>][/bold green] [bold green]Đang tạo link vượt key...[/bold green]")
            link = create_free_key_link(device_id)
            
            if link:
                console.print(f"[bold green][<>][/bold green] [bold green]Link Vượt Key:[/bold green] [bold cyan]{link}[/bold cyan]")
                console.print(f"[bold green][<>][/bold green] [bold red]Device ID:[/bold red] [bold yellow]{device_id}[/bold yellow]")
                webbrowser.open(link)
            else:
                console.print("[bold red]❌ Lấy link thất bại![/bold red]")
                time.sleep(2)
                return False, None, False

        user_key = Prompt.ask(
                "[bold green][<>][/bold green] [bold yellow]Nhập Key Sau Khi Vượt Link[/bold yellow]"
)

        if Path(TEMP_KEY_FILE).exists():
            try:
                with open(TEMP_KEY_FILE, "r", encoding="utf-8") as f:
                    lines = f.read().strip().split("\n")
                    if len(lines) >= 1:
                        stored_encrypted = lines[0]
                    else:
                        console.print("[bold red]❌ Lấy key lỗi! Vui lòng lấy lại link.[/bold red]")
                        clear_link_history()
                        if Path(TEMP_KEY_FILE).exists():
                            os.remove(TEMP_KEY_FILE)
                        time.sleep(2)
                        return False, None, False
            except Exception:
                console.print("[bold red]❌ Lỗi đọc file key! Vui lòng tạo lại link.[/bold red]")
                clear_link_history()
                if Path(TEMP_KEY_FILE).exists():
                    os.remove(TEMP_KEY_FILE)
                time.sleep(2)
                return False, None, False

            input_encrypted = encrypt_key(device_id, user_key)

            if stored_encrypted == input_encrypted:
                duration = 24
                key_type = "FREE"
                now = datetime.now()

                if save_activation(device_id, user_key, now, duration, key_type):
                    if Path(TEMP_KEY_FILE).exists():
                        os.remove(TEMP_KEY_FILE)

                    clear_link_history()

                    console.print(f"[bold green][<>] Đã kích hoạt key thành công! {duration}h.[/bold green]")
                    console.print("[bold yellow][<>] Key chỉ dùng 1 lần![/bold yellow]")

                    time.sleep(2)
                    return True, user_key, False
                else:
                    console.print("[bold red]❌ Lỗi lưu kích hoạt![/bold red]")
                    time.sleep(2)
                    return False, None, False
            else:
                console.print("[bold red]❌ Key sai! Vui lòng lấy link mới.[/bold red]")
                if Path(TEMP_KEY_FILE).exists():
                    os.remove(TEMP_KEY_FILE)
                clear_link_history()
                time.sleep(2)
                return False, None, False
        else:
            console.print("[bold red][<>] Không tìm thấy file key tạm! Vui lòng tạo lại link.[/bold red]")
            clear_link_history()
            time.sleep(2)
            return False, None, False

    elif choice == "2":
        device_id = get_device_id()

        # Nếu VIP còn hạn thì vào tool luôn
        activation = load_activation()
        if activation and activation.get("key_type") == "VIP":
            try:
                expiry = datetime.fromisoformat(activation["expiry_time"])
                if datetime.now() < expiry:
                    console.print("[bold green][<>] Key VIP còn hạn - Đang mở Tool...[/bold green]")
                    time.sleep(1)
                    return True, activation["key"], True
            except Exception:
                pass

        user_key = Prompt.ask(f"[bold {VBTOOL_COLORS['red']}][<>] Nhập Key VIP[/bold {VBTOOL_COLORS['red']}]")

        console.print("[bold red][<>] Đang kiểm tra key...[/bold red]")

        server_result = verify_vip_key_from_server(device_id, user_key)

        if server_result and server_result.get("status") in {"REVOKED", "EXPIRED", "DEVICE_MISMATCH", "INVALID"}:
            time.sleep(2)
            return False, None, False

        if server_result:
            duration = server_result.get("duration_hours", 24)
            key_type = server_result.get("key_type", "VIP")
            is_forever = server_result.get("is_forever", False)

            now = datetime.now()

            if save_activation(device_id, user_key, now, duration, key_type):
                if is_forever:
                    time_text = "VĨNH VIỄN (10 năm)"
                elif duration >= 72:
                    time_text = f"{duration / 24:.0f} ngày"
                else:
                    time_text = f"{duration} giờ"

                console.print(f"[bold green][<>] Đã kích hoạt key thành công! {time_text}.[/bold green]")
                console.print("[bold yellow][<>] Key chỉ dùng 1 lần![/bold yellow]")
                console.print("[bold red][<>] Đã kích hoạt tài khoản VIP[/bold red]")
                time.sleep(2)
                return True, user_key, True

            console.print("[bold red]❌ Lỗi lưu kích hoạt![/bold red]")
            time.sleep(2)
            return False, None, False

        console.print("[bold red]❌ Key không hợp lệ hoặc không xác nhận được key![/bold red]")
        time.sleep(3)
        return False, None, False

def show_tool_selection() -> str:
    console.clear()
    console.print(show_ultimate_header())
    _, _, is_vip = check_activation_valid(exit_on_expired=False)

    vip_note = "" if is_vip else " (Chỉ Key VIP)"

    console.print(Panel(
        Align.center(Text(f"{ICONS['game']} CHỌN GAME",
        style=f"bold {VBTOOL_COLORS['bold_cyan']}")),
        border_style=VBTOOL_COLORS["neon_pink"],
        box=box.ROUNDED,
        padding=(0, 2)
    ))

    console.print(Panel(
        Align.center(Text.assemble(
            ("  1. ", f"bold {VBTOOL_COLORS['bold_cyan']}"),
            ("VUA THOÁT HIỂM", f"bold {VBTOOL_COLORS['bold_cyan']}"),
            (" • Auto đặt cược, hỗ trợ nhiều thuật toán\n", "dim"),
            ("  2. ", f"bold {VBTOOL_COLORS['neon_pink']}"),
            ("LOTTO", f"bold {VBTOOL_COLORS['neon_pink']}"),
            (" • Phân tích cầu LOTTO, dự đoán xác suất\n", "dim"),
            ("  3. ", f"bold {VBTOOL_COLORS['gold']}"),
            ("CHẠY ĐUA TỐC ĐỘ", f"bold {VBTOOL_COLORS['gold']}"),
            (" • Auto cược (USDT/BUILD/WORLD)\n", "dim"),
            ("  4. ", f"bold {VBTOOL_COLORS['bright_green']}"),
            ("CANH CODE XWORLD", f"bold {VBTOOL_COLORS['bright_green']}"),
            (f" • Theo dõi code, kiểm tra và nhập code tự động{vip_note}\n", "dim"),
            ("  5. ", f"bold {VBTOOL_COLORS['diamond']}"),
            ("HILO", f"bold {VBTOOL_COLORS['diamond']}"),
            (" • Auto Hilo && dự đoán lá tiếp theo", "dim"),
        )),
        border_style=VBTOOL_COLORS["history_blue"],
        box=box.DOUBLE,
        padding=(1, 4)))

    return Prompt.ask(f"[bold {VBTOOL_COLORS['yellow']}]👉 Nhập lựa chọn của bạn [1/2/3/4/5][/bold {VBTOOL_COLORS['yellow']}]")

# ================== TOOL 1: VUA THOÁT HIỂM ==================

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

BET_API_URL = "https://api.escapemaster.net/escape_game/bet"
WS_URL = "wss://api.escapemaster.net/escape_master/ws"
WALLET_API_URL = "https://wallet.3games.io/api/wallet/user_asset"

HTTP = requests.Session()
try:
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=50, max_retries=Retry(total=3, backoff_factor=0.2, status_forcelist=(500, 502, 503, 504)))
    HTTP.mount("https://", adapter)
    HTTP.mount("http://", adapter)
except Exception:
    pass

ROOM_NAMES = {1: "📦 Nhà kho", 2: "🪑 Phòng họp", 3: "👔 Phòng giám đốc", 4: "💬 Phòng trò chuyện", 5: "🎥 Phòng giám sát", 6: "🏢 Văn phòng", 7: "💰 Phòng tài vụ", 8: "👥 Phòng nhân sự"}
ROOM_ORDER = [1, 2, 3, 4, 5, 6, 7, 8]

USER_ID: Optional[int] = None
SECRET_KEY: Optional[str] = None
IS_VIP_USER: bool = False
issue_id: Optional[int] = None
issue_start_ts: Optional[float] = None
issue_end_ts: Optional[float] = None
count_down: Optional[int] = None
killed_room: Optional[int] = None
round_index: int = 0

room_state: Dict[int, Dict[str, Any]] = {r: {"players": 0, "bet": 0} for r in ROOM_ORDER}
room_stats: Dict[int, Dict[str, Any]] = {r: {"kills": 0, "survives": 0, "last_kill_round": None, "last_players": 0, "last_bet": 0} for r in ROOM_ORDER}

predicted_room: Optional[int] = None
last_killed_room: Optional[int] = None
last_killed_room_delayed: Optional[int] = None
prediction_locked: bool = False

current_build: Optional[float] = None
current_usdt: Optional[float] = None
current_world: Optional[float] = None
last_balance_ts: Optional[float] = None
last_balance_val: Optional[float] = None
starting_balance: Optional[float] = None
cumulative_profit: Optional[float] = None

win_streak: int = 0
lose_streak: int = 0
max_win_streak: int = 0
max_lose_streak: int = 0

base_bet: float = 1.0
multiplier: float = 2.0
current_bet: Optional[float] = None
last_display_bet: float = 0.0
run_mode: str = "AUTO"
bet_rounds_before_skip: int = 0
_rounds_placed_since_skip: int = 0
skip_next_round_flag: bool = False

bet_history: deque = deque(maxlen=200)
bet_sent_for_issue: set = set()

pause_after_losses: int = 0
_skip_rounds_remaining: int = 0
profit_target: Optional[float] = None
stop_when_profit_reached: bool = False
stop_loss_target: Optional[float] = None
stop_when_loss_reached: bool = False
stop_flag: bool = False

ui_state: str = "IDLE"
analysis_duration: float = 45.0
analysis_initial_delay: float = 1.5
analysis_ready_ts: Optional[float] = None
analysis_start_ts: Optional[float] = None

def _vth_get_remaining_seconds() -> Optional[float]:
    """
    UI chỉ chạy theo countdown server vừa gửi.
    Không tự trôi theo đồng hồ nội bộ giữa các lần cập nhật.
    """
    try:
        if count_down is not None:
            return max(0.0, float(count_down))
    except Exception:
        pass
    return None

last_msg_ts: float = time.time()
last_balance_fetch_ts: float = 0.0
BALANCE_POLL_INTERVAL: float = 4.0
_ws: Dict[str, Any] = {"ws": None}
active_vth_poller: Optional[Any] = None

def _shutdown_vth_runtime(message: Optional[str] = None):
    global stop_flag, active_vth_poller
    stop_flag = True

    if message:
        try:
            console.print(message)
        except Exception:
            pass

    poller = active_vth_poller
    active_vth_poller = None
    if poller is not None:
        try:
            poller.stop()
        except Exception:
            pass

    try:
        wsobj = _ws.get("ws")
        if wsobj:
            wsobj.close()
    except Exception:
        pass

_sequential_bet_index = 0
killer_history = deque(maxlen=20)
game_kill_log = deque(maxlen=10)
processed_result_issues = set()
history_recorded_issue = set()
# Khóa cố định phòng đã chọn theo từng ván để lịch sử luôn trùng 100% với mục tiêu đã hiển thị.
bet_selection_by_issue: Dict[int, Dict[str, Any]] = {}

# ================== 22 LOGIC CHO VUA THOÁT HIỂM ==================
SELECTION_MODES = {
    # Logic FREE (1-13)
    "RANDOM": "Ngẫu Nhiên",
    "MIN_PLAYER_BET": "An Toàn ",
    "PROBABILITY": "Tính Xác Suất",
    "FOLLOW_KILLER": "Bám Theo Sát Thủ",
    "MIN_BET": "Ít Cược",
    "SEQUENTIAL": "Theo Thứ Tự (P1->P8)",
    "KILLER_PERSONALITY": "Tính Cách Sát Thủ",
    "ALL": "ALL IN (Cược hết số dư)",
    "SMART_SAFE": "Né Sát Thủ Thông Minh",
    "FOLLOW_KILLER_DELAYED": "Theo Dấu Sát Thủ",
    "HIDE_SEEK_MASTER": "Bậc Thầy Trốn Tìm",
    "MANY_PLAYER_LOW_BET": "Nhiều Người Ít Cược",
    "HOT_SAFE": "Né Rủi Ro",
    # Logic VIP (14-23)
    "HOA_THAN": "Hoá Thần (VIP)",
    "KILLER_WAVE": "Bắt Xu Hướng (VIP)",
    "PSYCHO_ANALYSIS": "VBTTH-AI (VIP)",   
    "DEEP_ANALYSIS": "Phân Tích Chuyên Sâu (VIP)",
    "MARKOV_CHAIN": "Siêu Phân Tích V1 (VIP)",    
    "GOD_MODE": "Thần Thánh AI (VIP)",    
    "HUNTER": "Thợ Săn (VIP)",
    "HEAVEN_EYE": "Siêu Phân Tích V2 (VIP)",
    "INFINITY": "Tối Thượng (VIP)",
    "TONG_HOP": "Tổng Hợp (VIP)",}

settings = {"algo": "RANDOM"}
selected_vth_algo = "RANDOM"
STRATEGY_CONFIG_FILE = "strategy.json"
_spinner = ["📦", "🪑", "👔", "💬", "🎥", "🏢", "💰", "👥"]
_num_re = re.compile(r"-?\d+[\d,]*\.?\d*")
VIP_COLORS = ["#FF00FF", "#D700FF", "#AF00FF", "#8700FF", "#5F00FF", "#0000FF", "#005FFF", "#0087FF", "#00AFFF", "#00D7FF", "#00FFFF"]

# ================== CÁC HÀM HỖ TRỢ VTH ==================

def slow_print(text: str, delay: float = 0.01, style: Optional[str] = None):
    for char in text:
        console.print(Text(char, style=style or "default"), end="")
        time.sleep(delay)
    console.print()

def log_debug(msg: str):
    try:
        logger.debug(msg)
    except Exception:
        pass

def _parse_number(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x)
    m = _num_re.search(s)
    if not m:
        return None
    token = m.group(0).replace(",", "")
    try:
        return float(token)
    except Exception:
        return None

def human_ts() -> str:
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def safe_input(prompt: str, default=None, cast=None):
    try:
        s = input(prompt).strip()
    except EOFError:
        return default
    if s == "":
        return default
    if cast:
        try:
            return cast(s)
        except Exception:
            return default
    return s

def _parse_balance_from_json(j: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    if not isinstance(j, dict):
        return None, None, None
    build = None
    world = None
    usdt = None
    data = j.get("data") if isinstance(j.get("data"), dict) else j
    if isinstance(data, dict):
        cwallet = data.get("cwallet") if isinstance(data.get("cwallet"), dict) else None
        if cwallet:
            for key in ("ctoken_contribute", "ctoken", "build", "balance", "amount"):
                if key in cwallet and build is None:
                    build = _parse_number(cwallet.get(key))
        for k in ("build", "ctoken", "ctoken_contribute"):
            if build is None and k in data:
                build = _parse_number(data.get(k))
        for k in ("usdt", "kusdt", "usdt_balance"):
            if usdt is None and k in data:
                usdt = _parse_number(data.get(k))
        for k in ("world", "xworld"):
            if world is None and k in data:
                world = _parse_number(data.get(k))
    found = []
    def walk(o: Any, path=""):
        if isinstance(o, dict):
            for kk, vv in o.items():
                nk = (path + "." + str(kk)).strip(".")
                if isinstance(vv, (dict, list)):
                    walk(vv, nk)
                else:
                    n = _parse_number(vv)
                    if n is not None:
                        found.append((nk.lower(), n))
        elif isinstance(o, list):
            for idx, it in enumerate(o):
                walk(it, f"{path}[{idx}]")
    walk(j)
    for k, n in found:
        if build is None and any(x in k for x in ("ctoken", "build", "contribute", "balance")):
            build = n
        if usdt is None and "usdt" in k:
            usdt = n
        if world is None and any(x in k for x in ("world", "xworld")):
            world = n
    return build, world, usdt

def balance_headers_for(uid: Optional[int] = None, secret: Optional[str] = None) -> Dict[str, str]:
    h = {"accept": "*/*", "accept-language": "vi,en;q=0.9", "cache-control": "no-cache", "country-code": "vn", "origin": "https://xworld.info", "pragma": "no-cache", "referer": "https://xworld.info/", "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36", "user-login": "login_v2", "xb-language": "vi-VN"}
    if uid is not None:
        h["user-id"] = str(uid)
    if secret:
        h["user-secret-key"] = str(secret)
    return h

def fetch_balances_3games(retries=3, timeout=8, params=None, uid=None, secret=None):
    global current_build, current_usdt, current_world, last_balance_ts, starting_balance, last_balance_val, cumulative_profit
    uid = uid or USER_ID
    secret = secret or SECRET_KEY
    payload = {"user_id": int(uid) if uid is not None else None, "source": "home"}
    attempt = 0
    while attempt <= retries:
        attempt += 1
        try:
            r = HTTP.post(WALLET_API_URL, json=payload, headers=balance_headers_for(uid, secret), timeout=timeout)
            r.raise_for_status()
            j = r.json()
            data = j.get("data", {}) if isinstance(j, dict) else {}
            ua = data.get("user_asset", {}) if isinstance(data, dict) else {}
            build = _parse_number(ua.get("BUILD"))
            world = _parse_number(ua.get("WORLD"))
            usdt = _parse_number(ua.get("USDT"))
            if build is not None:
                if last_balance_val is None:
                    starting_balance = build
                    last_balance_val = build
                else:
                    last_balance_val = build
                current_build = build
                if starting_balance is not None:
                    cumulative_profit = current_build - starting_balance
            if usdt is not None:
                current_usdt = usdt
            if world is not None:
                current_world = world
            last_balance_ts = time.time()
            return current_build, current_world, current_usdt
        except Exception as e:
            log_debug(f"wallet fetch attempt {attempt} error: {e}")
            time.sleep(min(1.5 * attempt, 4))
    return current_build, current_world, current_usdt

# ================== 22 LOGIC CHỌN PHÒNG ==================

# Logic 1: Ngẫu Nhiên
def choose_random():
    return random.choice(ROOM_ORDER)
# Logic 2:An Toàn    
def choose_min_player_bet():
    if not ROOM_ORDER:
        return 1
    scores = {}
    max_players = max((room_state[r]["players"] for r in ROOM_ORDER), default=1)
    max_bet = max((room_state[r]["bet"] for r in ROOM_ORDER), default=1)
    if max_players <= 0:
        max_players = 1
    if max_bet <= 0:
        max_bet = 1
    for r in ROOM_ORDER:
        player_score = 1 - (room_state[r]["players"] / max_players)
        bet_score = 1 - (room_state[r]["bet"] / max_bet)
        scores[r] = (
            player_score * 0.60 +
            bet_score * 0.40
        )
        if r == last_killed_room:
            scores[r] -= 0.25
    return max(scores, key=scores.get)

# Logic 3: Tính xác xuất
def choose_probability():
    scores = {}
    for r in ROOM_ORDER:
        kills = room_stats[r]["kills"]
        survives = room_stats[r]["survives"]
        total = kills + survives
        survival_rate = survives / total if total > 0 else 0.5
        if r == last_killed_room:
            survival_rate -= 0.25
        scores[r] = survival_rate
    return max(scores, key=scores.get)

# Logic 4: Bám Theo Sát Thủ
def choose_follow_killer():
    if last_killed_room is not None and last_killed_room in ROOM_ORDER:
        return last_killed_room
    return random.choice(ROOM_ORDER)

# Logic 5: Ít Cược
def choose_min_bet():
    if not ROOM_ORDER:
        return 1
    scores = {}
    max_bet = max((room_state[r]["bet"] for r in ROOM_ORDER), default=1)
    if max_bet <= 0:
        max_bet = 1
    for r in ROOM_ORDER:
        scores[r] = 1 - (room_state[r]["bet"] / max_bet)
        if r == last_killed_room:
            scores[r] -= 0.25
    return max(scores, key=scores.get)
    
# Logic 6: Theo Thứ Tự (P1->P8)
def choose_sequential():
    global _sequential_bet_index
    room_to_bet = ROOM_ORDER[_sequential_bet_index]
    _sequential_bet_index = (_sequential_bet_index + 1) % len(ROOM_ORDER)
    return room_to_bet

# Logic 7: TÍNH CÁCH SÁT THỦ
def choose_killer_personality():
    if not killer_history:
        return choose_random()
    avg_players = sum(h['players'] for h in killer_history) / len(killer_history)
    avg_bet = sum(h['bet'] for h in killer_history) / len(killer_history)
    avoidance_scores = {}
    for r in ROOM_ORDER:
        if r == last_killed_room:
            avoidance_scores[r] = -999999
            continue
        current_players = room_state[r]['players']
        current_bet = room_state[r]['bet']
        player_dist = abs(current_players - avg_players) / (avg_players + 1)
        bet_dist = abs(current_bet - avg_bet) / (avg_bet + 1)
        avoidance_scores[r] = player_dist + bet_dist
    return max(avoidance_scores, key=avoidance_scores.get)
    
# Logic 8: ALL IN
def choose_all():
    if not ROOM_ORDER:
        return 1

    if len(ROOM_ORDER) == 1:
        return ROOM_ORDER[0]

    max_players = max(
        (
            room_state.get(r, {}).get("players", 0)
            for r in ROOM_ORDER
        ),
        default=1
    ) or 1

    max_bet = max(
        (
            room_state.get(r, {}).get("bet", 0)
            for r in ROOM_ORDER
        ),
        default=1
    ) or 1

    full_history = list(game_kill_log)
    history100 = full_history[-100:]
    history10 = history100[-10:]

    scores = {}
    current_gaps = {}

    for room in ROOM_ORDER:
        state = room_state.get(room, {})

        players = max(
            0.0,
            float(state.get("players", 0))
        )

        bet = max(
            0.0,
            float(state.get("bet", 0))
        )

        bet_score = 1.0 - (
            bet / max_bet
        )

        bet_score = max(
            0.0,
            min(
                1.0,
                bet_score
            )
        )

        player_score = (
            players / max_players
        )

        player_score = max(
            0.0,
            min(
                1.0,
                player_score
            )
        )

        hits100 = history100.count(room)

        if history100:
            kill_safety100 = 1.0 - (
                hits100 / len(history100)
            )
        else:
            kill_safety100 = 0.5

        kill_safety100 = max(
            0.0,
            min(
                1.0,
                kill_safety100
            )
        )

        hits10 = history10.count(room)

        if history10:
            kill_safety10 = 1.0 - (
                hits10 / len(history10)
            )
        else:
            kill_safety10 = 0.5

        kill_safety10 = max(
            0.0,
            min(
                1.0,
                kill_safety10
            )
        )

        current_gap = len(history100)

        for i in range(
            len(history100) - 1,
            -1,
            -1
        ):
            if history100[i] == room:
                current_gap = (
                    len(history100) - 1 - i
                )
                break

        current_gaps[room] = current_gap

        if history100:
            delay_score = min(
                current_gap / len(history100),
                1.0
            )
        else:
            delay_score = 0.5

        delay_score = max(
            0.0,
            min(
                1.0,
                delay_score
            )
        )

        score = (
            bet_score * 0.55 +
            player_score * 0.05 +
            kill_safety100 * 0.15 +
            kill_safety10 * 0.10 +
            delay_score * 0.15
        )

        if hits10 == 0 and len(history10) >= 5:
            score += 0.05

        if hits100 <= 2 and len(history100) >= 30:
            score += 0.04

        if (
            current_gap >= 10
            and
            len(history100) >= 20
        ):
            score += 0.04

        if (
            current_gap >= 20
            and
            len(history100) >= 30
        ):
            score += 0.03

        scores[room] = score

    available_rooms = [
        room
        for room in ROOM_ORDER
        if room != last_killed_room
    ]

    if not available_rooms:
        available_rooms = list(ROOM_ORDER)

    best_score = max(
        scores.get(
            room,
            float("-inf")
        )
        for room in available_rooms
    )

    candidates = [
        room
        for room in available_rooms
        if scores.get(
            room,
            float("-inf")
        ) >= best_score - 0.02
    ]

    if not candidates:
        candidates = available_rooms

    candidates.sort(
        key=lambda room: (
            -scores.get(
                room,
                float("-inf")
            ),
            current_gaps.get(
                room,
                0
            ),
            -history100.count(room),
            -history10.count(room),
            room_state.get(
                room,
                {}
            ).get(
                "bet",
                float("inf")
            )
        )
    )

    return candidates[0]

# Logic 9: Né Sát Thủ Thông Minh
def choose_smart_safe():
    scores = {}

    max_players = max(room_state[r]["players"] for r in ROOM_ORDER) or 1
    max_bet = max(room_state[r]["bet"] for r in ROOM_ORDER) or 1

    for r in ROOM_ORDER:
        kills = room_stats[r]["kills"]
        survives = room_stats[r]["survives"]

        total = kills + survives
        survival = survives / total if total > 0 else 0.5

        player_score = 1 - room_state[r]["players"] / max_players
        bet_score = 1 - room_state[r]["bet"] / max_bet

        score = (
            survival * 0.50 +
            player_score * 0.30 +
            bet_score * 0.20
        )

        if r == last_killed_room:
            score -= 0.35

        scores[r] = score

    return max(scores, key=scores.get)

# Logic 10: Theo Vết Sát Thủ
def choose_follow_killer_delayed():
    global last_killed_room_delayed
    if last_killed_room_delayed is not None and last_killed_room_delayed in ROOM_ORDER:
        chosen = last_killed_room_delayed

        return chosen
    return random.choice(ROOM_ORDER)

# Logic 11: Bậc Thầy Trốn Tìm
def choose_hide_seek_master():
    danger_scores = {}
    max_players = max(rs['players'] for rs in room_state.values()) or 1
    max_bet = max(rs['bet'] for rs in room_state.values()) or 1
    avg_players_killed = 0
    avg_bet_killed = 0
    if killer_history:
        avg_players_killed = sum(h['players'] for h in killer_history) / len(killer_history)
        avg_bet_killed = sum(h['bet'] for h in killer_history) / len(killer_history)
    for r in ROOM_ORDER:
        kills = room_stats[r].get('kills', 0)
        survives = room_stats[r].get('survives', 0)
        hist_danger = (kills + 1) / (kills + survives + 2)
        crowd_danger = room_state[r]['players'] / max_players
        money_danger = room_state[r]['bet'] / max_bet
        personality_danger = 0
        if killer_history:
            player_sim = 1 - (abs(room_state[r]['players'] - avg_players_killed) / (avg_players_killed + max_players + 1))
            bet_sim = 1 - (abs(room_state[r]['bet'] - avg_bet_killed) / (avg_bet_killed + max_bet + 1))
            personality_danger = (player_sim + bet_sim) / 2
        recency_penalty = 1.0 if r == last_killed_room else 0.0
        total_danger = (0.3 * hist_danger) + (0.2 * crowd_danger) + (0.2 * money_danger) + (0.3 * personality_danger) + recency_penalty
        danger_scores[r] = total_danger
    return min(danger_scores, key=danger_scores.get)
    
#Logic 12: Nhiều Người Ít Cược
def choose_many_player_low_bet():

    best_room = ROOM_ORDER[0]
    best_score = -1

    max_players = max(room_state[r]["players"] for r in ROOM_ORDER) or 1
    max_bet = max(room_state[r]["bet"] for r in ROOM_ORDER) or 1

    for room in ROOM_ORDER:
        players = room_state[room]["players"]
        bet = room_state[room]["bet"]
        player_score = players / max_players
        bet_score = 1 - (bet / max_bet)
        score = player_score * 0.7 + bet_score * 0.3
        
        if score > best_score:
            best_score = score
            best_room = room

    return best_room
    
# Logic 13: Né Rủi Ro
def choose_hot_safe_room(window: int = 12):
    if not ROOM_ORDER:
        return 1

    if len(ROOM_ORDER) == 1:
        return ROOM_ORDER[0]

    history = list(game_kill_log)

    if len(history) < 6:
        try:
            fallback = choose_min_player_bet()

            if (
                fallback in ROOM_ORDER
                and fallback != last_killed_room
            ):
                return fallback
        except Exception:
            pass

        candidates = [
            room
            for room in ROOM_ORDER
            if room != last_killed_room
        ]

        if candidates:
            return candidates[0]

        return ROOM_ORDER[0]

    rooms = list(ROOM_ORDER)

    history100 = history[-100:]
    history10 = history100[-10:]

    recent = history[-max(5, window):]
    short = history[-5:]
    medium = history[-12:]
    long = history[-25:]

    previous_room = (
        recent[-1]
        if recent
        else None
    )

    max_players = max(
        1.0,
        float(_room_max("players"))
    )

    max_bet = max(
        1.0,
        float(_room_max("bet"))
    )

    scores = {}

    for room in rooms:
        if room == last_killed_room:
            continue

        state = _safe_room_state(room)

        players = float(
            state.get("players", 0) or 0
        )

        bet = float(
            state.get("bet", 0) or 0
        )

        total_weight = 0.0
        hit_weight = 0.0

        n = len(short)

        for i, value in enumerate(short):
            age = n - 1 - i
            weight = 0.80 ** age

            total_weight += weight

            if value == room:
                hit_weight += weight

        if total_weight > 0:
            short_hot = (
                hit_weight /
                total_weight
            )
        else:
            short_hot = 0.0

        total_weight = 0.0
        hit_weight = 0.0

        n = len(medium)

        for i, value in enumerate(medium):
            age = n - 1 - i
            weight = 0.90 ** age

            total_weight += weight

            if value == room:
                hit_weight += weight

        if total_weight > 0:
            medium_hot = (
                hit_weight /
                total_weight
            )
        else:
            medium_hot = 0.0

        total_weight = 0.0
        hit_weight = 0.0

        n = len(long)

        for i, value in enumerate(long):
            age = n - 1 - i
            weight = 0.97 ** age

            total_weight += weight

            if value == room:
                hit_weight += weight

        if total_weight > 0:
            long_hot = (
                hit_weight /
                total_weight
            )
        else:
            long_hot = 0.0

        transition_total = 0
        transition_hits = 0

        for i in range(
            1,
            len(recent)
        ):
            if recent[i - 1] == previous_room:
                transition_total += 1

                if recent[i] == room:
                    transition_hits += 1

        if transition_total > 0:
            transition_danger = (
                transition_hits /
                transition_total
            )
        else:
            transition_danger = 0.0

        repeat_total = 0
        repeat_hits = 0

        for i in range(
            1,
            len(recent)
        ):
            if recent[i - 1] == room:
                repeat_total += 1

                if recent[i] == room:
                    repeat_hits += 1

        if repeat_total > 0:
            repeat_danger = (
                repeat_hits /
                repeat_total
            )
        else:
            repeat_danger = 0.0

        delay = len(history100)

        for i in range(
            len(history100) - 1,
            -1,
            -1
        ):
            if history100[i] == room:
                delay = (
                    len(history100) -
                    1 -
                    i
                )
                break

        if history100:
            delay_score = min(
                delay /
                len(history100),
                1.0
            )
        else:
            delay_score = 0.5

        longest_gap = 0
        current_gap = 0

        for killed_room in history100:
            if killed_room == room:
                if current_gap > longest_gap:
                    longest_gap = current_gap

                current_gap = 0
            else:
                current_gap += 1

        if current_gap > longest_gap:
            longest_gap = current_gap

        if history100:
            longest_gap_score = min(
                longest_gap /
                len(history100),
                1.0
            )
        else:
            longest_gap_score = 0.5

        hits100 = history100.count(room)

        if history100:
            kill_safety100 = (
                1.0 -
                hits100 /
                len(history100)
            )
        else:
            kill_safety100 = 0.5

        hits10 = history10.count(room)

        if history10:
            kill_safety10 = (
                1.0 -
                hits10 /
                len(history10)
            )
        else:
            kill_safety10 = 0.5

        player_safety = max(
            0.0,
            min(
                1.0,
                1.0 -
                players /
                max_players
            )
        )

        bet_safety = max(
            0.0,
            min(
                1.0,
                1.0 -
                bet /
                max_bet
            )
        )

        try:
            survival = float(
                _survival_rate(room)
            )
        except Exception:
            survival = 0.5

        survival = max(
            0.0,
            min(
                1.0,
                survival
            )
        )

        history_safety = (
            (1.0 - short_hot) * 0.25 +
            (1.0 - medium_hot) * 0.20 +
            (1.0 - long_hot) * 0.15 +
            (1.0 - transition_danger) * 0.10 +
            (1.0 - repeat_danger) * 0.05 +
            delay_score * 0.15 +
            longest_gap_score * 0.10
        )

        score = (
            history_safety * 0.35 +
            survival * 0.25 +
            bet_safety * 0.10 +
            player_safety * 0.05 +
            kill_safety100 * 0.10 +
            kill_safety10 * 0.15
        )

        if hits10 == 0 and len(history10) >= 5:
            score += 0.05

        if hits100 <= 2 and len(history100) >= 30:
            score += 0.04

        if delay >= 10 and len(history100) >= 20:
            score += 0.05

        if delay >= 20 and len(history100) >= 30:
            score += 0.04

        if longest_gap >= 15 and len(history100) >= 30:
            score += 0.03

        recent3_hits = recent[-3:].count(room)

        if recent3_hits >= 2:
            score -= 0.12

        if recent3_hits >= 3:
            score -= 0.15

        consecutive = 0

        for killed_room in reversed(recent):
            if killed_room == room:
                consecutive += 1
            else:
                break

        if consecutive >= 2:
            score -= min(
                consecutive * 0.10,
                0.30
            )

        scores[room] = score

    available_rooms = [
        room
        for room in rooms
        if room != last_killed_room
        and room in scores
    ]

    if not available_rooms:
        available_rooms = [
            room
            for room in rooms
            if room != last_killed_room
        ]

    if not available_rooms:
        return ROOM_ORDER[0]

    best_score = max(
        scores.get(
            room,
            -999999.0
        )
        for room in available_rooms
    )

    candidates = [
        room
        for room in available_rooms
        if scores.get(
            room,
            -999999.0
        ) >= best_score - 0.015
    ]

    if not candidates:
        return max(
            available_rooms,
            key=lambda room: scores.get(
                room,
                -999999.0
            )
        )

    candidates.sort(
        key=lambda room: (
            scores.get(
                room,
                -999999.0
            ),
            survival
            if room in scores
            else 0.5,
            (
                len(history100) -
                next(
                    (
                        len(history100) -
                        1 -
                        i
                        for i in range(
                            len(history100) - 1,
                            -1,
                            -1
                        )
                        if history100[i] == room
                    ),
                    len(history100)
                )
            ),
            -history100.count(room),
            -history10.count(room),
            -_safe_room_state(room).get(
                "players",
                0
            ),
            -_safe_room_state(room).get(
                "bet",
                0
            )
        ),
        reverse=True
    )

    return candidates[0]

def _safe_room_state(room: int) -> Dict[str, float]:
    """Đọc trạng thái phòng an toàn, luôn trả về số hợp lệ."""
    state = room_state.get(room) or {}
    try:
        players = _parse_number(state.get("players", 0))
    except Exception:
        players = None
    try:
        bet = _parse_number(state.get("bet", 0))
    except Exception:
        bet = None
    return {
        "players": max(0.0, float(players or 0.0)),
        "bet": max(0.0, float(bet or 0.0)),
    }


def _room_max(field: str) -> float:
    values = []
    for r in ROOM_ORDER:
        state = _safe_room_state(r)
        values.append(state[field])
    return max(values, default=0.0)


def _survival_rate(room: int) -> float:
    stats = room_stats.get(room) or {}
    kills = float(stats.get("kills", 0) or 0)
    survives = float(stats.get("survives", 0) or 0)
    total = kills + survives
    return ((survives + 1.0) / (total + 2.0)) if total > 0 else 0.5


# Logic 14: Hoá Thần (VIP)
def choose_hoa_than():
    if not ROOM_ORDER:
        return choose_random()

    if len(ROOM_ORDER) == 1:
        return choose_random()

    if len(killer_history) < 5:
        return choose_random()

    history = list(game_kill_log)
    recent5 = history[-5:]
    scores = {}

    if len(history) < 5:
        return choose_random()

    for r in ROOM_ORDER:
        stats = room_stats.get(r) or {}

        try:
            kills = float(stats.get("kills", 0) or 0)
        except Exception:
            kills = 0.0

        try:
            survives = float(stats.get("survives", 0) or 0)
        except Exception:
            survives = 0.0

        total = kills + survives

        if total <= 0:
            continue

        survival_rate = (survives + 1.0) / (total + 2.0)

        kill_score = 1.0 / (1.0 + kills)

        delay = len(history)

        for i in range(len(history) - 1, -1, -1):
            if history[i] == r:
                delay = len(history) - 1 - i
                break

        delay_score = min(
            delay / max(1, len(history)),
            1.0
        )

        recent_hits = recent5.count(r)

        score = 0.0

        score += survival_rate * 8.0

        score += kill_score * 2.5

        score += delay_score * 2.5

        score += (1.0 - recent_hits / 5.0) * 1.5

        if r == last_killed_room:
            score -= 7.0

        consecutive = 0

        for value in reversed(history[-20:]):
            if value == r:
                consecutive += 1
            else:
                break

        score -= min(consecutive * 1.0, 3.0)

        if survival_rate < 0.40:
            score -= 4.0
        elif survival_rate < 0.50:
            score -= 2.0
        elif survival_rate >= 0.80:
            score += 3.0
        elif survival_rate >= 0.70:
            score += 1.5

        scores[r] = score

    if not scores:
        return choose_random()

    best_score = max(scores.values())

    candidates = [
        r for r in ROOM_ORDER
        if r in scores and abs(scores[r] - best_score) < 1e-9
    ]

    if not candidates:
        return choose_random()

    if len(candidates) > 1:
        candidates.sort(
            key=lambda r: (
                -(
                    (float((room_stats.get(r) or {}).get("survives", 0) or 0) + 1.0)
                    /
                    (
                        float((room_stats.get(r) or {}).get("survives", 0) or 0)
                        +
                        float((room_stats.get(r) or {}).get("kills", 0) or 0)
                        +
                        2.0
                    )
                ),
                float((room_stats.get(r) or {}).get("kills", 0) or 0)
            )
        )

    return candidates[0]

# Logic 15: Bắt Sóng Sát Thủ (VIP)
def choose_killer_wave():
    if not ROOM_ORDER:
        return 1
    if len(killer_history) < 3:
        return choose_random()

    recent_kills = list(game_kill_log)[-5:]
    max_players = max(1.0, _room_max("players"))
    max_bet = max(1.0, _room_max("bet"))
    scores = {}

    for r in ROOM_ORDER:
        state = _safe_room_state(r)
        recent_hits = recent_kills.count(r)
        score = _survival_rate(r) * 0.50
        score += (1.0 - recent_hits / max(1, len(recent_kills))) * 0.20
        score += (1.0 - state["players"] / max_players) * 0.15
        score += (1.0 - state["bet"] / max_bet) * 0.15
        if r == last_killed_room:
            score -= 0.35
        scores[r] = score

    return max(scores, key=scores.get)


# Logic 16: Phân Tích Tâm Lý (VIP)
def choose_psycho_analysis():
    try:
        if not ROOM_ORDER:
            return 1

        history = list(game_kill_log)[-5:]
        if len(history) < 3:
            return choose_random()

        counts = Counter(history)
        max_bet = max((float((room_state.get(r) or {}).get("bet", 0) or 0) for r in ROOM_ORDER), default=1.0) or 1.0
        scores = {}

        for room in ROOM_ORDER:
            state = room_state.get(room) or {}
            stats = room_stats.get(room) or {}

            try:
                bet = max(0.0, float(state.get("bet", 0) or 0))
            except Exception:
                bet = 0.0

            try:
                kills = max(0.0, float(stats.get("kills", 0) or 0))
                survives = max(0.0, float(stats.get("survives", 0) or 0))
            except Exception:
                kills = survives = 0.0

            total = kills + survives
            survival_rate = (survives + 1.0) / (total + 2.0) if total > 0 else 0.5
            frequency = counts.get(room, 0) / max(1, len(history))

            score = 0.0
            score += (1.0 - frequency) * 3.0
            score += survival_rate * 3.0
            score += (1.0 - min(bet / max_bet, 1.0)) * 1.5

            consecutive = 0
            for item in reversed(history):
                if item != room:
                    break
                consecutive += 1

            score -= min(consecutive * 0.25, 1.0)

            if room == last_killed_room:
                score -= 0.50

            scores[room] = score

        best_score = max(scores.values())
        candidates = [r for r, score in scores.items() if abs(score - best_score) < 1e-9]

        return random.choice(candidates) if candidates else max(scores, key=scores.get)

    except Exception:
        return choose_random()

# Logic 17: Phân Tích Chuyên Sâu (VIP)
def choose_deep_analysis():
    if not ROOM_ORDER:
        return 1

    usable = [
        b for b in list(bet_history)[-15:]
        if isinstance(b, dict)
        and b.get("room") in ROOM_ORDER
        and b.get("result") in {"Thắng", "Thua"}
    ]

    if len(usable) < 3:
        return choose_random()

    recent_kills = list(game_kill_log)[-8:]
    max_bet = max(
        1.0,
        max(
            (
                float(
                    (room_state.get(r) or {}).get(
                        "bet",
                        0
                    ) or 0
                )
                for r in ROOM_ORDER
            ),
            default=1.0
        )
    )

    recent_selected = []

    try:
        for item in list(bet_history)[-8:]:
            if isinstance(item, dict):
                room = item.get("room")
                if room in ROOM_ORDER:
                    recent_selected.append(room)
    except Exception:
        recent_selected = []

    scores = {}

    for r in ROOM_ORDER:
        state = room_state.get(r) or {}
        stats = room_stats.get(r) or {}

        try:
            bet = max(
                0.0,
                float(
                    state.get(
                        "bet",
                        0
                    ) or 0
                )
            )
        except Exception:
            bet = 0.0

        try:
            kills = max(
                0.0,
                float(
                    stats.get(
                        "kills",
                        0
                    ) or 0
                )
            )
        except Exception:
            kills = 0.0

        try:
            survives = max(
                0.0,
                float(
                    stats.get(
                        "survives",
                        0
                    ) or 0
                )
            )
        except Exception:
            survives = 0.0

        score = 0.0

        survival = (
            (survives + 1.0) /
            (kills + survives + 2.0)
            if kills + survives > 0
            else 0.5
        )

        survival = max(
            0.0,
            min(
                1.0,
                survival
            )
        )

        for i, b in enumerate(usable):
            if b["room"] == r:
                recency_weight = (
                    0.65 +
                    0.70 * (
                        (i + 1) /
                        len(usable)
                    )
                )

                if b["result"] == "Thắng":
                    score += recency_weight
                else:
                    score -= recency_weight

        score += survival * 1.60

        bet_safety = (
            1.0 -
            min(
                bet / max_bet,
                1.0
            )
        )

        score += bet_safety * 0.35

        score -= recent_kills.count(r) * 0.55

        if r == last_killed_room:
            score -= 0.75

        if recent_selected:
            repeat_count = recent_selected.count(r)
            score -= min(
                repeat_count * 0.10,
                0.40
            )

            if recent_selected[-1] == r:
                score -= 0.20

            if (
                len(recent_selected) >= 2
                and recent_selected[-1] == r
                and recent_selected[-2] == r
            ):
                score -= 0.20

        scores[r] = score

    if not scores:
        return choose_random()

    best_score = max(scores.values())

    candidates = [
        r for r, score in scores.items()
        if score >= best_score - 0.05
    ]

    if not candidates:
        return choose_random()

    if len(candidates) > 1:
        candidates.sort(
            key=lambda r: (
                recent_selected.count(r),
                r == recent_selected[-1]
                if recent_selected
                else False,
                -(
                    (
                        float(
                            (room_stats.get(r) or {}).get(
                                "survives",
                                0
                            ) or 0
                        ) + 1.0
                    )
                    /
                    (
                        float(
                            (room_stats.get(r) or {}).get(
                                "kills",
                                0
                            ) or 0
                        )
                        +
                        float(
                            (room_stats.get(r) or {}).get(
                                "survives",
                                0
                            ) or 0
                        )
                        + 2.0
                    )
                ),
                float(
                    (room_state.get(r) or {}).get(
                        "bet",
                        0
                    ) or 0
                )
            )
        )

    return candidates[0]


# Logic 18: Siêu Phân Tích V1 (VIP)
def choose_markov_chain():
    if not ROOM_ORDER:
        return 1

    # Dùng chuỗi kết quả sát thủ thực tế để lấy xác suất chuyển trạng thái.
    history = [r for r in list(game_kill_log) if r in ROOM_ORDER][-20:]
    if len(history) < 4:
        return choose_random()

    transition = {r: Counter() for r in ROOM_ORDER}
    for a, b in zip(history, history[1:]):
        transition[a][b] += 1

    last = history[-1]
    total_from_last = sum(transition[last].values())
    max_players = max(1.0, _room_max("players"))
    max_bet = max(1.0, _room_max("bet"))
    recent = history[-8:]
    scores = {}

    for r in ROOM_ORDER:
        # Xác suất bị sát thủ chuyển từ phòng vừa nổ sang r.
        p_transition = (transition[last].get(r, 0) / total_from_last) if total_from_last else 0.0
        state = _safe_room_state(r)
        stats = room_stats.get(r) or {}
        kills = float(stats.get("kills", 0) or 0)
        survives = float(stats.get("survives", 0) or 0)
        recent_kill_rate = recent.count(r) / max(1, len(recent))

        score = (
            1.80 * _survival_rate(r)
            - 1.20 * p_transition
            + 0.65 * (1.0 - state["players"] / max_players)
            + 0.55 * (1.0 - state["bet"] / max_bet)
            - 1.10 * recent_kill_rate
            - 0.35 * kills / max(1.0, kills + survives)
        )
        if r == last_killed_room:
            score -= 0.90
        scores[r] = score

    return max(scores, key=scores.get)


# Logic 19: Thần Thánh AI (VIP)
def choose_god_mode():
    if not ROOM_ORDER:
        return 1
    if len(game_kill_log) < 3:
        return choose_random()

    recent = list(game_kill_log)[-10:]
    total = len(recent)
    max_players = max(1.0, _room_max("players"))
    max_bet = max(1.0, _room_max("bet"))
    scores = {}

    for room in ROOM_ORDER:
        hits = recent.count(room)
        frequency = hits / max(1, total)
        state = _safe_room_state(room)
        score = 0.0
        
        score += (1.0 - frequency) * 0.45
        score += _survival_rate(room) * 0.30
        score += (1.0 - state["players"] / max_players) * 0.15
        score += (1.0 - state["bet"] / max_bet) * 0.10
        if room == last_killed_room:
            score -= 0.35
        scores[room] = score

    return max(scores, key=scores.get)


# Logic 20: Thợ Săn (VIP)
def choose_hunter():
    if not ROOM_ORDER:
        return choose_random()

    if len(ROOM_ORDER) == 1:
        return choose_random()

    if len(killer_history) < 3:
        return choose_random()

    recent_rooms = list(game_kill_log)[-20:]
    recent_count = Counter(recent_rooms)
    max_bet = max(1.0, _room_max("bet"))
    scores = {}

    for room in ROOM_ORDER:
        state = _safe_room_state(room)
        score = 0.0

        # Nhiều người hay ít người đều được
        # Không xét số người

        # Ít cược
        score += (1.0 - state["bet"] / max_bet) * 2.5

        # Tỷ lệ sống
        score += _survival_rate(room) * 3.0

        # Ít bị giết gần đây
        score -= min(recent_count.get(room, 0) * 0.8, 3.0)

        # Né phòng vừa bị giết
        if room == last_killed_room:
            score -= 3.0

        # Lâu chưa bị giết
        delay = 0
        for item in reversed(recent_rooms):
            if item == room:
                break
            delay += 1

        score += min(delay * 0.15, 2.0)

        # Né phòng bị giết liên tiếp
        consecutive = 0
        for item in reversed(recent_rooms):
            if item != room:
                break
            consecutive += 1

        if consecutive >= 2:
            score -= min(consecutive * 0.7, 2.5)

        scores[room] = score

    if not scores:
        return choose_random()

    best_room = max(scores, key=scores.get)

    # Chống tự tin quá lâu:
    # Nếu cùng một phòng xuất hiện quá nhiều lần gần đây
    # thì chuyển sang phòng khác có điểm cao tiếp theo.
    recent_selected = list(game_kill_log)[-5:]

    if recent_selected.count(best_room) >= 3:
        other_rooms = [
            room for room in ROOM_ORDER
            if room != best_room
        ]

        if other_rooms:
            return max(
                other_rooms,
                key=lambda room: scores.get(room, float("-inf"))
            )

    return best_room

# Logic 21: Siêu Phân Tích V2
def choose_super_analysis_v2():
    if not ROOM_ORDER:
        return choose_random()

    if len(ROOM_ORDER) == 1:
        return choose_random()

    if len(killer_history) < 5:
        return choose_random()

    full_kill_history = list(game_kill_log)
    history100 = full_kill_history[-100:]
    history10 = history100[-10:]

    if len(history100) < 5:
        return choose_random()


    recent_selected = []

    try:
        for item in list(bet_history)[-10:]:
            if isinstance(item, dict):
                room = item.get("room")
                if room in ROOM_ORDER:
                    recent_selected.append(room)
    except Exception:
        recent_selected = []

    scores = {}
    survivals = {}
    kill_rates100 = {}
    current_gaps = {}
    longest_gaps = {}


    max_bet = 1.0

    for room in ROOM_ORDER:
        state = room_state.get(room) or {}

        try:
            bet = float(state.get("bet", 0) or 0)
        except Exception:
            bet = 0.0

        if bet > max_bet:
            max_bet = bet

    for room in ROOM_ORDER:
        state = room_state.get(room) or {}

        try:
            bet = max(0.0, float(state.get("bet", 0) or 0))
        except Exception:
            bet = 0.0

        stats = room_stats.get(room) or {}

        try:
            kills = max(0.0, float(stats.get("kills", 0) or 0))
        except Exception:
            kills = 0.0

        try:
            survives = max(0.0, float(stats.get("survives", 0) or 0))
        except Exception:
            survives = 0.0

        total = kills + survives

        if total > 0:
            survival = (survives + 1.0) / (total + 2.0)
        else:
            survival = 0.5

        survival = max(0.0, min(1.0, survival))
        survivals[room] = survival

        survival_score = survival * 0.35


        bet_safety = 1.0 - (bet / max_bet)
        bet_safety = max(0.0, min(1.0, bet_safety))

        bet_score = bet_safety * 0.08

        hits100 = history100.count(room)

        kill_rates100[room] = (
            hits100 / len(history100)
            if history100
            else 0.0
        )

        kill_safety100 = 1.0 - kill_rates100[room]
        kill_safety100 = max(
            0.0,
            min(1.0, kill_safety100)
        )

        history100_score = kill_safety100 * 0.15

        hits10 = history10.count(room)

        if history10:
            kill_safety10 = 1.0 - (
                hits10 / len(history10)
            )
        else:
            kill_safety10 = 0.5

        kill_safety10 = max(
            0.0,
            min(1.0, kill_safety10)
        )

        history10_score = kill_safety10 * 0.10

        current_gap = 0

        if history100:
            current_gap = len(history100)

            for i in range(
                len(history100) - 1,
                -1,
                -1
            ):
                if history100[i] == room:
                    current_gap = (
                        len(history100) - 1 - i
                    )
                    break

        current_gaps[room] = current_gap

        gap_score = min(
            current_gap / max(1, len(history100)),
            1.0
        )

        delay_score = gap_score * 0.10

        longest_gap = 0
        running_gap = 0

        for killed_room in history100:
            if killed_room == room:
                longest_gap = max(
                    longest_gap,
                    running_gap
                )
                running_gap = 0
            else:
                running_gap += 1

        longest_gap = max(
            longest_gap,
            running_gap
        )

        longest_gaps[room] = longest_gap

        longest_gap_score = min(
            longest_gap / max(1, len(history100)),
            1.0
        )

        long_gap_score = longest_gap_score * 0.07

        repeat_count = recent_selected.count(room)

        if recent_selected:
            repeat_safety = 1.0 - (
                repeat_count /
                len(recent_selected)
            )
        else:
            repeat_safety = 0.5

        repeat_safety = max(
            0.0,
            min(1.0, repeat_safety)
        )

        repeat_score = repeat_safety * 0.05

        consecutive = 0

        for selected_room in reversed(
            recent_selected
        ):
            if selected_room == room:
                consecutive += 1
            else:
                break

        if consecutive >= 2:
            repeat_score -= min(
                consecutive * 0.08,
                0.30
            )


        total_score = (
            survival_score +
            bet_score +
            history100_score +
            history10_score +
            delay_score +
            long_gap_score +
            repeat_score
        )

        if survival >= 0.80:
            total_score += 0.08
        elif survival >= 0.70:
            total_score += 0.04
        elif survival < 0.40:
            total_score -= 0.10
        elif survival < 0.50:
            total_score -= 0.05

        if (
            hits10 == 0
            and len(history10) >= 5
        ):
            total_score += 0.05

        if (
            current_gap >= 10
            and len(history100) >= 20
        ):
            total_score += 0.04

        if (
            current_gap >= 20
            and len(history100) >= 30
        ):
            total_score += 0.03

        if (
            hits100 <= 2
            and len(history100) >= 30
        ):
            total_score += 0.04

        if (
            hits100 <= 4
            and len(history100) >= 50
        ):
            total_score += 0.02

        if room == last_killed_room:
            total_score -= 1.0

        scores[room] = total_score

    available_rooms = [
        room
        for room in ROOM_ORDER
        if room != last_killed_room
    ]

    if not available_rooms:
        available_rooms = list(ROOM_ORDER)

    if len(recent_selected) >= 3:
        selected_counts = Counter(
            recent_selected[-5:]
        )

        blocked_rooms = {
            room
            for room, count in selected_counts.items()
            if count >= 3
        }

        filtered_rooms = [
            room
            for room in available_rooms
            if room not in blocked_rooms
        ]

        if filtered_rooms:
            available_rooms = filtered_rooms

    if len(recent_selected) >= 2:
        if (
            recent_selected[-1]
            == recent_selected[-2]
        ):
            blocked_room = recent_selected[-1]

            filtered_rooms = [
                room
                for room in available_rooms
                if room != blocked_room
            ]

            if filtered_rooms:
                available_rooms = filtered_rooms

    if not available_rooms:
        available_rooms = list(ROOM_ORDER)

    best_score = max(
        scores.get(
            room,
            float("-inf")
        )
        for room in available_rooms
    )

    candidates = [
        room
        for room in available_rooms
        if scores.get(
            room,
            float("-inf")
        ) >= best_score - 0.03
    ]

    if not candidates:
        return max(
            available_rooms,
            key=lambda room: scores.get(
                room,
                float("-inf")
            )
        )
        
    candidates.sort(
        key=lambda room: (
            survivals.get(room, 0.5),
            -kill_rates100.get(room, 0.0),
            current_gaps.get(room, 0),
            longest_gaps.get(room, 0),
            -recent_selected.count(room)
        ),
        reverse=True
    )

    return candidates[0]


# Logic 22: Tối Thượng (VIP)
def choose_infinity():
    if not ROOM_ORDER:
        return 1

    if len(game_kill_log) < 5:
        return choose_min_player_bet()

    recent = list(game_kill_log)[-30:]
    n = len(recent)
    max_players = max(1.0, max((float((room_state.get(r) or {}).get("players", 0) or 0) for r in ROOM_ORDER), default=1.0))
    max_bet = max(1.0, max((float((room_state.get(r) or {}).get("bet", 0) or 0) for r in ROOM_ORDER), default=1.0))
    scores = {}

    for room in ROOM_ORDER:
        state = room_state.get(room) or {}
        stats = room_stats.get(room) or {}
        players = max(0.0, float(state.get("players", 0) or 0))
        bet = max(0.0, float(state.get("bet", 0) or 0))
        kills = max(0.0, float(stats.get("kills", 0) or 0))
        survives = max(0.0, float(stats.get("survives", 0) or 0))
        total = kills + survives
        survival = (survives + 1.0) / (total + 2.0) if total > 0 else 0.5
        survival = max(0.0, min(1.0, survival))

        weighted_hits = 0.0
        weighted_total = 0.0

        for i, killed_room in enumerate(recent):
            weight = 0.85 ** (n - 1 - i)
            weighted_total += weight
            if killed_room == room:
                weighted_hits += weight

        recent_kill_rate = weighted_hits / weighted_total if weighted_total > 0 else 0.0
        recent_safety = 1.0 - recent_kill_rate
        last5 = recent[-5:]
        hot5 = last5.count(room) / max(1, len(last5))
        cold5 = 1.0 - hot5

        delay = n
        for index in range(n - 1, -1, -1):
            if recent[index] == room:
                delay = n - 1 - index
                break

        delay_score = min(delay / max(1, n), 1.0)

        player_ratio = min(players / max_players, 1.0)
        player_score = 1.0 - abs(player_ratio - 0.5) * 0.20

        bet_safety = 1.0 - min(bet / max_bet, 1.0)
        last_kill_penalty = 0.35 if room == last_killed_room else 0.0

        consecutive = 0
        for killed_room in reversed(recent):
            if killed_room == room:
                consecutive += 1
            else:
                break

        consecutive_penalty = min(consecutive * 0.12, 0.30)
        recent3_hits = recent[-3:].count(room)
        burst_penalty = min(recent3_hits * 0.10, 0.25)

        score = (
            survival * 0.32 +
            recent_safety * 0.25 +
            cold5 * 0.14 +
            delay_score * 0.10 +
            player_score * 0.10 +
            bet_safety * 0.09
        )

        score -= last_kill_penalty + consecutive_penalty + burst_penalty
        scores[room] = score

    best_score = max(scores.values())
    candidates = [room for room, score in scores.items() if score >= best_score - 0.02]

    if len(candidates) > 1:
        random.shuffle(candidates)
        return candidates[0]

    return candidates[0]
    
def choose_decision_tree():
    if not ROOM_ORDER: return None
    if len(killer_history) < 5: return random.choice(ROOM_ORDER)

    danger_scores = {}
    max_players = max(rs.get('players', 0) for rs in room_state.values()) or 1
    max_bet = max(rs.get('bet', 0) for rs in room_state.values()) or 1
    avg_players_killed = sum(h.get('players', 0) for h in killer_history) / len(killer_history)
    avg_bet_killed = sum(h.get('bet', 0) for h in killer_history) / len(killer_history)

    for r in ROOM_ORDER:
        state = room_state.get(r, {})
        stats = room_stats.get(r, {})
        kills = stats.get('kills', 0)
        survives = stats.get('survives', 0)
        players = state.get('players', 0)
        bet = state.get('bet', 0)
        hist_danger = (kills + 1) / (kills + survives + 2)
        crowd_danger = players / max_players
        money_danger = bet / max_bet
        player_sim = 1 - abs(players - avg_players_killed) / (avg_players_killed + max_players + 1)
        bet_sim = 1 - abs(bet - avg_bet_killed) / (avg_bet_killed + max_bet + 1)
        personality_danger = (player_sim + bet_sim) / 2
        recency_penalty = 1.0 if r == last_killed_room else 0.0
        danger_scores[r] = 0.3 * hist_danger + 0.2 * crowd_danger + 0.2 * money_danger + 0.3 * personality_danger + recency_penalty

    return min(danger_scores, key=danger_scores.get)
    
def choose_van_bao():
    if not ROOM_ORDER:
        return 1

    WEIGHT_BET = 0.30
    WEIGHT_SURVIVAL = 0.30
    WEIGHT_PLAYERS = 0.15
    WEIGHT_RECENT_KILL = 0.15
    WEIGHT_REPEAT = 0.10

    room_data = {}
    max_bet = 0.0
    max_players = 0.0

    for room in ROOM_ORDER:
        state = _safe_room_state(room)
        bet = max(0.0, float(state.get("bet", 0.0)))
        players = max(0.0, float(state.get("players", 0.0)))
        room_data[room] = {"bet": bet, "players": players}
        max_bet = max(max_bet, bet)
        max_players = max(max_players, players)

    max_bet = max(max_bet, 1.0)
    max_players = max(max_players, 1.0)

    recent_kills = [r for r in list(game_kill_log)[-10:] if r in ROOM_ORDER]
    recent_total = max(1, len(recent_kills))
    recent_selected = []

    try:
        for item in list(bet_history)[-10:]:
            if isinstance(item, dict) and item.get("room") in ROOM_ORDER:
                recent_selected.append(item.get("room"))
    except Exception:
        recent_selected = []

    consecutive_selected = {}

    for room in ROOM_ORDER:
        count = 0
        for selected_room in reversed(recent_selected):
            if selected_room == room:
                count += 1
            else:
                break
        consecutive_selected[room] = count

    scores = {}

    for room in ROOM_ORDER:
        bet = room_data[room]["bet"]
        players = room_data[room]["players"]
        bet_ratio = min(bet / max_bet, 1.0)

        bet_score = max(0.0, min(1.0, 1.0 - bet_ratio ** 1.35))
        if bet_ratio >= 0.85:
            bet_score -= 0.20
        if bet_ratio >= 0.95:
            bet_score -= 0.30
        bet_score = max(0.0, min(1.0, bet_score))

        survival_score = _survival_rate(room)

        player_ratio = players / max_players
        player_score = 1.0 - abs(player_ratio - 0.5) * 0.5

        recent_kill_count = recent_kills.count(room)
        recent_kill_score = 1.0 - recent_kill_count / recent_total

        if recent_kill_count >= 3:
            recent_kill_score -= 0.15
        if recent_kill_count >= 4:
            recent_kill_score -= 0.20

        recent_kill_score = max(0.0, min(1.0, recent_kill_score))

        repeat_count = consecutive_selected.get(room, 0)
        repeat_score = 1.0 if repeat_count <= 1 else 0.75 if repeat_count == 2 else 0.45 if repeat_count == 3 else 0.15 if repeat_count == 4 else 0.0

        score = (
            bet_score * WEIGHT_BET +
            survival_score * WEIGHT_SURVIVAL +
            player_score * WEIGHT_PLAYERS +
            recent_kill_score * WEIGHT_RECENT_KILL +
            repeat_score * WEIGHT_REPEAT
        )

        if room == last_killed_room:
            score -= 0.30
        if room == last_killed_room and recent_kill_count >= 2:
            score -= 0.15
        if bet_ratio >= 0.90:
            score -= 0.20
        if bet_ratio >= 0.97:
            score -= 0.35

        scores[room] = score

    best_score = max(scores.values())
    candidates = [room for room, score in scores.items() if score >= best_score - 0.025]

    if len(candidates) > 1:
        candidates.sort(key=lambda room: (room != last_killed_room, -room_data[room]["bet"], _survival_rate(room), -recent_kills.count(room)), reverse=True)
        return candidates[0]

    return max(scores, key=scores.get)

# Logic 23: Tổng Hợp (VIP)
def choose_tong_hop():
    # 1) Chưa đủ lịch sử -> Random
    # 2) Cho toàn bộ logic VIP cùng bỏ phiếu
    # 3) Chọn phòng có nhiều phiếu nhất
    if not ROOM_ORDER:
        return 1

    if len(killer_history) < 3:
        return choose_random()

    vip_logic_funcs = [
        choose_hoa_than,
        choose_killer_wave,
        choose_psycho_analysis,
        choose_deep_analysis,
        choose_markov_chain,
        choose_god_mode,
        choose_hunter,
        choose_super_analysis_v2,
        choose_infinity,
        choose_decision_tree,
        choose_van_bao,
    ]

    votes = defaultdict(int)

    for func in vip_logic_funcs:
        try:
            room = func()
            if room in ROOM_ORDER:
                votes[room] += 1
        except Exception:
            log_debug(
                f"TONG_HOP: lỗi khi gọi "
                f"{getattr(func, '__name__', 'unknown')}"
            )

    if not votes:
        return choose_random()

    return max(votes, key=votes.get)


def choose_room_tn(mode: str) -> Tuple[int, str]:
    mode = mode.upper()

    logic_map = {
        "RANDOM": choose_random,
        "MIN_PLAYER_BET": choose_min_player_bet,
        "PROBABILITY": choose_probability,
        "FOLLOW_KILLER": choose_follow_killer,
        "MIN_BET": choose_min_bet,
        "SEQUENTIAL": choose_sequential,
        "KILLER_PERSONALITY": choose_killer_personality,
        "ALL": choose_all,
        "SMART_SAFE": choose_smart_safe,
        "FOLLOW_KILLER_DELAYED": choose_follow_killer_delayed,
        "HIDE_SEEK_MASTER": choose_hide_seek_master,
        "MANY_PLAYER_LOW_BET": choose_many_player_low_bet,
        "HOT_SAFE": choose_hot_safe_room,
        "HOA_THAN": choose_hoa_than,
        "KILLER_WAVE": choose_killer_wave,
        "PSYCHO_ANALYSIS": choose_psycho_analysis,
        "DEEP_ANALYSIS": choose_deep_analysis,
        "MARKOV_CHAIN": choose_markov_chain,
        "GOD_MODE": choose_god_mode,
        "HUNTER": choose_hunter,
        "HEAVEN_EYE": choose_super_analysis_v2,
        "INFINITY": choose_infinity,
        "TONG_HOP": choose_tong_hop,
    }

    func = logic_map.get(mode, choose_random)

    try:
        chosen_room = func()

        if chosen_room not in ROOM_ORDER:
            logger.warning(f"{mode} trả về phòng không hợp lệ: {chosen_room}")
            chosen_room = choose_random()

    except Exception:
        log_debug(f"Lỗi thuật toán {mode}")
        chosen_room = choose_random()

    return chosen_room, mode

# ================== API VÀ ĐẶT CƯỢC VTH ==================

def api_headers() -> Dict[str, str]:
    return {"content-type": "application/json", "user-agent": "Mozilla/5.0", "user-id": str(USER_ID) if USER_ID else "", "user-secret-key": SECRET_KEY if SECRET_KEY else ""}

def place_bet_http(issue: int, room_id: int, amount: float) -> dict:
    payload = {"asset_type": "BUILD", "user_id": USER_ID, "room_id": int(room_id), "bet_amount": float(amount)}
    try:
        r = requests.post(BET_API_URL, headers=api_headers(), json=payload, timeout=8)
        try:
            return r.json()
        except Exception:
            return {"raw": r.text, "http_status": r.status_code}
    except Exception as e:
        return {"error": str(e)}

def record_bet(issue: int, room_id: int, amount: float, resp: dict, algo_used: Optional[str] = None) -> dict:
    """Ghi lịch sử bằng đúng snapshot phòng đã chốt cho ván.

    Không lấy lại predicted_room hiện tại vì sau khi sang ván mới biến này
    có thể đã đổi sang phòng khác. Snapshot theo issue giúp tránh tình trạng
    UI hiển thị P6 nhưng lịch sử lại ghi P7.
    """
    try:
        issue = int(issue)
    except (TypeError, ValueError):
        return {}

    if issue in history_recorded_issue:
        return next((r for r in bet_history if r.get("issue") == issue), {})

    snapshot = bet_selection_by_issue.get(issue) or {}
    selected_room = snapshot.get("room", room_id)
    try:
        selected_room = int(selected_room)
    except (TypeError, ValueError):
        selected_room = None

    # Tuyệt đối không ghi ID ngoài P1-P8. Nếu snapshot lỗi thì dùng room_id
    # truyền vào nhưng vẫn validate lại trước khi đưa vào lịch sử.
    if selected_room not in ROOM_ORDER:
        try:
            selected_room = int(room_id)
        except (TypeError, ValueError):
            selected_room = None
    if selected_room not in ROOM_ORDER:
        log_debug(f"Bỏ ghi lịch sử: room không hợp lệ issue={issue}, room={room_id!r}")
        return {}

    if room_id != selected_room:
        log_debug(
            f"ROOM SNAPSHOT mismatch issue={issue}: request_room={room_id!r}, "
            f"selected_room={selected_room}. Dùng selected_room."
        )

    history_recorded_issue.add(issue)
    now = datetime.now(tz).strftime("%H:%M:%S")
    display_algo = algo_used or snapshot.get("algo") or selected_vth_algo or settings.get("algo")
    if display_algo == "RANDOM" and selected_vth_algo and selected_vth_algo != "RANDOM":
        display_algo = selected_vth_algo

    rec = {
        "issue": issue,
        "room": selected_room,
        "amount": float(amount),
        "time": now,
        "resp": resp,
        "result": "Đang",
        "algo": display_algo,
        "delta": 0.0,
        "win_streak": win_streak,
        "lose_streak": lose_streak,
    }
    bet_history.append(rec)
    return rec

def place_bet_async(issue: int, room_id: int, amount: float, algo_used: Optional[str] = None):
    try:
        issue = int(issue)
    except (TypeError, ValueError):
        return

    # Luôn ưu tiên snapshot của đúng ván.
    snapshot_room = (bet_selection_by_issue.get(issue) or {}).get("room")
    if snapshot_room in ROOM_ORDER:
        room_id = int(snapshot_room)
    else:
        try:
            room_id = int(room_id)
        except (TypeError, ValueError):
            return
        if room_id not in ROOM_ORDER:
            log_debug(f"place_bet_async bỏ qua room không hợp lệ issue={issue}: {room_id!r}")
            return

    if issue in bet_sent_for_issue:
        return
    bet_sent_for_issue.add(issue)
    def worker():

        time.sleep(random.uniform(0.05, 0.45))
        res = place_bet_http(issue, room_id, amount)
        rec = record_bet(issue, room_id, amount, res, algo_used=algo_used)
        if isinstance(res, dict) and (res.get("msg") == "ok" or res.get("code") == 0 or res.get("status") in ("ok", 1)):
            bet_sent_for_issue.add(issue)

        else:
            bet_sent_for_issue.discard(issue)
            history_recorded_issue.discard(issue)
            console.print(f"[red]❌ Đặt lỗi v{issue}: {res}[/]")
    threading.Thread(target=worker, daemon=True).start()

def lock_prediction_if_needed(force: bool = False):
    global prediction_locked, predicted_room, ui_state
    global current_bet, _rounds_placed_since_skip
    global skip_next_round_flag, _skip_rounds_remaining
    global stop_flag
    global last_display_bet
    global count_down
    global analysis_ready_ts

    if stop_flag:
        return

    if prediction_locked and not force:
        return

    if issue_id is None:
        return

    if not force and analysis_ready_ts is not None and time.time() < analysis_ready_ts:
        return

    if not force:
        remaining = _vth_get_remaining_seconds()
        # Tự động chốt dự đoán và đặt cược khi countdown còn 10 giây.
        if remaining is not None and remaining > 10:
            return

    mode = settings.get("algo", "RANDOM").upper()
    is_vip = is_vip_activated()

    # KIỂM TRA QUYỀN LOGIC VIP
    if mode in [
        "HOA_THAN",
        "KILLER_WAVE",
        "PSYCHO_ANALYSIS",
        "DEEP_ANALYSIS",
        "MARKOV_CHAIN",
        "GOD_MODE",
        "HUNTER",
        "HEAVEN_EYE",
        "INFINITY",
        "TONG_HOP",
    ]:
        if not is_vip:
            console.print("[red]❌ Thuật toán này chỉ dành cho Key VIP! Chuyển sang RANDOM.[/red]")
            mode = "RANDOM"
            settings["algo"] = "RANDOM"
   
    try:
        chosen, algo_used = choose_room_tn(mode)
        if chosen not in ROOM_ORDER:
            raise ValueError(f"Phòng không hợp lệ: {chosen!r}")
    except Exception as e:
        log_debug(f"Lỗi chọn phòng ({mode}): {e}")
        chosen = choose_random()
        if chosen not in ROOM_ORDER:
            chosen = ROOM_ORDER[0]
        algo_used = "RANDOM"
    predicted_room = int(chosen)
    prediction_locked = True

    # Chốt phòng theo issue ngay tại thời điểm hiển thị mục tiêu.
    # History/API về sau đều phải dùng snapshot này, không dùng predicted_room
    # của ván mới.
    try:
        current_issue = int(issue_id)
        bet_selection_by_issue[current_issue] = {
            "room": int(predicted_room),
            "algo": str(algo_used),
            "created_at": time.time(),
        }
        # Giữ bộ nhớ nhỏ, chỉ giữ snapshot các ván gần nhất.
        if len(bet_selection_by_issue) > 100:
            for old_issue in sorted(bet_selection_by_issue)[:-60]:
                bet_selection_by_issue.pop(old_issue, None)
    except (TypeError, ValueError):
        pass

    if _skip_rounds_remaining > 0:
        console.print(f"[yellow]⏸️ Đang nghỉ {_skip_rounds_remaining} ván theo cấu hình sau khi thua.[/]")
        _skip_rounds_remaining -= 1
        return
    if skip_next_round_flag:
        console.print("[yellow]⏸️ TẠM DỪNG THEO DÕI SÁT THỦ[/]")
        skip_next_round_flag = False
        return
    if run_mode == "AUTO":
        bld = current_build
        if bld is None:
            bld, _, _ = fetch_balances_3games(retries=1, timeout=3)
            if bld is None:
                console.print("[yellow]⚠️ Không lấy được số dư, không thể đặt cược. Sẽ thử lại...[/]")
                prediction_locked = False
                predicted_room = None
                ui_state = "ANALYZING"
                return
        if current_bet is None:
            current_bet = base_bet
        if mode == "ALL":
            bld, _, _ = fetch_balances_3games(retries=1, timeout=3)
            if bld is None:
                console.print("[yellow]⚠️ Không lấy được số dư BUILD.[/]")
                return
            amt = float(bld)
            last_display_bet = amt
        else:
            amt = float(current_bet)
            last_display_bet = amt
        if amt <= 0:
            console.print("[yellow]⚠️ Số tiền đặt không hợp lệ. Bỏ qua.[/]")
            return
        if mode != "ALL" and amt > bld:
            console.print(f"[red]🔥 VỐN KHÔNG ĐỦ ĐỂ GẤP THẾP! Cần {amt:,.2f} nhưng chỉ có {bld:,.2f}. Reset về cược gốc.[/red]")
            current_bet = base_bet
            amt = float(current_bet)
            last_display_bet = amt
            if amt > bld:
                console.print(f"[red]💀 Vốn không đủ để đặt cược gốc ({amt:,.2f}). Dừng tool.[/red]")
                stop_flag = True
                return
                
        place_bet_async(issue_id, predicted_room, amt, algo_used=algo_used)
        ui_state = "PREDICTED"
        _rounds_placed_since_skip += 1

        if (
            bet_rounds_before_skip > 0
            and _rounds_placed_since_skip >= bet_rounds_before_skip
        ):
            skip_next_round_flag = True
            _rounds_placed_since_skip = 0

# ================== WEBSOCKET VTH ==================

def safe_send_enter_game(ws):
    if not ws:
        log_debug("safe_send_enter_game: ws None")
        return
    try:
        payload = {"msg_type": "handle_enter_game", "asset_type": "BUILD", "user_id": USER_ID, "user_secret_key": SECRET_KEY}
        ws.send(json.dumps(payload))
        log_debug("Sent enter_game")
    except Exception as e:
        log_debug(f"safe_send_enter_game err: {e}")

def _extract_issue_id(d: Dict[str, Any]) -> Optional[int]:
    if not isinstance(d, dict):
        return None
    possible = []
    for key in ("issue_id", "issueId", "issue", "id"):
        v = d.get(key)
        if v is not None:
            possible.append(v)
    if isinstance(d.get("data"), dict):
        for key in ("issue_id", "issueId", "issue", "id"):
            v = d["data"].get(key)
            if v is not None:
                possible.append(v)
    for p in possible:
        try:
            return int(p)
        except Exception:
            try:
                return int(str(p))
            except Exception:
                continue
    return None

def on_open(ws):
    _ws["ws"] = ws
    console.print("[green]ĐANG TRUY CẬP DỮ LIỆU GAME[/]")
    safe_send_enter_game(ws)
def on_message(ws, message):
    global issue_id, count_down, killed_room, round_index, ui_state, analysis_start_ts, issue_start_ts, issue_end_ts
    global prediction_locked, predicted_room, last_killed_room, last_killed_room_delayed, last_msg_ts, current_bet
    global win_streak, lose_streak, max_win_streak, max_lose_streak, cumulative_profit, _skip_rounds_remaining, stop_flag

    last_msg_ts = time.time()

    try:
        if isinstance(message, bytes):
            try:
                message = message.decode("utf-8", errors="replace")
            except Exception:
                message = str(message)

        data = None
        try:
            data = json.loads(message)
        except Exception:
            try:
                data = json.loads(message.replace("'", '"'))
            except Exception:
                log_debug(f"on_message non-json: {str(message)[:200]}")
                return

        if isinstance(data, dict) and isinstance(data.get("data"), str):
            try:
                inner = json.loads(data.get("data"))
                merged = dict(data)
                merged.update(inner)
                data = merged
            except Exception:
                pass

        msg_type = str(data.get("msg_type") or data.get("type") or "")
        new_issue = _extract_issue_id(data)

        if msg_type == "notify_enter_game":
            info = data.get("info", {})
            if isinstance(info, dict):
                if info.get("start_time"):
                    st = float(info.get("start_time"))
                    if st > time.time() * 500:
                        st /= 1000.0
                    issue_start_ts = st

                if info.get("end_time"):
                    et = float(info.get("end_time"))
                    if et > time.time() * 500:
                        et /= 1000.0
                    issue_end_ts = et

            if data.get("last_killed_room_id") is not None:
                try:
                    candidate_kill = int(data["last_killed_room_id"])
                except (TypeError, ValueError):
                    candidate_kill = None
                last_killed_room = candidate_kill if candidate_kill in ROOM_ORDER else None

            room_stat = data.get("room_stat", [])
            if isinstance(room_stat, list):
                for rm in room_stat:
                    _process_room_update(rm)

        elif msg_type == "notify_issue_stat" or "issue_stat" in msg_type:
            rooms = data.get("rooms") or []
            if not rooms and isinstance(data.get("data"), dict):
                rooms = data["data"].get("rooms", [])

            for rm in (rooms or []):
                _process_room_update(rm)
                try:
                    rid = int(rm.get("room_id") or rm.get("roomId") or rm.get("id"))
                except Exception:
                    continue

                # _process_room_update đã parse và validate dữ liệu.
                state = room_state.get(rid)
                if state is None:
                    continue
                room_stats[rid]["last_players"] = state.get("players", 0)
                room_stats[rid]["last_bet"] = state.get("bet", 0)

            if new_issue is not None and new_issue != issue_id:
                log_debug(f"New issue: {issue_id} -> {new_issue}")
                issue_id = new_issue
                processed_result_issues.clear()
                history_recorded_issue.clear()

                if data.get("start_time"):
                    st = float(data.get("start_time"))
                    if st > time.time() * 500:
                        st /= 1000.0
                    issue_start_ts = st
                else:
                    issue_start_ts = time.time()

                if data.get("end_time"):
                    et = float(data.get("end_time"))
                    if et > time.time() * 500:
                        et /= 1000.0
                    issue_end_ts = et
                else:
                    issue_end_ts = time.time() + 60

                count_down = 60
                round_index += 1
                killed_room = None
                prediction_locked = False
                predicted_room = None
                ui_state = "ANALYZING"
                analysis_start_ts = time.time()
                analysis_ready_ts = analysis_start_ts + analysis_initial_delay

        elif msg_type == "notify_count_down" or "count_down" in msg_type:
            try:
                new_count = (
                    data.get("count_down")
                    or data.get("countDown")
                    or data.get("count")
                    or data.get("data", {}).get("count_down")
                    or data.get("data", {}).get("countDown")
                )

                if new_count is not None:
                    # Đồng bộ countdown ngay khi server gửi
                    count_down = max(0, int(float(new_count)))
                    last_msg_ts = time.time()

                    # Không để countdown tự trôi giữa các lần update
                    issue_end_ts = None

                    # Khóa dự đoán khi countdown còn 10 giây
                    if count_down <= 10 and not prediction_locked:
                        lock_prediction_if_needed()

            except Exception as e:
                log_debug(f"notify_count_down error: {e}")

        elif msg_type == "notify_result":
            if issue_id in processed_result_issues:
                return

            processed_result_issues.add(issue_id)
            kr = None
            possible_keys = ["killed_room", "killed_room_id", "killedRoom", "killedRoomId", "kill_room"]

            for key in possible_keys:
                if data.get(key) is not None:
                    kr = data.get(key)
                    break

            if kr is None and isinstance(data.get("data"), dict):
                for key in possible_keys:
                    if data["data"].get(key) is not None:
                        kr = data["data"].get(key)
                        break

            if kr is not None:
                try:
                    krid = int(kr)
                except Exception:
                    krid = kr

                if krid not in ROOM_ORDER:
                    log_debug(f"Bỏ qua killed_room_id không hợp lệ: {krid!r}")
                    return

                killed_room = krid
                game_kill_log.append(krid)
                update_killer_history(krid)
                last_killed_room = krid
                last_killed_room_delayed = krid

                for rid in ROOM_ORDER:
                    if rid == krid:
                        room_stats[rid]["kills"] += 1
                        room_stats[rid]["last_kill_round"] = round_index
                    else:
                        room_stats[rid]["survives"] += 1

                balance_before_payout = current_build
                rec = None
                for b in reversed(bet_history):
                    if b.get("issue") == issue_id:
                        rec = b
                        break

                if rec is not None:
                    try:
                        placed_room = int(rec.get("room"))
                        if placed_room != int(killed_room):
                            rec["result"] = "Thắng"
                            current_bet = base_bet
                            win_streak += 1
                            lose_streak = 0
                            if win_streak > max_win_streak:
                                max_win_streak = win_streak
                        else:
                            rec["result"] = "Thua"
                            try:
                                if current_bet is not None:
                                    current_bet *= float(multiplier)
                            except Exception:
                                current_bet = base_bet

                            lose_streak += 1
                            win_streak = 0
                            if lose_streak > max_lose_streak:
                                max_lose_streak = lose_streak

                            if pause_after_losses > 0:
                                _skip_rounds_remaining = pause_after_losses

                        threading.Thread(
                            target=_background_update_balance_after_result,
                            args=(rec, balance_before_payout),
                            daemon=True
                        ).start()

                        rec["win_streak"] = win_streak
                        rec["lose_streak"] = lose_streak

                    except Exception as e:
                        log_debug(f"result handle err: {e}")

            ui_state = "RESULT"

    except Exception as e:
        log_debug(f"on_message err: {e}")

def _stop_for_capital_limit(message: str):
    if stop_flag:
        return
    _shutdown_vth_runtime(message)

def _check_capital_limit_now() -> bool:
    if (
        stop_when_profit_reached
        and profit_target is not None
        and isinstance(current_build, (int, float))
        and current_build >= profit_target
    ):
        _stop_for_capital_limit(
            f"[bold green]🎉 Đã đạt mục tiêu lãi ({current_build:,.2f} BUILD). Tool dừng.[/bold green]"
        )
        return True

    if (
        stop_when_loss_reached
        and stop_loss_target is not None
        and isinstance(current_build, (int, float))
        and current_build <= stop_loss_target
    ):
        _stop_for_capital_limit(
            f"[bold red]💀 Đã chạm cắt lỗ ({current_build:,.2f} BUILD). Tool dừng.[/bold red]"
        )
        return True

    return False

def _background_update_balance_after_result(rec: dict, balance_before: Optional[float]):
    global cumulative_profit
    global current_build, current_usdt, current_world
    global stop_flag

    try:
        time.sleep(2)

        for _ in range(10):
            new_balance, usdt, world = fetch_balances_3games(
                retries=1,
                timeout=5
            )

            if isinstance(new_balance, (int, float)):
                current_build = new_balance
                current_usdt = usdt
                current_world = world

                if _check_capital_limit_now():
                    return
                break

            time.sleep(1)

        if rec and isinstance(current_build, (int, float)):
            if isinstance(balance_before, (int, float)):
                rec["delta"] = current_build - balance_before
                if starting_balance is not None:
                    cumulative_profit = current_build - starting_balance
            else:
                if rec.get("result") == "Thắng":
                    rec["delta"] = float(rec.get("amount", 0)) * 7
                else:
                    rec["delta"] = -float(rec.get("amount", 0))

        if _check_capital_limit_now():
            return

        while not stop_flag:
            new_balance, usdt, world = fetch_balances_3games(
                retries=1,
                timeout=5
            )

            if isinstance(new_balance, (int, float)):
                current_build = new_balance
                current_usdt = usdt
                current_world = world

            if _check_capital_limit_now():
                return

            time.sleep(1)

    except Exception as e:
        log_debug(f"Error in background balance update: {e}")

def update_killer_history(killed_room_id):
    if killed_room_id in room_state:
        killer_history.append({'players': room_state[killed_room_id].get('players', 0), 'bet': room_state[killed_room_id].get('bet', 0)})
def _process_room_update(room_data: dict):
    if not isinstance(room_data, dict):
        return
    try:
        rid = int(room_data.get("room_id") or room_data.get("roomId") or room_data.get("id"))
        if rid not in ROOM_ORDER:
            return

        players = int(_parse_number(
            room_data.get("user_cnt")
            if room_data.get("user_cnt") is not None
            else room_data.get("userCount", 0)
        ) or 0)
        bet = _parse_number(
            room_data.get("total_bet_amount")
            if room_data.get("total_bet_amount") is not None
            else (room_data.get("totalBet") if room_data.get("totalBet") is not None else room_data.get("bet", 0))
        ) or 0.0

        room_state[rid] = {"players": players, "bet": float(bet)}
        if rid not in room_stats:
            room_stats[rid] = {"kills": 0, "survives": 0, "last_kill_round": None, "last_players": 0, "last_bet": 0}
        room_stats[rid]["last_players"] = players
        room_stats[rid]["last_bet"] = float(bet)
    except (ValueError, TypeError):
        pass

def on_close(ws, code, reason):
    log_debug(f"WS closed: {code} {reason}")
def on_error(ws, err):
    log_debug(f"WS error: {err}")
def start_ws():
    backoff = 1.0
    while not stop_flag:
        try:
            ws_app = websocket.WebSocketApp(WS_URL, on_open=on_open, on_message=on_message, on_close=on_close, on_error=on_error)
            _ws["ws"] = ws_app
            ws_app.run_forever(ping_interval=15, ping_timeout=6)
        except Exception as e:
            log_debug(f"start_ws exception: {e}")
        t = min(backoff + random.random() * 0.8, 30)
        log_debug(f"Reconnect WS after {t}s")
        time.sleep(t)
        backoff = min(backoff * 1.8, 30)

class BalancePoller(threading.Thread):
    def __init__(self, uid: Optional[int], secret: Optional[str], poll_seconds: int = 2, on_balance=None, on_error=None, on_status=None):
        super().__init__(daemon=True)
        self.uid = uid
        self.secret = secret
        self.poll_seconds = max(1, int(poll_seconds))
        self._running = True
        self._last_balance_local: Optional[float] = None
        self.on_balance = on_balance
        self.on_error = on_error
        self.on_status = on_status

    def stop(self):
        self._running = False

    def run(self):
        if self.on_status:
            self.on_status("Kết nối...")
        while self._running and not stop_flag:
            try:
                build, world, usdt = fetch_balances_3games(params={"userId": str(self.uid)} if self.uid else None, uid=self.uid, secret=self.secret)
                if build is None:
                    raise RuntimeError("Không đọc được balance từ response")
                delta = 0.0 if self._last_balance_local is None else (build - self._last_balance_local)
                first_time = (self._last_balance_local is None)
                if first_time or abs(delta) > 0:
                    self._last_balance_local = build
                    if self.on_balance:
                        self.on_balance(float(build), float(delta), {"ts": human_ts()})
                    if self.on_status:
                        self.on_status("Đang theo dõi")
                else:
                    if self.on_status:
                        self.on_status("Đang theo dõi (không đổi)")
            except Exception as e:
                if self.on_error:
                    self.on_error(str(e))
                if self.on_status:
                    self.on_status("Lỗi kết nối vui lòng thử lại...")
            for _ in range(max(1, int(self.poll_seconds * 5))):
                if not self._running or stop_flag:
                    break
                time.sleep(0.2)
        if self.on_status:
            self.on_status("Đã dừng")

def monitor_loop():
    global last_balance_fetch_ts, last_msg_ts, stop_flag

    while not stop_flag:
        now = time.time()

        if now - last_balance_fetch_ts >= BALANCE_POLL_INTERVAL:
            last_balance_fetch_ts = now
            try:
                fetch_balances_3games(
                    params={"userId": str(USER_ID)} if USER_ID else None
                )
            except Exception as e:
                log_debug(f"monitor fetch err: {e}")

        if now - last_msg_ts > 12:
            log_debug("No ws msg >12s, send enter_game")
            try:
                safe_send_enter_game(_ws.get("ws"))
            except Exception as e:
                log_debug(f"monitor send err: {e}")

        if now - last_msg_ts > 45:
            log_debug("No ws msg >45s, force reconnect")
            try:
                wsobj = _ws.get("ws")
                if wsobj:
                    try:
                        wsobj.close()
                    except Exception:
                        pass
            except Exception:
                pass

        try:
            # Luôn dùng countdown / end_time từ server
            remaining = _vth_get_remaining_seconds()

            if (
                analysis_start_ts
                and (time.time() - analysis_start_ts >= analysis_duration)
                and not prediction_locked
                and remaining is not None
                and remaining <= 10
            ):
                lock_prediction_if_needed()

        except Exception as e:
            log_debug(f"monitor loop err: {e}")

        time.sleep(1)

def _spinner_char():
    return _spinner[int(time.time() * 4) % len(_spinner)]
    
def _rainbow_border_style() -> str:
    idx = int(time.time() * 4) % len(VIP_COLORS)
    return VIP_COLORS[idx]
# ================== GIAO DIỆN GAME VTH ==================

def build_premium_header():
    logo_text = build_logo_with_gradient(LOGO_SMALL)

    info_table = Table(box=None, show_header=False, pad_edge=False, expand=True)
    info_table.add_column(
        style=f"bold {VBTOOL_COLORS['bright_cyan']}",
        no_wrap=True,
        justify="right",
        width=18)
    info_table.add_column(style="white")

    info_table.add_row(
        f"{ICONS['user']}User:",
        f"[bold {VBTOOL_COLORS['platinum']}]{USER_ID}[/bold {VBTOOL_COLORS['platinum']}]"
        if USER_ID else "[dim]-[/dim]")

    b = f"{current_build:,.2f}" if isinstance(current_build, (int, float)) else "0.00"
    info_table.add_row(
        f"{ICONS['money']}Số dư:",
        f"[bold {VBTOOL_COLORS['emerald']}]{b}[/bold {VBTOOL_COLORS['emerald']}] BUILD")

    pnl_val = cumulative_profit if cumulative_profit is not None else 0
    if pnl_val > 0:
        pnl_color = VBTOOL_COLORS["emerald"]
        pnl_icon = "📈"
    elif pnl_val < 0:
        pnl_color = VBTOOL_COLORS["ruby"]
        pnl_icon = "📉"
    else:
        pnl_color = VBTOOL_COLORS["white"]
        pnl_icon = "➖"

    info_table.add_row(
        f"{ICONS['chart']}Lãi/lỗ:",
        f"[{pnl_color}]{pnl_icon} {pnl_val:+,.2f}[/{pnl_color}] BUILD")

    streak_text = Text.assemble(
        ("🏆 ", f"bold {VBTOOL_COLORS['neon_orange']}"),
        (f"{win_streak}", f"bold {VBTOOL_COLORS['emerald']}"),
        (" | ", "dim"),
        ("💀 ", f"bold {VBTOOL_COLORS['ruby']}"),
        (f"{lose_streak}", f"bold {VBTOOL_COLORS['ruby']}"))

    info_table.add_row("🔥Chuỗi hiện tại:", streak_text)

    elapsed=int(time.time()-tool_start_time)
    h,m=divmod(elapsed,3600)
    m,s=divmod(m,60)
    info_table.add_row(
        f"{ICONS['trophy']}Kỷ lục chuỗi:",
        Text.assemble(("🏆 ","bold gold"),(f"{max_win_streak}",f"bold {VBTOOL_COLORS['emerald']}"),(" | ","dim"),("💀 ","bold red"),(f"{max_lose_streak}",f"bold {VBTOOL_COLORS['ruby']}")))

    info_table.add_row(
        f"{ICONS['target']}Ván hiện tại:",
        f"[{VBTOOL_COLORS['white']} dim]{issue_id if issue_id else '_'}[/{VBTOOL_COLORS['white']} dim]")

    algo_label = SELECTION_MODES.get(selected_vth_algo, SELECTION_MODES.get(settings.get("algo"), settings.get("algo")))
    info_table.add_row(
        f"{ICONS['brain']}Thuật toán:",
        (f"[bold bright_red]{algo_label}[/bold bright_red]" if list(SELECTION_MODES).index(settings.get("algo"))>=13 else f"[bold bright_cyan]{algo_label}[/bold bright_cyan]"))
    info_table.add_row(
        f"{ICONS['clock']}Chạy tool:",       f"[{VBTOOL_COLORS['white']}]{h:02}:{m:02}:{s:02}[/{VBTOOL_COLORS['white']}]")

    content = Group(
        Align.center(logo_text),
        info_table)

    return Panel(
        content,
        border_style=VBTOOL_COLORS["neon_pink"],
        box=box.HEAVY,
        padding=(1, 2))
def build_premium_rooms():
    table = Table.grid(expand=True)
    table.add_column(ratio=1)

    for i, room in enumerate(ROOM_ORDER, 1):
        st = room_state.get(room, {})
        line = (
            f"{i:>2}. "
            f"{ROOM_NAMES[room]:<20}"
            f"👥 {st.get('players', 0):>2}      "
            f"💰 {int(st.get('bet', 0) or 0):,}")

        if room == predicted_room:
            style = "bold bright_green"
        elif room == killed_room:
            style = "bold red"
        else:
            style = None

        table.add_row(f"[{style}]{line}[/{style}]" if style else line)

    return Panel(
        table,
        title="[bold cyan]═══ BÀN CHƠI ═══[/bold cyan]",
        border_style="bright_blue",
        box=box.ROUNDED,
        padding=(1, 2),
        expand=True,)

def build_premium_mid():
    global analysis_start_ts, last_display_bet, count_down

    if ui_state == "ANALYZING":

        remaining_val = _vth_get_remaining_seconds()

        # Chưa nhận countdown / chưa có mốc kết thúc từ server
        if remaining_val is None:
            remaining_text = "--"
            percent = 0
        else:
            remaining_val = max(0.0, float(remaining_val))
            remaining_text = f"{int(math.ceil(remaining_val))}"
            if remaining_val >= 60:
                percent = 0
            elif remaining_val <= 10:
                percent = 100
            else:
                # 60s -> 0%, 5s -> 100%
                percent = int(round(((60.0 - remaining_val) / 50.0) * 100))

            percent = max(0, min(100, percent))

        BAR_LENGTH = 50
        filled = int(BAR_LENGTH * percent / 100)
        bar = "█" * filled + "░" * (BAR_LENGTH - filled)

        text = [
            f"[bold {VBTOOL_COLORS['bright_cyan']}]🤖 AI ĐANG PHÂN TÍCH[/bold {VBTOOL_COLORS['bright_cyan']}]",
            "",
            f"[bold white]{bar}[/bold white]  [bold {VBTOOL_COLORS['white']}]{percent}%[/bold {VBTOOL_COLORS['white']}]",
            "",
            f"⏳ [bold {VBTOOL_COLORS['gold']}]Thời gian còn lại: {remaining_text}s[/bold {VBTOOL_COLORS['gold']}]"
        ]

        return Panel(
            Text.from_markup("\n".join(text)),
            border_style=VBTOOL_COLORS["dark_blue"],
            box=box.ROUNDED,
            padding=(1, 2),
            expand=True,
        )

    if ui_state == "PREDICTED":
        name = ROOM_NAMES.get(predicted_room, "-")

        bet_amount = last_display_bet if last_display_bet else current_bet
        bet = f"{bet_amount:,.2f}"

        target = Text.from_markup(
            f"""
[bold {VBTOOL_COLORS['bright_green']}]╔══════════════════════════════════════════╗[/]
[bold {VBTOOL_COLORS['bright_green']}]║[/][bold {VBTOOL_COLORS['gold']}]{'🎯 ĐÃ CHỌN MỤC TIÊU 🎯':^40}[/][bold {VBTOOL_COLORS['bright_green']}]║[/]
[bold {VBTOOL_COLORS['bright_green']}]║[/][bold {VBTOOL_COLORS['emerald']}]{name:^41}[/][bold {VBTOOL_COLORS['bright_green']}]║[/]
[bold {VBTOOL_COLORS['bright_green']}]║[/][bold {VBTOOL_COLORS['gold']}]{('💰 ' + bet + ' BUILD'):^41}[/][bold {VBTOOL_COLORS['bright_green']}]║[/]
[bold {VBTOOL_COLORS['bright_green']}]╚══════════════════════════════════════════╝[/]
"""
        )

        status = Text.assemble(
            ("☠️ Kill ván trước: ", ""),
            (ROOM_NAMES.get(last_killed_room, "-"), f"bold {VBTOOL_COLORS['ruby']}"),
            ("  |  🏆 Win: ", ""),
            (str(win_streak), f"bold {VBTOOL_COLORS['emerald']}"),
            ("  |  💀 Lose: ", ""),
            (str(lose_streak), f"bold {VBTOOL_COLORS['ruby']}"))

        return Panel(
            Group(
                Align.center(target),
                Align.center(status)),
            border_style=VBTOOL_COLORS["bright_green"],
            box=box.HEAVY,
            padding=1,
            expand=True)
    if ui_state == "RESULT":
        killed = ROOM_NAMES.get(killed_room, "-") if killed_room else "-"
        result = "Chờ"
        color = VBTOOL_COLORS["yellow"]
        if bet_history:
            last = bet_history[-1]
            if last.get("issue") == issue_id:
                if last.get("result") == "Thắng":
                    result = "Win"
                    color = VBTOOL_COLORS["bright_green"]
                elif last.get("result") == "Thua":
                    result = "Lose"
                    color = VBTOOL_COLORS["ruby"]
        profit_color = (
            VBTOOL_COLORS["ruby"]
            if cumulative_profit < 0
            else VBTOOL_COLORS["bright_green"])
        content = Text.assemble(
            ("\n", ""),           ("╔═══════════════════════════════════╗\n", color),
            ("║  ", color),
            (f"{result:^31}", f"bold {color}"),
            ("  ║\n", color),
            ("╚═══════════════════════════════════╝\n", color),
            ("\n☠️ Sát thủ vừa vào: ", ""),
            (killed, f"bold {VBTOOL_COLORS['ruby']}"),
            ("\n📊 Lãi/lỗ: ", ""),
            (f"{cumulative_profit:+,.2f}", f"bold {profit_color}"),
            (" BUILD", ""))

        return Panel(
            Align.center(content),
            border_style=color,
            box=box.HEAVY,
            padding=1,
            expand=True)

def get_algo_color(algo):
    algo = str(algo or "").upper().strip()
    # Thuật toán 1 - 13 (Xanh ngọc)
    if algo in {"RANDOM","MIN_PLAYER_BET","PROBABILITY","FOLLOW_KILLER","MIN_BET","SEQUENTIAL","KILLER_PERSONALITY","ALL","SMART_SAFE","FOLLOW_KILLER_DELAYED","HIDE_SEEK_MASTER","MANY_PLAYER_LOW_BET","HOT_SAFE"}:
        return VBTOOL_COLORS["turquoise"]

    # Thuật toán 14 - 23 (Đỏ)
    if algo in {"HOA_THAN","KILLER_WAVE","PSYCHO_ANALYSIS","DEEP_ANALYSIS","MARKOV_CHAIN","GOD_MODE","HUNTER","HEAVEN_EYE","INFINITY","TONG_HOP"}: return VBTOOL_COLORS["ruby"]
    return VBTOOL_COLORS["white"]
    
def _history_room_name(room: Any) -> str:
    """Tên phòng duy nhất dùng cho lịch sử, theo ID P1-P8."""
    try:
        rid = int(room)
    except (TypeError, ValueError):
        return "-"
    return ROOM_NAMES.get(rid, "-") if rid in ROOM_ORDER else "-"

def build_premium_history():
    t = Table(
        title=f"[bold {VBTOOL_COLORS['white']} dim] ═══LỊCH SỬ CƯỢC═══[/bold {VBTOOL_COLORS['white']} dim]",
        box=box.ROUNDED,
        expand=True,       border_style=VBTOOL_COLORS["onyx"])
    t.add_column("Ván", no_wrap=True, style=f"{VBTOOL_COLORS['white']} dim")
    t.add_column("Phòng", no_wrap=True, style=VBTOOL_COLORS["emerald"])
    t.add_column("Tiền", justify="right", no_wrap=True, style=VBTOOL_COLORS["gold"])
    t.add_column("Kết quả", no_wrap=True)
    t.add_column("Thuật toán", no_wrap=True)
    last_n = list(bet_history)[-6:]
    for b in reversed(last_n):
        amt = b.get("amount") or 0
        res = str(b.get("result") or "⏳")
        algo = str(b.get("algo") or "-")
        if "Thắng" in res:
            res_text = Text(f"✅ Win", style=VBTOOL_COLORS["emerald"])
        elif "Thua" in res:
            res_text = Text(f"❌ Lose", style=VBTOOL_COLORS["ruby"])
        else:
            res_text = Text(f"⏳ Đang đặt", style=f"{VBTOOL_COLORS['yellow']} dim")

        algo_name = SELECTION_MODES.get(algo, algo) if algo and algo != "-" else "-"
        if algo in {"HOA_THAN","KILLER_WAVE","PSYCHO_ANALYSIS","DEEP_ANALYSIS","MARKOV_CHAIN","GOD_MODE","HUNTER","HEAVEN_EYE","INFINITY","TONG_HOP"}: algo_color = VBTOOL_COLORS["ruby"]

        else:
            algo_color = VBTOOL_COLORS["turquoise"]

        algo_text = Text(algo_name, style=algo_color)

        t.add_row(
            str(b.get("issue") or "-"),
            _history_room_name(b.get("room")),
            f"{float(amt):,.2f}",
            res_text,
            algo_text,)

    return Panel(
        t,
        border_style=VBTOOL_COLORS["sapphire"],
        box=box.HEAVY,
        expand=True)

def save_strategy_config():
    config_data = {"base_bet": base_bet, "multiplier": multiplier, "algo": settings.get("algo"), "bet_rounds_before_skip": bet_rounds_before_skip, "pause_after_losses": pause_after_losses, "profit_target": profit_target, "stop_when_profit_reached": stop_when_profit_reached, "stop_loss_target": stop_loss_target, "stop_when_loss_reached": stop_when_loss_reached}
    try:
        with open(STRATEGY_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
        console.print(f"[green]✅ Cấu hình của bạn đã được lưu thành công[/green]")
    except Exception as e:
        console.print(f"[red]❌Không thể lưu cấu hình: {e}[/red]")

def load_strategy_config() -> bool:
    global base_bet, multiplier, run_mode, bet_rounds_before_skip, current_bet, pause_after_losses, profit_target, stop_when_profit_reached, stop_loss_target, stop_when_loss_reached
    if not Path(STRATEGY_CONFIG_FILE).exists():
        console.print(f"[yellow]⚠️ Không tìm thấy cấu hình.[/yellow]")
        console.print("[yellow] Vui lòng sử dụng lựa chọn 4. để lưu cấu hình trước.[/yellow]")
        return False
    try:
        with open(STRATEGY_CONFIG_FILE, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        base_bet = config_data.get("base_bet", 1.0)
        multiplier = config_data.get("multiplier", 2.0)
        settings["algo"] = config_data.get("algo", "SAFE")
        global selected_vth_algo
        selected_vth_algo = settings["algo"]
        bet_rounds_before_skip = config_data.get("bet_rounds_before_skip", 0)
        pause_after_losses = config_data.get("pause_after_losses", 0)
        profit_target = config_data.get("profit_target", None)
        stop_when_profit_reached = config_data.get("stop_when_profit_reached", False)
        stop_loss_target = config_data.get("stop_loss_target", None)
        stop_when_loss_reached = config_data.get("stop_when_loss_reached", False)
        current_bet = base_bet
        run_mode = "AUTO"
        console.print(f"[green]✅ Đã tải cấu hình thành công[/green]")
        console.print()
        summary = build_config_summary()
        console.print(Panel(summary, title="[bold]CẤU HÌNH CỦA BẠN[/bold]", box=box.HEAVY, border_style=VBTOOL_COLORS["emerald"], expand=False))
        time.sleep(2)
        return True
    except Exception as e:
        console.print(f"[red] ❌ Không thể tải cấu hình: {e}[/red]")
        return False

def build_config_header():
    return Text("")
def build_step_indicator(current_step: int, total_steps: int):
    return ""
def prompt_settings() -> bool:
    global base_bet, multiplier, run_mode
    global bet_rounds_before_skip, current_bet
    global pause_after_losses
    global profit_target, stop_when_profit_reached
    global stop_loss_target, stop_when_loss_reached
    console.clear()
    console.print(build_config_header())
    console.print()
    console.print(build_step_indicator(1, 4))
    console.print(
        Rule(f"[bold {VBTOOL_COLORS['neon_pink']}]CHỌN THUẬT TOÁN[/bold {VBTOOL_COLORS['neon_pink']}]",
            style=VBTOOL_COLORS["neon_pink"],))

    modes = list(SELECTION_MODES.items())

    algo_table = Table(
        box=box.ROUNDED,
        border_style=VBTOOL_COLORS["dark_blue"]
    )

    algo_table.add_column(
        "STT",
        style=f"bold {VBTOOL_COLORS['turquoise']}",
        width=4)

    algo_table.add_column(
        "Tên thuật toán",
        style=VBTOOL_COLORS["white"])

    is_vip = is_vip_activated()

    for i, (key, label) in enumerate(modes, 1):

        style = VBTOOL_COLORS["white"]

        if (
            key in [
                "HOA_THAN",
                "KILLER_WAVE",
                "PSYCHO_ANALYSIS",
                "DEEP_ANALYSIS",
                "MARKOV_CHAIN",
                "GOD_MODE",
                "HUNTER",
                "HEAVEN_EYE",
                "INFINITY",
                "TONG_HOP",
            ]
            and not is_vip
        ):
            label += " 🔒 (Chỉ dành cho KEY VIP)"
            style = "dim"

        algo_table.add_row(
            str(i),
            f"[{style}]{label}[/{style}]")

    console.print(algo_table)
    console.print()

    while True:

        choice = IntPrompt.ask("👉 Chọn số thứ tự")

        if choice < 1 or choice > len(modes):
            console.print(f"[bold red]❌ Vui lòng nhập từ 1 đến {len(modes)}[/bold red]")
            continue

        if not is_vip and choice >= 14:
            console.print("[bold red]❌ Lựa chọn này chỉ dành cho Key VIP![/bold red]")
            time.sleep(2)
            continue

        break

    selected_key = modes[choice - 1][0]

    global selected_vth_algo
    selected_vth_algo = selected_key
    settings["algo"] = selected_key

    if selected_key in [
        "HOA_THAN",
        "KILLER_WAVE",
        "PSYCHO_ANALYSIS",
        "DEEP_ANALYSIS",
        "MARKOV_CHAIN",
        "GOD_MODE",
        "HUNTER",
        "HEAVEN_EYE",
        "INFINITY",
        "TONG_HOP",
    ] and not is_vip:
        console.print("[red]❌ Logic VIP chỉ dành cho Key VIP![/red]")
        settings["algo"] = "RANDOM"

    console.print(f"[green]✅ Đã chọn: {SELECTION_MODES.get(selected_vth_algo, selected_vth_algo)}[/green]")

    time.sleep(1)
    
    if settings["algo"] == "ALL":

        console.print()
        console.print(f"[bold {VBTOOL_COLORS['gold']}]💰 MỤC TIÊU LÃI (Enter = Tắt)[/bold {VBTOOL_COLORS['gold']}]")

        pt_str = Prompt.ask(f"[bold {VBTOOL_COLORS['white']}]👉Nhập số BUILD muốn đạt[/bold {VBTOOL_COLORS['white']}]")

        if pt_str.strip():
            try:
                profit_target = float(pt_str)
                stop_when_profit_reached = True
                console.print(f"[green]✅ Đã đặt mục tiêu lãi: Dừng khi số dư >= {profit_target:,.2f} BUILD[/green]")
            except ValueError:
                profit_target = None
                stop_when_profit_reached = False
        else:
            profit_target = None
            stop_when_profit_reached = False

        stop_loss_target = None
        stop_when_loss_reached = False

        base_bet = 0
        multiplier = 1
        current_bet = 0
        bet_rounds_before_skip = 0
        pause_after_losses = 0

        run_mode = "AUTO"
        return True

    console.clear()
    console.print(build_config_header())
    console.print()

    console.print(build_step_indicator(2, 4))
    console.print(
        Rule(f"[bold {VBTOOL_COLORS['gold']}]QUẢN LÝ VỐN[/bold {VBTOOL_COLORS['gold']}]",
            style=VBTOOL_COLORS["gold"],))

    console.print()

    base_bet = FloatPrompt.ask(f"[bold {VBTOOL_COLORS['white']}]  1. Cược gốc: Số BUILD sẽ đặt mỗi ván (tối thiểu 1.0)[/bold {VBTOOL_COLORS['white']}]")

    console.print()

    multiplier = FloatPrompt.ask(f"[bold {VBTOOL_COLORS['white']}]  2. Hệ số nhân sau khi thua[/bold {VBTOOL_COLORS['white']}]")

    current_bet = base_bet

    console.print()
    console.print(f"[green]  ✅ Cược gốc: {base_bet:,.2f} BUILD[/green]")
        
    console.print(f"[green]  ✅ Hệ số nhân: x{multiplier}[/green]")

    time.sleep(1)

    console.clear()
    console.print(build_config_header())
    console.print()

    console.print(build_step_indicator(3, 4))
    console.print(
        Rule(f"[bold {VBTOOL_COLORS['bright_green']}]QUẢN LÝ RỦI RO[/bold {VBTOOL_COLORS['bright_green']}]",
            style=VBTOOL_COLORS["bright_green"],))

    console.print()

    bet_rounds_before_skip = IntPrompt.ask(
        f"[bold {VBTOOL_COLORS['white']}]  3. Chống soi: Nghỉ 1 ván sau bao nhiêu ván cược? (0 = Tắt)[/bold {VBTOOL_COLORS['white']}]")

    console.print()

    pause_after_losses = IntPrompt.ask(
        f"[bold {VBTOOL_COLORS['white']}]  4. Nghỉ sau khi thua: Nghỉ bao nhiêu ván? (0 = Tắt)[/bold {VBTOOL_COLORS['white']}]")

    console.clear()
    console.print(build_config_header())
    console.print()

    console.print(build_step_indicator(4, 4))
    console.print(
        Rule(f"[bold {VBTOOL_COLORS['gold']}]ĐẶT MỤC TIÊU[/bold {VBTOOL_COLORS['gold']}]",
            style=VBTOOL_COLORS["gold"],))

    console.print()

    pt_str = Prompt.ask(f"[bold {VBTOOL_COLORS['white']}]  5. Mục tiêu lãi: Nhập số BUILD muốn đặt (Enter = Tắt)[/bold {VBTOOL_COLORS['white']}]")

    if pt_str.strip():
        try:
            profit_target = float(pt_str)
            stop_when_profit_reached = True
            console.print(f"[green]  ✅ Đã đặt mục tiêu lãi: {profit_target:,.2f} BUILD[/green]")
        except ValueError:
            profit_target = None
            stop_when_profit_reached = False
    else:
        profit_target = None
        stop_when_profit_reached = False

    console.print()

    sl_str = Prompt.ask(f"[bold {VBTOOL_COLORS['white']}]  6. Cắt lỗ: Nhập số BUILD tối thiểu còn lại để dừng (Enter = Tắt)[/bold {VBTOOL_COLORS['white']}]")

    if sl_str.strip():
        try:
            stop_loss_target = float(sl_str)
            stop_when_loss_reached = True
            console.print(f"[green]  ✅ Đã đặt cắt lỗ: Còn {stop_loss_target:,.2f} BUILD[/green]")
        except ValueError:
            stop_loss_target = None
            stop_when_loss_reached = False
    else:
        stop_loss_target = None
        stop_when_loss_reached = False

    console.print()
    console.print("[bold green]  ✅ Hoàn tất cấu hình![/bold green]")
    time.sleep(1)

    console.clear()

    run_mode = "AUTO"
    return True

def load_accounts() -> list:
    acc_file = Path("accounts.json")
    if not acc_file.exists():
        return []
    try:
        return json.loads(acc_file.read_text())
    except (json.JSONDecodeError, IOError):
        return []

def save_accounts(accounts: list):
    acc_file = Path("accounts.json")
    with acc_file.open("w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2)

def add_new_account(accounts: list) -> bool:
    while True:
        console.clear()

        console.print(Panel(
            Text.assemble(
                (" Hướng dẫn lấy link game:\n", "green"),
                ("    1. Truy cập: https://xworld.info/vi-VN\n", "white"),
                ("    2. Đăng nhập tài khoản\n", "white"),
                ("    3. Chọn Vua Thoát Hiểm\n", "white"),
                ("    4. Bấm 'Lập tức truy cập'\n", "white"),
                ("    5. Sao chép link trên thanh địa chỉ và dán vào đây", "white"),
            ),
            border_style=VBTOOL_COLORS["sapphire"],
            box=box.ROUNDED,
        ))

        link = Prompt.ask(
            f"[bold {VBTOOL_COLORS['yellow']}]👉 Dán link vào đây (Enter để huỷ)[/bold {VBTOOL_COLORS['yellow']}]"
        ).strip()

        if not link:
            console.print("[yellow]Đã huỷ.[/yellow]")
            time.sleep(1)
            return False

        try:
            params = parse_qs(urlparse(link).query)
            uid = int(params["userId"][0])
            skey = params["secretKey"][0].strip()

            if not skey:
                raise ValueError

            accounts.append({"userId": uid, "secretKey": skey})
            save_accounts(accounts)

            console.print(Panel(
                Align.center(Text(
                    f"{ICONS['check']} Đã thêm tài khoản: {uid} thành công",
                    style="bold bright_green"
                )),
                border_style=VBTOOL_COLORS["emerald"],
                box=box.ROUNDED,
            ))

            time.sleep(2)
            return True

        except (KeyError, IndexError):
            console.print("[bold red]❌ Link game không hợp lệ![/bold red]")
        except ValueError:
            console.print("[bold red]❌ UserID hoặc SecretKey không hợp lệ![/bold red]")
        except Exception as e:
            console.print(f"[bold red]❌ Lỗi: {e}[/bold red]")

        time.sleep(2)

def start_threads():
    threading.Thread(target=start_ws, daemon=True).start()
    threading.Thread(target=monitor_loop, daemon=True).start()

def start_game_flow():
    global stop_flag, IS_VIP_USER, active_vth_poller

    if USER_ID is None or SECRET_KEY is None:
        console.print("[red]❌ Chưa chọn tài khoản.[/red]")
        time.sleep(2)
        return

    _, _, IS_VIP_USER = check_activation_valid()

    # Khởi động các luồng nền
    start_threads()

    # Khởi động poller luôn, không chờ kết nối
    poller = BalancePoller(
        USER_ID,
        SECRET_KEY,
        poll_seconds=max(1, int(BALANCE_POLL_INTERVAL)),
        on_balance=None,
        on_error=None,
        on_status=None,
    )
    active_vth_poller = poller
    poller.start()

    def generate_layout() -> Table:
        is_mobile = console.width < 100
        if is_mobile:
            main_layout = Table.grid(expand=True, pad_edge=False)
            main_layout.add_row(build_premium_rooms())
            main_layout.add_row(build_premium_mid())
            main_layout.add_row(build_premium_history())
        else:
            main_grid = Table.grid(expand=True, pad_edge=False)
            main_grid.add_column("main", ratio=60)
            main_grid.add_column("side", ratio=40)
            right_column_grid = Table.grid(expand=True, pad_edge=False)
            right_column_grid.add_row(build_premium_mid())
            right_column_grid.add_row(build_premium_history())
            main_grid.add_row(build_premium_rooms(), right_column_grid)
            main_layout = main_grid
        root_layout = Table.grid(expand=True, pad_edge=False)
        root_layout.add_row(build_premium_header())
       #  root_layout.add_row(build_premium_marquee())
        root_layout.add_row(main_layout)
        return root_layout

    try:
        with Live(generate_layout(), refresh_per_second=4, console=console, screen=True) as live:
            try:
                while not stop_flag:
                    live.update(generate_layout())
                    time.sleep(0.25)
                console.print("[bold yellow]Tool đã dừng.[/]")
            except KeyboardInterrupt:
                _shutdown_vth_runtime("[bold yellow]Đã dừng tool.[/bold yellow]")
    finally:
        _shutdown_vth_runtime()
        try:
            poller.stop()
        except Exception:
            pass
        if active_vth_poller is poller:
            active_vth_poller = None

def main_vth():
    start_key_expiry_monitor()

    if not check_activation_valid()[0]:
        console.print("[bold red]❌ Key của bạn không còn hiệu lực.[/bold red]")
        time.sleep(2)
        return

    global stop_flag, USER_ID, SECRET_KEY
    stop_flag = False

    console.clear()
    save_accounts([])
    if not add_new_account([]):
        return

    accounts = load_accounts()
    if not accounts:
        return

    USER_ID = accounts[0]["userId"]
    SECRET_KEY = accounts[0]["secretKey"]

    console.clear()
    if not prompt_settings():
        return

    console.clear()
    start_game_flow()

# ================== TOOL 2: LOTTO ==================

ACCOUNTS_FILE = "accounts.json"
CONFIG_FILE = "wh_config.json"
API_URL = "https://api.winhash.net/lucky_game/hourly_issue_list"
HOME_URL = "https://api.winhash.net/lucky_game/home"
API_URL_GET_BALANCE = "https://wallet.3games.io/api/wallet/user_asset"
HOME_POLL_INTERVAL = 3
UI_REFRESH = 6
DECIMALS = 4

ICON_LOTTO = {"nho": "🔵", "lon": "🔴", "hoa": "⚖️", 1:"1", 2:"2", 3:"3", 4:"4", 5:"5", 6:"6"}
NUMBER_COLORS = {1:"bright_blue", 2:"bright_cyan", 3:"bright_green", 4:"yellow", 5:"bright_magenta", 6:"bright_red"}

_num_re_local = re.compile(r"-?\d+[\d,]*\.?\d*")

# ================== CLASS PHÂN TÍCH LOTTO ==================

class ThreeNumberAnalyzer:
    def __init__(self):
        self.position_stats = {0: defaultdict(lambda: Counter()), 1: defaultdict(lambda: Counter()), 2: defaultdict(lambda: Counter())}
        self.position_names = {0: "ĐẦU", 1: "GIỮA", 2: "CUỐI"}
        self.pattern_history = []
        self.last_seen_index = {0: {}, 1: {}, 2: {}}

    def _build_position_stats(self, history: List[Dict], decay: float = 0.06):
        self.pattern_history = []
        for p in [0,1,2]:
            self.position_stats[p] = defaultdict(lambda: Counter())
            self.last_seen_index[p] = {}
        n = max(1, len(history) - 1)
        for i in range(len(history) - 1):
            current = history[i].get('lucky_codes', [])
            next_codes = history[i + 1].get('lucky_codes', [])
            if len(current) == 3 and len(next_codes) == 3:
                distance = (n - 1) - i
                weight = float(math.exp(-decay * max(0, distance)))
                for pos in [0, 1, 2]:
                    trigger_num = current[pos]
                    result_num = next_codes[pos]
                    self.position_stats[pos][trigger_num][result_num] += weight
                self.pattern_history.append({'current': tuple(current), 'next': tuple(next_codes), 'current_sum': sum(current), 'next_sum': sum(next_codes)})
        for pos in [0,1,2]:
            seen = {}
            for dist, rec in enumerate(reversed(history)):
                codes = rec.get('lucky_codes', [])
                if not isinstance(codes, list) or len(codes) != 3:
                    continue
                num = codes[pos]
                if num not in seen:
                    seen[num] = dist
            self.last_seen_index[pos] = seen

    def _predict_position(self, position: int, current_num: int, context: Optional[Tuple[int,int,int]] = None) -> Dict:
        stats = self.position_stats[position][current_num]
        total = float(sum(stats.values()))
        if total == 0:
            return {i: 1/6 for i in range(1, 7)}
        probs = {i: stats.get(i, 0) / total for i in range(1, 7)}
        alpha = 0.5
        last_seen = self.last_seen_index.get(position, {})
        recency_boost = {}
        for i in range(1,7):
            dist = last_seen.get(i)
            if dist is None:
                recency_boost[i] = 1.0
            else:
                recency_boost[i] = 1.0 + max(0.0, (6.0 - float(dist)) / 12.0)
        smoothed = {}
        denom = total + 6 * alpha
        for i in range(1,7):
            base = (stats.get(i, 0) + alpha) / denom
            smoothed[i] = base * recency_boost.get(i, 1.0)
        s_sum = sum(smoothed.values())
        if s_sum <= 0:
            return {i: 1/6 for i in range(1, 7)}
        base_probs = {i: smoothed[i] / s_sum for i in range(1,7)}
        if context and self.pattern_history:
            boost = defaultdict(float)
            total_ctx = 0.0
            for idx, ph in enumerate(reversed(self.pattern_history)):
                cur = ph.get('current')
                nxt = ph.get('next')
                if not cur or not nxt: continue
                match = 0
                for p in range(3):
                    if p == position: continue
                    if context[p] == cur[p]:
                        match += 1
                if match >= 1:
                    recency_w = math.exp(-0.06 * idx)
                    observed = nxt[position]
                    boost[observed] += recency_w * (1.0 + match * 0.25)
                    total_ctx += recency_w
            if total_ctx > 0:
                ctx_probs = {i: (boost.get(i, 0.0) / total_ctx) for i in range(1,7)}
                mix = 0.25
                blended = {i: base_probs.get(i,0.0) * (1.0 - mix) + ctx_probs.get(i,0.0) * mix for i in range(1,7)}
                s = sum(blended.values())
                if s > 0:
                    return {i: blended[i]/s for i in range(1,7)}
        return base_probs

    def analyze(self, history: List[Dict]) -> Dict:
        if len(history) < 2:
            return {"last_three": [], "position_probs": [{}, {}, {}], "predicted_numbers": [], "predicted_sum": 0, "prediction": None, "confidence": 0.0, "bet_action": "small"}
        self._build_position_stats(history)
        last_record = history[-1]
        last_three = last_record.get('lucky_codes', [])
        if len(last_three) != 3:
            return {"last_three": last_three, "position_probs": [{}, {}, {}], "predicted_numbers": [], "predicted_sum": 0, "prediction": None, "confidence": 0.0, "bet_action": "small"}
        position_probs = []
        predicted_numbers = []
        total_confidence = 0.0
        per_number_details = []
        for pos in [0, 1, 2]:
            current_num = last_three[pos]
            probs = self._predict_position(pos, current_num, context=last_three)
            details = {}
            counts = self.position_stats[pos]
            sample_size = float(sum(counts.get(current_num, Counter()).values())) if counts.get(current_num) else 0.0
            for num in range(1,7):
                prob = probs.get(num, 0.0)
                dist = self.last_seen_index.get(pos, {}).get(num)
                recency_score = 0.0 if dist is None else max(0.0, (12.0 - float(dist)) / 12.0)
                freq = 0
                for k,v in self.position_stats[pos].items():
                    freq += v.get(num, 0)
                freq_score = float(freq) / max(1.0, sum(sum(c.values()) for c in self.position_stats[pos].values()))
                score = prob * 0.6 + recency_score * 0.25 + freq_score * 0.15
                details[num] = {'prob': prob, 'recency_score': recency_score, 'freq': freq, 'freq_score': freq_score, 'score': score}
            position_probs.append(probs)
            best_num = max(details.items(), key=lambda x: x[1]['score'])[0]
            predicted_numbers.append(best_num)
            total_confidence += details[best_num]['prob']
            per_number_details.append({'position': pos, 'current': current_num, 'sample_size': sample_size, 'details': details})
        predicted_sum = sum(predicted_numbers)
        avg_confidence = total_confidence / 3
        if 3 <= predicted_sum <= 9:
            bet_action = "nho"
            prediction = "Nho"
        elif 10 <= predicted_sum <= 11:
            bet_action = "hoa"
            prediction = "Hoa"
        elif 12 <= predicted_sum <= 18:
            bet_action = "lon"
            prediction = "Lon"
        else:
            bet_action = "nho"
            prediction = "Nho"
        sample_sizes = []
        for pos in [0, 1, 2]:
            current_num = last_three[pos]
            stats = self.position_stats[pos][current_num]
            sample_sizes.append(sum(stats.values()))
        avg_sample = sum(sample_sizes) / 3 if sample_sizes else 0
        try:
            ent = 0.0
            for probs in position_probs:
                s = 0.0
                for p in probs.values():
                    if p > 0: s -= p * math.log(p)
                ent += s
            avg_entropy = ent / 3.0 if position_probs else 0.0
            entropy_penalty = avg_entropy / max(1.0, math.log(6))
            avg_confidence *= max(0.25, 1.0 - 0.5 * entropy_penalty)
        except Exception:
            pass
        if avg_sample < 3:
            avg_confidence *= 0.55
        elif avg_sample < 6:
            avg_confidence *= 0.8
        return {"last_three": last_three, "position_probs": position_probs, "predicted_numbers": predicted_numbers, "predicted_sum": predicted_sum, "prediction": prediction, "confidence": avg_confidence, "sample_sizes": sample_sizes, "bet_action": bet_action, "per_position_details": per_number_details}

class AccountManager:
    def __init__(self, path: str = ACCOUNTS_FILE):
        self.path = path
        self.accounts = self._load()

    def _load(self) -> List[Dict]:
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.accounts, f, ensure_ascii=False, indent=2)

    def parse_link_to_account(self, link: str) -> Optional[Dict]:
        try:
            p = urlparse(link)
            qs = parse_qs(p.query)

            user_id = qs.get("userId", [None])[0]
            secret = qs.get("secretKey", [None])[0]

            if not user_id or not secret:
                return None

            return {
                "user-id": user_id,
                "user-secret-key": secret,
                "country-code": "vn",
                "user-agent": "Mozilla/5.0",
                "asset": "BUILD",
            }

        except Exception:
            return None

    def add_account(self) -> Dict:
        while True:
            raw = Prompt.ask("👉 Dán link game")

            if raw.strip() == "":
                raise KeyboardInterrupt

            # Chỉ chấp nhận link có userId và secretKey
            if (
                raw.startswith("http")
                and "userId=" in raw
                and "secretKey=" in raw
            ):
                acc = self.parse_link_to_account(raw)

                if acc:
                    self.accounts.clear()
                    self.accounts.append(acc)
                    self.save()

                    console.print(
                        Panel(
                            f"✅ Đăng nhập thành công\nUser ID: {acc['user-id']}",
                            style="bold green",
                            border_style="green",
                        )
                    )

                    return acc

            console.print("[bold red]❌ Link không hợp lệ![/bold red]")

    def remove_account(self, index: int) -> bool:
        if 0 <= index < len(self.accounts):
            self.accounts.pop(index)
            self.save()
            return True
        return False

class MartingaleBetting:

    def __init__(self, initial_bet: float, multiplier: float, asset: str):
        self.initial_bet = float(initial_bet)
        self.multiplier = float(multiplier)
        self.asset = asset
        self.current_bet = float(initial_bet)
        self.total_wagered = 0.0
        self.total_won = 0.0
        self.win_count = 0
        self.loss_count = 0
        self.current_win_streak = 0
        self.current_loss_streak = 0
        self.max_win_streak = 0
        self.max_loss_streak = 0
        self.net_profit = 0.0

    def get_bet_amount(self) -> float:
        return float(self.current_bet)

    def on_win(self, payout: float):
        try:
            self.total_won += float(payout)
        except Exception:
            pass
        self.win_count += 1
        self.current_bet = float(self.initial_bet)
        self.current_win_streak += 1
        self.current_loss_streak = 0
        if self.current_win_streak > self.max_win_streak:
            self.max_win_streak = self.current_win_streak

    def on_loss(self):
        self.loss_count += 1
        self.current_bet = float(self.current_bet) * float(self.multiplier)
        self.current_loss_streak += 1
        self.current_win_streak = 0
        if self.current_loss_streak > self.max_loss_streak:
            self.max_loss_streak = self.current_loss_streak

    def record_wager(self, amount: float):
        try:
            self.total_wagered += float(amount)
        except Exception:
            pass

    def get_stats(self) -> Dict:
        net_profit = self.total_won - self.total_wagered
        total_bets = self.win_count + self.loss_count
        return {"total_bets": total_bets, "wins": self.win_count, "losses": self.loss_count, "total_wagered": self.total_wagered, "total_won": self.total_won, "net_profit": net_profit, "current_bet": self.current_bet, "asset": self.asset, "current_win_streak": self.current_win_streak, "current_loss_streak": self.current_loss_streak, "max_win_streak": self.max_win_streak, "max_loss_streak": self.max_loss_streak}

def build_headers(config: Dict[str, str]) -> Dict[str, str]:
    return {'accept': '*/*', 'accept-language': 'en-US,en;q=0.9', 'country-code': config.get('country-code', 'vn'), 'origin': 'https://winhash.io', 'referer': 'https://winhash.io/', 'user-agent': config.get('user-agent', 'Mozilla/5.0'), 'user-id': config['user-id'], 'user-login': 'login_v2', 'user-secret-key': config['user-secret-key'], 'xb-language': config.get('xb-language', 'en-US')}

def fetch_issue_list(session: requests.Session, headers: Dict[str, str], ts: int) -> List[Dict]:
    params = {'ts': str(ts)}
    try:
        resp = session.get(API_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get('code') is not None and data.get('code') != 0:
            return []
        return data.get('data', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    except Exception:
        return []

def fetch_home(session: requests.Session, headers: Dict[str, str], asset: str) -> Optional[Dict]:
    params = {'game_id': '1', 'asset': asset}
    try:
        resp = session.get(HOME_URL, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get('code') is not None and data.get('code') != 0:
            return None
        return data.get('data') if isinstance(data, dict) else None
    except Exception:
        return None

def get_balance(s: requests.Session, headers: Dict[str, str], uid: str, key: str) -> Dict[str, Dict[str, float]]:
    h = headers.copy()
    h["user-id"] = uid
    h["user-secret-key"] = key

    try:
        payload = {
            "user_id": int(uid) if str(uid).isdigit() else uid,
            "source": "home"
        }

        r = s.post(
            API_URL_GET_BALANCE,
            headers=h,
            json=payload,
            timeout=10
        )
        r.raise_for_status()

        d = r.json()

        if isinstance(d, dict) and d.get("code") == 0:

            data = d.get("data") or {}
            ua = data.get("user_asset") or data.get("assets") or data

            build = world = usdt = None

            if isinstance(ua, list):
                for item in ua:
                    asset = str(item.get("asset", "")).upper()
                    bal = _safe_round(
                        item.get("balance")
                        or item.get("amount")
                        or 0
                    )

                    if asset == "BUILD":
                        build = bal
                    elif asset in ("WORLD", "XWORLD"):
                        world = bal
                    elif asset == "USDT":
                        usdt = bal

            elif isinstance(ua, dict):
                for k, v in ua.items():

                    name = str(k).upper()

                    if isinstance(v, dict):
                        bal = _safe_round(
                            v.get("balance")
                            or v.get("amount")
                            or 0
                        )
                    else:
                        bal = _safe_round(v)

                    if name == "BUILD":
                        build = bal
                    elif name in ("WORLD", "XWORLD"):
                        world = bal
                    elif name == "USDT":
                        usdt = bal

            build = 0.0 if build is None else build
            world = 0.0 if world is None else world
            usdt = 0.0 if usdt is None else usdt

            return {
                "BUILD": {"balance": build},
                "XWORLD": {"balance": world},
                "USDT": {"balance": usdt},
            }

    except Exception as e:
        logger.debug(f"get_balance error: {e}")

    return {
        "BUILD": {"balance": 0.0},
        "XWORLD": {"balance": 0.0},
        "USDT": {"balance": 0.0},
    }

def _safe_round(val: Any, ndigits: int = DECIMALS) -> float:
    try:
        return round(float(val), ndigits)
    except Exception:
        return 0.0

def _parse_number_local(x) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x)
    m = _num_re_local.search(s)
    if not m:
        return None
    token = m.group(0).replace(",", "")
    try:
        return float(token)
    except Exception:
        return None

def sum_to_label(total: int) -> str:
    try:
        total = int(total)
    except Exception:
        return "unknown"
    if 3 <= total <= 9:
        return "nho"
    if 10 <= total <= 11:
        return "hoa"
    if 12 <= total <= 18:
        return "lon"
    return "unknown"

def get_balances_from_home(home: Dict) -> Dict[str, Optional[float]]:
    build = None
    world = None
    usdt = None
    if not isinstance(home, dict):
        return {"BUILD": None, "XWORLD": None, "USDT": None}
    ua = home.get('user_asset') or home.get('wallet') or home.get('assets') or {}
    if isinstance(ua, dict):
        if 'BUILD' in ua:
            build = _parse_number_local(ua.get('BUILD'))
        if 'WORLD' in ua:
            world = _parse_number_local(ua.get('WORLD'))
        if 'USDT' in ua:
            usdt = _parse_number_local(ua.get('USDT'))
    for k in ('build','ctoken','ctoken_contribute','balance','amount'):
        if build is None and k in home:
            build = _parse_number_local(home.get(k))
    for k in ('world','xworld','WORLD','XWORLD'):
        if world is None and k in home:
            world = _parse_number_local(home.get(k))
    for k in ('usdt','kusdt','USDT'):
        if usdt is None and k in home:
            usdt = _parse_number_local(home.get(k))
    if build is None or world is None or usdt is None:
        try:
            s = json.dumps(home)
            if build is None:
                m = re.search(r'(?:BUILD|build)[:\"\']*\s*([0-9\.,]+)', s, re.I)
                if m: build = _parse_number_local(m.group(1))
            if world is None:
                m = re.search(r'(?:WORLD|world|xworld)[:\"\']*\s*([0-9\.,]+)', s, re.I)
                if m: world = _parse_number_local(m.group(1))
            if usdt is None:
                m = re.search(r'(?:USDT|usdt|kusdt)[:\"\']*\s*([0-9\.,]+)', s, re.I)
                if m: usdt = _parse_number_local(m.group(1))
        except Exception:
            pass
    return {"BUILD": build, "XWORLD": world, "USDT": usdt}

def get_hour_start_timestamp(hour_offset: int = 0):
    now = datetime.now(timezone.utc)
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    hour_start = hour_start - timedelta(hours=hour_offset)
    return int(hour_start.timestamp())

def compute_number_counts(history: List[Dict]) -> Dict[str, Any]:
    overall = Counter()
    per_pos = {0: Counter(), 1: Counter(), 2: Counter()}
    for rec in history:
        codes = rec.get('lucky_codes') or []
        if not isinstance(codes, list) or len(codes) != 3:
            continue
        for pos, num in enumerate(codes):
            per_pos[pos][num] += 1
            overall[num] += 1
    return {'overall': overall, 'per_pos': per_pos}

def issue_to_record(issue: Dict) -> Optional[Dict]:
    lucky_codes = issue.get('lucky_codes') or []
    if len(lucky_codes) != 3:
        return None
    total = sum(lucky_codes)
    return {'issue_id': issue.get('issue_id'), 'lucky_codes': lucky_codes, 'sum': total, 'result': sum_to_label(total)}

def home_to_record(home: Dict) -> Optional[Dict]:
    last_issue_id = home.get('last_issue_id')
    lucky_codes = home.get('last_issue_lucky_code') or []
    if last_issue_id is None or len(lucky_codes) != 3:
        return None
    total = sum(lucky_codes)
    return {'issue_id': last_issue_id, 'lucky_codes': lucky_codes, 'sum': total, 'result': sum_to_label(total)}

def place_bet(session: requests.Session, headers: Dict[str, str], issue_id: int, bet_type: str, amount: float, asset: str) -> tuple:
    bet_ids = {'nho': 70309, 'lon': 71218, 'hoa': 71011}
    if bet_type not in bet_ids:
        return False, "Invalid bet type"
    payload = {"game_id": 1, "issue_id": issue_id, "items": [{"id": bet_ids[bet_type], "amount": str(amount), "asset": asset}]}
    try:
        resp = session.post('https://api.winhash.net/lucky_game/v2/create_order', headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            success = data.get('code') == 0
            error_msg = data.get('msg', 'Unknown error')
            return success, error_msg if not success else "Success"
        else:
            return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)

def make_vbtool_header(tick: int = 0):
    logo_text = build_logo_with_gradient(LOGO_VBTOOL)

    activation = load_activation()

    key_type = "Chưa kích hoạt"
    key_color = "bold white"
    key_time = "⏰ Chưa kích hoạt"

    if activation:
        try:
            if activation.get("key_type") == "VIP":
                key_type = "VIP"
                key_color = "bold red"
            else:
                key_type = "FREE"
                key_color = "bold green"

            expiry_time = datetime.fromisoformat(activation["expiry_time"])
            remaining = expiry_time - datetime.now()

            if remaining.total_seconds() > 0:
                days = remaining.days
                hours = (remaining.seconds % 86400) // 3600
                minutes = (remaining.seconds % 3600) // 60

                if days > 0:
                    key_time = f"⏰ Còn {days} Ngày {hours} Giờ"
                elif hours > 0:
                    key_time = f"⏰ Còn {hours} Giờ {minutes} Phút"
                else:
                    key_time = f"⏰ Còn {minutes} Phút"
            else:
                key_time = "❌ Đã hết hạn"

        except Exception:
            key_type = "Không xác định"
            key_color = "bold red"
            key_time = "❌ Không xác định"

    admin_info = Text.assemble(
        ("\n", ""),
        (f"{ICONS['user']} Admin : ", "bold magenta"),
        ("Nguyễn Văn Bảo", "bold cyan"),
        ("              ", ""),
        (f"{ICONS['phone']} ", "bold gold"),
        ("Zalo : ", "bold orange1"),
        ("0797676482", "bold white"),
        ("\n", ""),
        ("💎 Loại Key : ", "bold deepsky_blue1"),
        (key_type, key_color),
        ("                      ", ""),
        (key_time, "bold bright_green"),
        ("\n", ""),
        ("━" * 60 + "\n", f"dim {VBTOOL_COLORS['gold']}"),
    )

    return Group(
        Align.center(logo_text),
        Align.center(admin_info),
    )

def make_vbtool_compact_panel(state: Dict, tick: int = 0) -> Panel:
    balances = state.get('balances') or {}
    def _fmt_bal(b):
        try:
            if b is None: return '—'
            if isinstance(b, dict): return f"{_safe_round(b.get('balance',0)):.2f}"
            return f"{_safe_round(b):.2f}"
        except: return '—'
    b_build = _fmt_bal(balances.get('BUILD'))
    b_x = _fmt_bal(balances.get('XWORLD'))
    last_issue = state.get('last_issue', '—')
    last_result = state.get('last_result', '—')
    next_pred = state.get('next_prediction', '—')
    conf = state.get('next_confidence', 0.0)
    analysis = state.get('three_number_analysis', {})
    last_three = analysis.get('last_three', [])
    predicted_numbers = analysis.get('predicted_numbers', [])
    predicted_sum = analysis.get('predicted_sum', 0)
    start_bal = None
    if isinstance(state.get('start_balances'), dict):
        try:
            start_bal = float(state['start_balances'].get('BUILD', {}).get('balance'))
        except: pass
    cur_bal = None
    try:
        b = balances.get('BUILD')
        if isinstance(b, dict): cur_bal = b.get('balance')
        else: cur_bal = float(b) if b else None
    except: pass
    model_stats = state.get('model_stats', {})
    wins = model_stats.get('wins', 0)
    losses = model_stats.get('losses', 0)
    total_pred = model_stats.get('predictions', 0)
    win_rate = (wins / total_pred * 100) if total_pred > 0 else 0.0

    t = Text()
    t.append(f"{ICONS['user']} User: {state.get('account_id', '—')}", style=VBTOOL_COLORS["history_blue"])
    t.append("  |  ", style="dim")
    t.append(f"{ICONS['diamond']} BUILD: {b_build}", style=f"bold {VBTOOL_COLORS['emerald']}")
    t.append("  |  ", style="dim")
    t.append(f"🌍 XW: {b_x}", style=VBTOOL_COLORS["history_blue"])
    t.append("\n" + "━" * 68 + "\n", style=VBTOOL_COLORS["gold"])
    t.append(f"📊 Kết quả #{last_issue}: {last_result}", style=VBTOOL_COLORS["platinum"])
    t.append(f"  |  Tỷ lệ: ", style="dim")
    t.append(f"{win_rate:.0f}%", style=f"bold {VBTOOL_COLORS['history_blue']}")
    if start_bal is not None and cur_bal is not None:
        diff = _safe_round(cur_bal - start_bal, DECIMALS)
        pct = (diff / start_bal * 100.0) if (start_bal and start_bal != 0) else 0.0
        sign = "+" if diff > 0 else ""
        if diff > 0: arrow, style = "🚀", f"bold {VBTOOL_COLORS['emerald']}"
        elif diff < 0: arrow, style = "💔", f"bold {VBTOOL_COLORS['ruby']}"
        else: arrow, style = "➡️", VBTOOL_COLORS["gold"]
        t.append("  |  ", style="dim")
        t.append(f"{arrow} {sign}{diff:.2f} ({sign}{pct:.1f}%)", style=style)
    t.append("\n" + "─" * 68 + "\n", style="dim")
    t.append(f"{ICONS['dice']} Hiện tại: ", style="dim")
    for num in last_three:
        icon = ICON_LOTTO.get(num, str(num))
        color = NUMBER_COLORS.get(num, "white")
        t.append(f"{icon} ", style=f"bold {color}")
    t.append("  →  ", style="dim")
    t.append("Dự đoán: ", style="dim")
    for num in predicted_numbers:
        icon = ICON_LOTTO.get(num, str(num))
        color = NUMBER_COLORS.get(num, "white")
        t.append(f"{icon} ", style=f"bold {color}")
    t.append(f"(Σ={predicted_sum})", style=VBTOOL_COLORS["gold"])
    t.append("\n")
    t.append(f"{ICONS['target']} Cược tiếp: ", style="dim")
    t.append(f"{next_pred}", style=f"bold {VBTOOL_COLORS['neon_pink']}")
    if conf:
        conf_bar = int(conf * 12)
        conf_style = VBTOOL_COLORS["emerald"] if conf >= 0.7 else (VBTOOL_COLORS["gold"] if conf >= 0.5 else VBTOOL_COLORS["ruby"])
        t.append("  [", style="dim")
        t.append("█" * conf_bar, style=conf_style)
        t.append("░" * (12 - conf_bar), style="dim")
        t.append(f" {conf*100:.0f}%]", style=conf_style)
    hist = state.get('history', []) or []
    counts = compute_number_counts(hist) if hist else {'overall': Counter(), 'per_pos': {0: Counter(), 1: Counter(), 2: Counter()}}
    overall = counts.get('overall', {})
    if overall:
        t.append("\n", "")
        t.append("🔥❄️ Hot/Cold: ", style="dim")
        maxc = max(overall.values()) if overall else 1
        for n in range(1,7):
            c = overall.get(n, 0)
            color = NUMBER_COLORS.get(n, 'white')
            bl = int((c / maxc) * 6) if maxc else 0
            bars = '█' * bl + ' ' * (6 - bl)
            t.append(f" {ICON_LOTTO.get(n)}", style=f"bold {color}")
            t.append(bars, style=color)
        t.append("\n", "")
    t.append(f"{ICONS['chart']} Tổng: ", style="dim")
    t.append(f"{total_pred} ván", style=VBTOOL_COLORS["platinum"])
    t.append("  |  🏆 Win ", style="dim")
    t.append(f"{wins}", style=VBTOOL_COLORS["emerald"])
    t.append("  💀 Lose ", style="dim")
    t.append(f"{losses}", style=VBTOOL_COLORS["ruby"])
    bet_stats = state.get('bet_stats')
    if bet_stats:
        win_streak = bet_stats.get('current_win_streak', 0)
        loss_streak = bet_stats.get('current_loss_streak', 0)
        if win_streak > 0:
            t.append("\n", "")
            t.append(f"{ICONS['fire']} Chuỗi thắng: ", style=VBTOOL_COLORS["emerald"])
            t.append(f"{win_streak}", style=f"bold {VBTOOL_COLORS['emerald']}")
            if win_streak >= 3:
                t.append(" 🏆", style=VBTOOL_COLORS["gold"])
        if loss_streak > 0:
            t.append("\n", "")
            t.append(f"💀 Chuỗi thua: ", style=VBTOOL_COLORS["ruby"])
            t.append(f"{loss_streak}", style=f"bold {VBTOOL_COLORS['ruby']}")
            if loss_streak >= 3:
                t.append(" ⚠️", style=VBTOOL_COLORS["gold"])
        t.append("\n", "")
        total_wagered = bet_stats.get('total_wagered', 0)
        if start_bal is not None and cur_bal is not None:
            net_profit = _safe_round(cur_bal - start_bal, DECIMALS)
        else:
            net_profit = bet_stats.get('net_profit', 0)
        asset = bet_stats.get('asset', 'BUILD')
        t.append(f"{ICONS['money']} Đã cược: ", style="dim")
        t.append(f"{total_wagered:.2f} {asset}", style=VBTOOL_COLORS["gold"])
        profit_style = f"bold {VBTOOL_COLORS['emerald']}" if net_profit > 0 else (f"bold {VBTOOL_COLORS['ruby']}" if net_profit < 0 else VBTOOL_COLORS["gold"])
        t.append(f"  |  {ICONS['chart']} Lãi/Lỗ: ", style="dim")
        t.append(f"{net_profit:+.2f} {asset}", style=profit_style)
    log_text = state.get('log_text', '—')
    t.append("\n" + "─" * 68 + "\n", style="dim")
    t.append(log_text, style=VBTOOL_COLORS["platinum"])
    t.append("\n", "")
    return Panel(t, border_style=VBTOOL_COLORS["bright_cyan"], box=box.SIMPLE_HEAVY, padding=(0, 1))

def make_vbtool_history_cards(history: List[Dict], limit: int = 5, cols: int = 1, tick: int = 0, highlight_issue: Optional[int] = None) -> Panel:
    recent = list(reversed(history[-limit:]))
    cards = []
    for rec in recent:
        issue = rec.get('issue_id')
        ts = rec.get('timestamp', '')
        short_ts = ts[11:19] if isinstance(ts, str) and len(ts) >= 19 else ''
        codes = rec.get('lucky_codes', [])
        code_line = Text()
        for i, n in enumerate(codes):
            color = NUMBER_COLORS.get(n, 'white')
            code_line.append(f" {ICON_LOTTO.get(n)} ", style=f"bold {color}")
            if i < len(codes)-1:
                code_line.append(' ', style='dim')
        kq = rec.get('result', '—')
        if kq == 'nho':
            kq_style = f"bold white on {VBTOOL_COLORS['sapphire']}"
            kq_icon = '🔵'
        elif kq == 'lon':
            kq_style = f"bold white on {VBTOOL_COLORS['ruby']}"
            kq_icon = '🔴'
        else:
            kq_style = f"bold black on {VBTOOL_COLORS['gold']}"
            kq_icon = '⚖️'
        bet = rec.get('bet') or {}
        pl = None
        try:
            bb = bet.get('balance_before')
            ba = bet.get('balance_after')
            if bb is not None and ba is not None:
                pl = float(ba) - float(bb)
            else:
                pl = bet.get('profit')
        except Exception:
            pl = bet.get('profit') if bet else None
        if pl is None:
            pl_text = Text('—', style='dim')
        elif pl > 0:
            pl_text = Text(f'+{pl:.2f}', style=f'bold {VBTOOL_COLORS["emerald"]}')
        elif pl < 0:
            pl_text = Text(f'{pl:.2f}', style=f'bold {VBTOOL_COLORS["ruby"]}')
        else:
            pl_text = Text(f'{pl:.2f}', style=VBTOOL_COLORS["gold"])
        bs = VBTOOL_COLORS["onyx"]
        if highlight_issue is not None and issue == highlight_issue:
            bs = VBTOOL_COLORS["gold"]
        card = Panel(Align.left(Text.assemble(Text(f"#{str(issue)[-4:]} ", style=f'bold {VBTOOL_COLORS["history_blue"]}'), Text(short_ts + '\n', style='dim'), code_line, Text('\n', ''), Text.assemble(Text(kq_icon + ' ', style=kq_style), Text(' ', ''), pl_text))), box=box.ROUNDED, padding=(0, 1), border_style=bs)
        cards.append(card)
    if not cards:
        return Panel(Text('Không có lịch sử', style='dim'), border_style=VBTOOL_COLORS["onyx"])
    return Panel(Columns(cards, equal=True, expand=True), title=f"LỊCH SỬ GẦN ĐÂY", border_style=VBTOOL_COLORS["history_blue"], box=box.ROUNDED)

def make_vbtool_layout(state: Dict) -> Layout:
    tick = state.get("tick", 0)

    layout = Layout(name="root")
    layout.split_column(
        Layout(name="header", size=8),
        Layout(name="main", ratio=1),
        Layout(name="history", size=12),)

    layout["header"].update(make_vbtool_header(tick))
    layout["main"].update(make_vbtool_compact_panel(state, tick))
    layout["history"].update(
        make_vbtool_history_cards(
            state.get("history", []),
            limit=5,
            cols=1,
            tick=tick,
            highlight_issue=state.get("last_issue"),))

    return layout
    
def choose_free(history):
    analysis = three_number_analyzer.analyze(history)
    return analysis
    
def choose_vip(history, analyzer):
    analysis = analyzer.analyze(history)
    score = {
        "nho": 0,
        "hoa": 0,
        "lon": 0
    }

    recent = history[-30:]
    # 1. Lịch sử có trọng số
    for i, item in enumerate(recent):
        weight = i + 1
        result = str(item.get("result", "")).lower()
        if result in score:
            score[result] += weight

    # 2. Chuỗi liên tiếp
    streak = 1
    if len(recent) >= 2:
        last = recent[-1]["result"].lower()
        for i in range(len(recent) - 2, -1, -1):
            if recent[i]["result"].lower() == last:
                streak += 1
            else:
                break
        if streak >= 4:
            if last == "nho":
                score["lon"] += 30
            elif last == "lon":
                score["nho"] += 30
            else:
                score["hoa"] += 15
    # 3. Phân tích lucky_codes
    for item in recent:
        nums = item.get("lucky_codes", [])
        if nums:
            tong = sum(nums)
            if tong < 14:
                score["nho"] += 2
            elif tong > 13:
                score["lon"] += 2
            else:
                score["hoa"] += 2
    # 4. Kết hợp AI gốc
    ai = analysis.get("bet_action", "nho")
    if ai in score:
        score[ai] += 20
    # 5. Quyết định cuối
    bet = max(score, key=score.get)
    analysis["bet_action"] = bet
    analysis["confidence"] = 0.95
    analysis["score"] = score
    return analysis

def main_lotto():
    start_key_expiry_monitor()
    if not check_activation_valid()[0]:
        console.print("[bold red]❌ Key của bạn không còn hiệu lực.[/bold red]")
        time.sleep(2)
        return

    console.clear()
    am = AccountManager()
    console.print(make_vbtool_header(0))
    console.print(
        Panel(
            "📋 Vui lòng dán link game để đăng nhập",
            title="LOTTO",            border_style=VBTOOL_COLORS["history_blue"],
            box=box.ROUNDED,))
    try:
        selected_account = am.add_account()
    except KeyboardInterrupt:
        return
    if not selected_account:
        console.print("[bold red]❌ Không thêm được tài khoản![/bold red]")
        return

    # Kiểm tra kích hoạt
    _, _, is_vip = check_activation_valid(exit_on_expired=False)
    # Lấy thông tin tài khoản
    uid = (
        selected_account.get("user-id")
        or selected_account.get("userId")
        or selected_account.get("uid"))
    secret = (
        selected_account.get("user-secret-key")
        or selected_account.get("secretKey")
        or selected_account.get("user_secret_key"))
    if not uid:
        console.print("[bold red]❌ Không tìm thấy User ID![/bold red]")
        return
    if not secret:
        console.print("[bold red]❌ Không tìm thấy Secret Key![/bold red]")
        return
    config = {
        "user-id": uid,
        "user-secret-key": secret,
        "country-code": selected_account.get("country-code", "vn"),
        "user-agent": selected_account.get("user-agent", "Mozilla/5.0"),
        "asset": selected_account.get("asset", "BUILD"),
    }

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    headers = build_headers(config)
    session = requests.Session()
    asset = config.get("asset", "BUILD")

    while True:
        try:
            bet_per_round = float(
                Prompt.ask(
                    f"[bold {VBTOOL_COLORS['white']}]1. Cược mỗi ván bao nhiêu BUILD?[/bold {VBTOOL_COLORS['white']}]",))
            break
        except ValueError:
            console.print("[bold red]❌ Vui lòng nhập số hợp lệ![/bold red]")

    while True:
        try:
            multiplier = float(
                Prompt.ask(
                    f"[bold {VBTOOL_COLORS['white']}]2. Nhập số nhân sau khi thua[/bold {VBTOOL_COLORS['white']}]",))
            break
        except ValueError:
            console.print("[bold red]❌ Vui lòng nhập số hợp lệ![/bold red]")

    while True:
        answer = Prompt.ask(
            f"[bold {VBTOOL_COLORS['white']}]3. Bật auto cược? (y/n)[/bold {VBTOOL_COLORS['white']}]"
        ).strip().lower()

        if answer in ("y", "yes"):
            enable_betting = True
            break
        elif answer in ("n", "no"):
            enable_betting = False
            break
        else:
            console.print(
                f"[bold {VBTOOL_COLORS['red']}]❌ Vui lòng nhập y hoặc n![/bold {VBTOOL_COLORS['red']}]"
            )

    betting_system = (
        MartingaleBetting(bet_per_round, multiplier, asset)
        if enable_betting
        else None
    )
    
    current_ts = get_hour_start_timestamp(0)
    previous_ts = get_hour_start_timestamp(1)
    issues = {}
    for issue in fetch_issue_list(session, headers, previous_ts) + fetch_issue_list(session, headers, current_ts):
        if issue.get('issue_id'):
            issues[issue['issue_id']] = issue
    history = [issue_to_record(i) for i in sorted(issues.values(), key=lambda x: x['issue_id']) if issue_to_record(i)]
    if not history:
        console.print('[bold red]❌ Không có lịch sử. Kiểm tra kết nối/config.[/bold red]')
        return
    three_number_analyzer = ThreeNumberAnalyzer()
    last_processed = max(h['issue_id'] for h in history)
    pending = {}
    pending_bets = {}
    processed_issue_ids = set()
    stop = False
    def handle_stop(_sig, _frame):
        raise KeyboardInterrupt

    state = {
        'account_id': selected_account.get('user-id') if selected_account else None,
        'balances': {"BUILD": None, "XWORLD": None, "USDT": None},
        'start_balances': {},
        'last_result': '—',
        'last_issue': '—',
        'next_prediction': '—',
        'next_confidence': None,
        'planned_bet': 0.0,
        'history_table': None,
        'history': history,
        'three_number_analysis': three_number_analyzer.analyze(history),
        'bet_stats': None,
        'model_stats': {'predictions':0, 'wins':0, 'losses':0, 'current_streak':0},
        'log_text': 'Sẵn sàng ✅',
        'tick': 0,
        'asset': asset
    }
    console.clear()
    with Live(make_vbtool_layout(state), console=console, refresh_per_second=UI_REFRESH) as live:
        history_changed = True
        while not stop:
            if not check_activation_valid()[0]:
                stop = True
                break

            history_changed = False
            state['tick'] = (state.get('tick', 0) + 1) % 1000000
            try:
                state['history_table'] = make_vbtool_history_cards(state.get('history', []), limit=5, cols=1, tick=state.get('tick', 0), highlight_issue=state.get('last_issue'))
            except Exception:
                pass
            try:
                uid = selected_account.get('user-id')
                key = selected_account.get('user-secret-key')
                if uid and key:
                    bmap = get_balance(session, headers, uid, key)
                    if isinstance(bmap, dict):
                        state['balances'] = bmap
                        if not state.get('start_balances'):
                            state['start_balances'] = {k: {'balance': float(v.get('balance',0)) if isinstance(v, dict) else _safe_round(v)} for k,v in bmap.items()}
                            state['log_text'] = 'Đã lưu số dư khởi điểm'
            except Exception:
                logger.debug("Wallet API read failed")
            home_data = fetch_home(session, headers, asset)

            if not home_data:
                state['log_text'] = 'Chờ dữ liệu...'

                try:
                    live.update(make_vbtool_layout(state))
                except Exception:
                    pass

                try:
                    time.sleep(HOME_POLL_INTERVAL)
                except KeyboardInterrupt:
                    return

                continue

            try:
                if state['balances'] and all(
                    (_safe_round(state['balances'].get(k, {}).get('balance', 0)) == 0.0
                     for k in ('BUILD', 'XWORLD', 'USDT'))
                ):
                    hb = get_balances_from_home(home_data)

                    for k in ('BUILD', 'XWORLD', 'USDT'):
                        v = hb.get(k)
                        if v is not None:
                            state['balances'][k] = {
                                'balance': _safe_round(v)
                            }

                    if state['balances'] and not state.get('start_balances'):
                        state['start_balances'] = {
                            k: {
                                'balance': float(v.get('balance', 0))
                                if isinstance(v, dict)
                                else _safe_round(v)
                            }
                            for k, v in state['balances'].items()
                        }

            except Exception:
                pass
            last_id = home_data.get('last_issue_id')
            if last_id and last_id > last_processed:
                record = home_to_record(home_data)
                if record:
                    last_processed = record['issue_id']
                    actual = record['result']
                    decision = pending.pop(record['issue_id'], None)
                    bet_info = pending_bets.pop(record['issue_id'], None)
                    state['last_issue'] = record['issue_id']
                    state['last_result'] = f"{actual.upper()} ({record['sum']})"
                    if decision:
                        predicted_bet = decision.get('bet_action', 'small')
                        correct = (actual == predicted_bet)
                        result_emoji = '✅' if correct else '❌'
                        state['log_text'] = f"{result_emoji} #{record['issue_id']}: {predicted_bet.upper()} → {actual.upper()}"
                        if betting_system and bet_info:
                            if isinstance(bet_info, dict):
                                bet_type = bet_info.get('type')
                                bet_amount = float(bet_info.get('amount', 0.0))
                                b_before = bet_info.get('balance_before')
                            else:
                                try:
                                    bet_type, bet_amount = bet_info
                                    b_before = None
                                except Exception:
                                    bet_type, bet_amount, b_before = (None, 0.0, None)
                            try:
                                b_after = None
                                bmap = state.get('balances') or {}
                                bval = bmap.get('BUILD')
                                if isinstance(bval, dict):
                                    b_after = float(bval.get('balance', 0.0))
                                else:
                                    b_after = _safe_round(bval)
                            except Exception:
                                b_after = None
                            if correct:
                                payout = bet_amount * 2
                                betting_system.on_win(payout)
                            else:
                                betting_system.on_loss()
                            profit_value = None
                            try:
                                if b_before is not None and b_after is not None:
                                    profit_value = float(b_after) - float(b_before)
                                else:
                                    if correct:
                                        profit_value = payout - bet_amount
                                    else:
                                        profit_value = -bet_amount
                            except Exception:
                                profit_value = (payout - bet_amount) if correct else -bet_amount
                            record['bet'] = {'type': bet_type, 'amount': float(bet_amount), 'profit': _safe_round(profit_value, DECIMALS), 'balance_before': b_before, 'balance_after': b_after}
                            state['bet_stats'] = betting_system.get_stats()
                        ms = state.get('model_stats') or {}
                        ms['predictions'] = ms.get('predictions', 0) + 1
                        if correct:
                            ms['wins'] = ms.get('wins', 0) + 1
                            ms['current_streak'] = 0
                        else:
                            ms['losses'] = ms.get('losses', 0) + 1
                            ms['current_streak'] = ms.get('current_streak', 0) + 1
                        state['model_stats'] = ms
                    try:
                        record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
                    except Exception:
                        record['timestamp'] = None
                    if record.get("issue_id") in processed_issue_ids:
                        continue
                    processed_issue_ids.add(record.get('issue_id'))
                    existing = next((i for i,h in enumerate(history) if h.get('issue_id') == record.get('issue_id')), None)
                    if existing is None:
                        history.append(record)
                    else:
                        history[existing] = record

                    MAX_HISTORY = 500
                    if len(history) > MAX_HISTORY:
                        history = history[-MAX_HISTORY:]
                    state['history'] = history
                    state['three_number_analysis'] = three_number_analyzer.analyze(history)
                    try:
                        live.update(make_vbtool_layout(state))
                    except Exception:
                        pass
            next_id = (last_id or 0) + 1

            if next_id not in pending:
                analysis = three_number_analyzer.analyze(history)
                state['three_number_analysis'] = analysis

                predicted_outcome = analysis.get('bet_action', 'nho')
                prediction_label = analysis.get('prediction', '1-3')
                conf = analysis.get('confidence', 0.5)
                decision = {
                    'action': 'PREDICT',
                    'bet_action': predicted_outcome,
                    'prediction': prediction_label,
                    'confidence': conf
                }

                pending[next_id] = decision
                icon = ICON_LOTTO.get(predicted_outcome, '')
                state['next_prediction'] = f"{icon} {predicted_outcome.upper()}"
                state['next_confidence'] = conf
                state['log_text'] = f'Dự #{next_id}: {predicted_outcome.upper()} (tin cậy {conf*100:.1f}%)'
                if betting_system:
                    bet_amount = betting_system.get_bet_amount()
                    samples = analysis.get('sample_sizes', [0,0,0])
                    avg_sample = sum(samples) / 3.0 if samples else 0.0
                    state['planned_bet'] = bet_amount
                    success, message = place_bet(session, headers, next_id, predicted_outcome, bet_amount, asset)
                    if success:
                        betting_system.record_wager(bet_amount)
                        try:
                            b_before = None
                            bmap = state.get('balances') or {}
                            bval = bmap.get('BUILD')
                            if isinstance(bval, dict):
                                b_before = float(bval.get('balance', 0.0))
                            else:
                                b_before = _safe_round(bval)
                        except Exception:
                            b_before = None
                        pending_bets[next_id] = {'type': predicted_outcome, 'amount': bet_amount, 'balance_before': b_before}
                        state['bet_stats'] = betting_system.get_stats()
                        state['log_text'] = f'💰Cược #{next_id}: {bet_amount:.2f} {asset} → {predicted_outcome.upper()}'
                    else:
                        state['log_text'] = f'⚠️ Lỗi: {message[:30]}'
                else:
                    state['log_text'] = f'🎯 Dự đoán #{next_id}: {predicted_outcome.upper()}'
                    state['planned_bet'] = 0.0
            try:
                live.update(make_vbtool_layout(state))
            except Exception:
                pass

            try:
                time.sleep(HOME_POLL_INTERVAL)
            except KeyboardInterrupt:
                return

    console.clear()
    return


# ================== GIAO DIỆN VTH-STYLE CHO CHẠY ĐUA TỐC ĐỘ ==================
CDTD_LIVE = None
CDTD_UI_STATE = {
    "user_id": None,
    "coin": "USDT",
    "balances": {"USDT": 0.0, "WORLD": 0.0, "BUILD": 0.0},
    "issue_id": None,
    "countdown": None,
    "status": "CHỜ KẾT NỐI",
    "selected": [],
    "winner": None,
    "result": "—",
    "bet_amount": 0.0,
    "award": 0.0,
    "profit": 0.0,
    "type_bet": "winner",
    "logic_type": "free",
    "stats": {"win": 0, "lose": 0, "win_streak": 0, "max_win_streak": 0, "lose_streak": 0, "max_lose_streak": 0},
    "history": [],
    "auto_bet": True,
    "key_type": "FREE",
}


def _cdtd_ui_number(value, decimals=6):
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        value = 0.0
    if abs(value) < 1e-12:
        value = 0.0
    text = f"{value:,.{decimals}f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


def _cdtd_ui_refresh():
    if CDTD_LIVE is None:
        return
    try:
        CDTD_LIVE.update(make_cdtd_vth_layout(CDTD_UI_STATE), refresh=True)
    except Exception as exc:
        log_debug(f"CDTD UI refresh error: {exc}")


def _cdtd_ui_stop():
    global CDTD_LIVE
    live = CDTD_LIVE
    CDTD_LIVE = None
    if live is not None:
        try:
            live.stop()
        except Exception:
            pass


def _cdtd_ui_progress(countdown):
    try:
        sec = max(0.0, float(countdown))
    except (TypeError, ValueError):
        return 0, "--"
    if sec >= 60:
        percent = 0
    elif sec <= 10:
        percent = 100
    else:
        percent = int(round(((60.0 - sec) / 50.0) * 100))
    return max(0, min(100, percent)), str(int(math.ceil(sec)))


def build_cdtd_vth_header(state):
    """Header mô phỏng trực tiếp bố cục header của Vua Thoát Hiểm."""
    logo_text = build_logo_with_gradient(LOGO_SMALL)
    info_table = Table(box=None, show_header=False, pad_edge=False, expand=True)
    info_table.add_column(
        style=f"bold {VBTOOL_COLORS['bright_cyan']}",
        no_wrap=True,
        justify="right",
        width=18,
    )
    info_table.add_column(style="white")

    info_table.add_row(
        f"{ICONS['user']}User:",
        f"[bold {VBTOOL_COLORS['platinum']}]{state.get('user_id') or '-'}[/bold {VBTOOL_COLORS['platinum']}]",
    )

    coin = str(state.get("coin") or "USDT").upper()
    balance_map = state.get("balances") or {}
    balance = _cdtd_ui_number(balance_map.get(coin), 6)
    info_table.add_row(
        f"{ICONS['money']}Số dư:",
        f"[bold {VBTOOL_COLORS['emerald']}]{balance}[/bold {VBTOOL_COLORS['emerald']}] {coin}",
    )

    profit = float(state.get("profit", 0) or 0)
    if profit > 0:
        pcolor, picon = VBTOOL_COLORS["emerald"], "📈"
    elif profit < 0:
        pcolor, picon = VBTOOL_COLORS["ruby"], "📉"
    else:
        pcolor, picon = VBTOOL_COLORS["white"], "➖"
    info_table.add_row(
        f"{ICONS['chart']}Lãi/lỗ:",
        f"[{pcolor}]{picon} {profit:+,.6f}[/] {coin}",
    )

    st = state.get("stats") or {}
    streak_text = Text.assemble(
        ("🏆 ", f"bold {VBTOOL_COLORS['emerald']}"),
        (str(int(st.get("win_streak", 0) or 0)), f"bold {VBTOOL_COLORS['emerald']}"),
        (" | ", "dim"),
        ("💀 ", f"bold {VBTOOL_COLORS['ruby']}"),
        (str(int(st.get("lose_streak", 0) or 0)), f"bold {VBTOOL_COLORS['ruby']}"),
    )
    info_table.add_row("🔥Chuỗi hiện tại:", streak_text)

    info_table.add_row(
        f"{ICONS['trophy']}Kỷ lục chuỗi:",
        Text.assemble(
            ("🏆 ", "bold gold"),
            (str(int(st.get("max_win_streak", 0) or 0)), f"bold {VBTOOL_COLORS['emerald']}"),
            (" | ", "dim"),
            ("💀 ", "bold red"),
            (str(int(st.get("max_lose_streak", 0) or 0)), f"bold {VBTOOL_COLORS['ruby']}"),
        ),
    )

    info_table.add_row(
        f"{ICONS['target']}Ván hiện tại:",
        f"[{VBTOOL_COLORS['white']} dim]{state.get('issue_id') or '_'}[/{VBTOOL_COLORS['white']} dim]",
    )

    type_name = {
        "winner": "Ai là quán quân",
        "not_winner": "Ai không là quán quân",
    }.get(state.get("type_bet"), str(state.get("type_bet") or "-"))
    logic = str(state.get("logic_type", "free")).upper()
    lcolor = VBTOOL_COLORS["ruby"] if logic == "VIP" else VBTOOL_COLORS["turquoise"]
    info_table.add_row(
        "🎯Loại đặt:",
        f"[bold {VBTOOL_COLORS['gold']}]{type_name}[/bold {VBTOOL_COLORS['gold']}]  •  [bold {lcolor}]{logic}[/bold {lcolor}]",
    )

    elapsed = int(time.time() - tool_start_time)
    h, rem = divmod(elapsed, 3600)
    m, sec = divmod(rem, 60)
    info_table.add_row(
        f"{ICONS['clock']}Chạy tool:",
        f"[{VBTOOL_COLORS['white']}]{h:02}:{m:02}:{sec:02}[/{VBTOOL_COLORS['white']}]",
    )

    return Panel(
        Group(Align.center(logo_text), info_table),
        border_style=VBTOOL_COLORS["neon_pink"],
        box=box.HEAVY,
        padding=(1, 2),
    )


def build_cdtd_vth_players(state):
    """Bàn chơi kiểu VTH, chuyển 8 phòng thành 6 vận động viên."""
    selected = set()
    for item in state.get("selected") or []:
        try:
            selected.add(int(item))
        except (TypeError, ValueError):
            pass

    try:
        winner = int(state.get("winner")) if state.get("winner") is not None else None
    except (TypeError, ValueError):
        winner = None

    table = Table.grid(expand=True)
    table.add_column(ratio=1)

    for i in range(1, 7):
        line = f"{i:>2}. {NV.get(i, str(i)):<28}"

        if i == winner:
            row = Text(line, style=f"bold {VBTOOL_COLORS['ruby']}")
        elif i in selected:
            row = Text(line, style=f"bold {VBTOOL_COLORS['bright_green']}")
        else:
            row = Text(line)

        table.add_row(row)

    return Panel(
        table,
        title="[bold cyan]═══ BÀN CHƠI ═══[/bold cyan]",
        border_style="bright_blue",
        box=box.ROUNDED,
        padding=(1, 2),
        expand=True,
    )

def build_cdtd_vth_mid(state):
    status = str(state.get("status") or "ĐANG PHÂN TÍCH").upper()

    try:
        remaining = max(0.0, float(state.get("countdown") or 0))
    except (TypeError, ValueError):
        remaining = 0.0

    start_countdown = state.get("_start_countdown")

    if start_countdown is None and remaining > 0:
        state["_start_countdown"] = remaining
        start_countdown = remaining

    try:
        start_countdown = float(start_countdown or remaining or 1)
    except (TypeError, ValueError):
        start_countdown = remaining or 1

    target_countdown = 10.0

    if start_countdown > target_countdown:
        percent = int(round(
            ((start_countdown - remaining) /
             (start_countdown - target_countdown)) * 100
        ))
    elif remaining <= target_countdown:
        percent = 100
    else:
        percent = 0

    percent = max(0, min(100, percent))

    BAR_LENGTH = 50
    filled = int(BAR_LENGTH * percent / 100)
    bar = "█" * filled + "░" * (BAR_LENGTH - filled)

    remaining_text = (
        str(int(remaining))
        if remaining.is_integer()
        else f"{remaining:.1f}"
    )

    selected = []

    for x in state.get("selected") or []:
        try:
            selected.append(NV.get(int(x), str(x)))
        except (TypeError, ValueError):
            pass

    try:
        winner = (
            int(state.get("winner"))
            if state.get("winner") is not None
            else None
        )
    except (TypeError, ValueError):
        winner = None

    winner_text = (
        NV.get(winner, str(winner))
        if winner is not None
        else "-"
    )

    coin = state.get("coin", "USDT")

    bet_text = (
        f"{_cdtd_ui_number(state.get('bet_amount'), 6)} {coin}"
    )

    award_text = (
        f"{_cdtd_ui_number(state.get('award'), 6)} {coin}"
    )

    if status in {"THẮNG", "WIN"}:
        color = VBTOOL_COLORS["bright_green"]
        profit = float(state.get("profit", 0) or 0)

        profit_color = (
            VBTOOL_COLORS["ruby"]
            if profit < 0
            else VBTOOL_COLORS["bright_green"]
        )

        content = Text.assemble(
            ("\n", ""),
            ("╔═══════════════════════════════════╗\n", color),
            ("║  ", color),
            (f"{'🏆 THẮNG':^30}", f"bold {color}"),
            ("  ║\n", color),
            ("╚═══════════════════════════════════╝\n", color),
            ("\n🏆 Quán quân: ", ""),
            (winner_text, f"bold {VBTOOL_COLORS['gold']}"),
            ("\n💰 Tổng nhận: ", ""),
            (award_text, f"bold {VBTOOL_COLORS['emerald']}"),
            ("\n📊 Lãi/lỗ: ", ""),
            (f"{profit:+,.6f}", f"bold {profit_color}"),
            (f" {coin}", ""),
        )

        return Panel(
            Align.center(content),
            border_style=color,
            box=box.HEAVY,
            padding=1,
            expand=True
        )

    if status in {"THUA", "LOSE"}:
        color = VBTOOL_COLORS["ruby"]
        profit = float(state.get("profit", 0) or 0)

        profit_color = (
            VBTOOL_COLORS["ruby"]
            if profit < 0
            else VBTOOL_COLORS["bright_green"]
        )

        content = Text.assemble(
            ("\n", ""),
            ("╔═══════════════════════════════════╗\n", color),
            ("║  ", color),
            (f"{'💀 THUA':^30}", f"bold {color}"),
            ("  ║\n", color),
            ("╚═══════════════════════════════════╝\n", color),
            ("\n🏆 Quán quân: ", ""),
            (winner_text, f"bold {VBTOOL_COLORS['gold']}"),
            ("\n💰 Tổng nhận: ", ""),
            (award_text, f"bold {VBTOOL_COLORS['ruby']}"),
            ("\n📊 Lãi/lỗ: ", ""),
            (f"{profit:+,.6f}", f"bold {profit_color}"),
            (f" {coin}", ""),
        )

        return Panel(
            Align.center(content),
            border_style=color,
            box=box.HEAVY,
            padding=1,
            expand=True
        )

    if status in {
        "ĐÃ PHÂN TÍCH",
        "ĐÃ ĐẶT CƯỢC",
        "ĐANG CƯỢC",
        "ĐANG ĐẶT CƯỢC",
        "CHỜ ĐẶT CƯỢC",
        "CHỜ KẾT QUẢ",
        "ĐANG LẤY KẾT QUẢ",
    }:
        target_lines = [
            f"[bold {VBTOOL_COLORS['bright_green']}]╔══════════════════════════════════════════╗[/]",
            f"[bold {VBTOOL_COLORS['bright_green']}]║[/]"
            f"[bold {VBTOOL_COLORS['gold']}]{'🎯 ĐÃ CHỌN MỤC TIÊU 🎯':^40}[/]"
            f"[bold {VBTOOL_COLORS['bright_green']}]║[/]",
        ]

        if not selected:
            selected = ["-"]

        current_line = ""

        for name in selected:
            test_line = (
                name
                if not current_line
                else current_line + ", " + name
            )

            if len(test_line) <= 40:
                current_line = test_line
            else:
                target_lines.append(
                    f"[bold {VBTOOL_COLORS['bright_green']}]║[/]"
                    f"[bold {VBTOOL_COLORS['emerald']}]{current_line:^42}[/]"
                    f"[bold {VBTOOL_COLORS['bright_green']}]║[/]"
                )
                current_line = name

        if current_line:
            target_lines.append(
                f"[bold {VBTOOL_COLORS['bright_green']}]║[/]"
                f"[bold {VBTOOL_COLORS['emerald']}]{current_line:^42}[/]"
                f"[bold {VBTOOL_COLORS['bright_green']}]║[/]"
            )

        target_lines.extend([
            f"[bold {VBTOOL_COLORS['bright_green']}]║[/]"
            f"[bold {VBTOOL_COLORS['gold']}]{('💰 ' + bet_text):^41}[/]"
            f"[bold {VBTOOL_COLORS['bright_green']}]║[/]",
            f"[bold {VBTOOL_COLORS['bright_green']}]╚══════════════════════════════════════════╝[/]",
        ])

        target = Text.from_markup("\n".join(target_lines))

        status_text = Text.assemble(
            ("⏳ Thời gian còn lại: ", ""),
            (
                f"{remaining_text}s",
                f"bold {VBTOOL_COLORS['gold']}"
            ),
        )

        return Panel(
            Group(
                Align.center(target),
                Align.center(status_text)
            ),
            border_style=VBTOOL_COLORS["bright_green"],
            box=box.HEAVY,
            padding=1,
            expand=True
        )

    text = [
        f"[bold {VBTOOL_COLORS['bright_cyan']}]🤖 AI ĐANG PHÂN TÍCH[/bold {VBTOOL_COLORS['bright_cyan']}]",
        "",
        f"[bold white]{bar}[/bold white]  "
        f"[bold {VBTOOL_COLORS['white']}]{percent}%[/bold {VBTOOL_COLORS['white']}]",
        "",
        f"⏳ [bold {VBTOOL_COLORS['gold']}]"
        f"Thời gian còn lại: {remaining_text}s"
        f"[/bold {VBTOOL_COLORS['gold']}]"
    ]

    return Panel(
        Text.from_markup("\n".join(text)),
        border_style=VBTOOL_COLORS["dark_blue"],
        box=box.ROUNDED,
        padding=(1, 2),
        expand=True
    )

def build_cdtd_vth_history(state):
    t = Table(
        title=f"[bold {VBTOOL_COLORS['white']} dim] ═══LỊCH SỬ CƯỢC═══[/bold {VBTOOL_COLORS['white']} dim]",
        box=box.ROUNDED,
        expand=True,
        border_style=VBTOOL_COLORS["onyx"]
    )

    t.add_column("Ván", no_wrap=True, style=f"{VBTOOL_COLORS['white']} dim", width=10)
    t.add_column(
        "Người chọn",
        no_wrap=True,
        style=VBTOOL_COLORS["emerald"],
        width=22,
        overflow="ellipsis"
    )
    t.add_column("Quán quân", no_wrap=True, style=VBTOOL_COLORS["gold"], width=20)
    t.add_column("Tiền", justify="right", no_wrap=True, style=VBTOOL_COLORS["gold"], width=12)
    t.add_column("Kết quả", no_wrap=True, width=12)
    t.add_column("Logic", no_wrap=True, width=8)

    last_n = list(state.get("history") or [])[:6]

    for item in last_n:
        chosen = item.get("bot_chon") or item.get("selected") or []

        names = ",".join(
            NV.get(int(x), str(x))
            for x in chosen
        )

        top = item.get("top1")
        top_name = (
            NV.get(int(top), str(top))
            if top is not None
            else "-"
        )

        amt = item.get("my_total_bet") or item.get("amount") or 0

        pending = (
            bool(item.get("_pending_cdtd"))
            or str(item.get("status", "")).upper()
            in {"ĐANG CƯỢC", "ĐÃ ĐẶT CƯỢC"}
        )

        won = bool(item.get("kq"))

        if pending:
            res_text = Text(
                "⏳ Đang đặt",
                style=f"{VBTOOL_COLORS['yellow']} dim"
            )
        elif won:
            res_text = Text(
                "✅ THẮNG",
                style=VBTOOL_COLORS["emerald"]
            )
        else:
            res_text = Text(
                "❌ THUA",
                style=VBTOOL_COLORS["ruby"]
            )

        logic = str(
            item.get("logic_type")
            or state.get("logic_type")
            or "free"
        )

        logic_color = (
            VBTOOL_COLORS["ruby"]
            if logic.lower() == "vip"
            else VBTOOL_COLORS["turquoise"]
        )

        logic_text = Text(
            logic.upper(),
            style=logic_color
        )

        t.add_row(
            str(item.get("issue_id") or item.get("issue") or "-"),
            names or "-",
            top_name,
            f"{float(amt):,.2f}",
            res_text,
            logic_text
        )

    return Panel(
        t,
        border_style=VBTOOL_COLORS["sapphire"],
        box=box.HEAVY,
        expand=True
    )


def make_cdtd_vth_layout(state):
    is_mobile = console.width < 100
    if is_mobile:
        main_layout = Table.grid(expand=True, pad_edge=False)
        main_layout.add_row(build_cdtd_vth_players(state))
        main_layout.add_row(build_cdtd_vth_mid(state))
        main_layout.add_row(build_cdtd_vth_history(state))
    else:
        main_grid = Table.grid(expand=True, pad_edge=False)
        main_grid.add_column("main", ratio=60)
        main_grid.add_column("side", ratio=40)
        right_column_grid = Table.grid(expand=True, pad_edge=False)
        right_column_grid.add_row(build_cdtd_vth_mid(state))
        right_column_grid.add_row(build_cdtd_vth_history(state))
        main_grid.add_row(build_cdtd_vth_players(state), right_column_grid)
        main_layout = main_grid

    root_layout = Table.grid(expand=True, pad_edge=False)
    root_layout.add_row(build_cdtd_vth_header(state))
    root_layout.add_row(main_layout)
    return root_layout

# ================== TOOL 3: CHẠY ĐUA TỐC ĐỘ ==================

def prints(r, g, b, text="text", end="\n"):
    print(f"\033[38;2;{r};{g};{b}m{text}\033[0m", end=end)

def cprints(color_name, text="", end="\n"):
    h = VBTOOL_COLORS[color_name].lstrip("#")
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    prints(r, g, b, text=text, end=end)

NV = {
    1: "Bậc Thầy Tấn Công",
    2: "Quyền Sắt",
    3: "Thợ Lặn Sâu",
    4: "Cơn Lốc Sân Cỏ",
    5: "Hiệp Sĩ Phi Nhanh",
    6: "Vua Home Run",
}

def _sprint_history_sequence(history):
    seq = []
    for item in history or []:
        if not isinstance(item, dict):
            continue
        top1 = item.get("top1")
        if isinstance(top1, int):
            seq.append(top1)
        elif isinstance(top1, str) and top1.isdigit():
            seq.append(int(top1))
    return seq

def _sprint_delay(seq, nv):
    delay = 0
    for x in seq:
        if x == nv:
            break
        delay += 1
    return delay

def _sprint_current_streak(seq, nv):
    streak = 0
    for x in seq:
        if x == nv:
            streak += 1
        else:
            break
    return streak

def _sprint_weighted_recent_hits(seq, nv, limit=30, decay=0.92):
    score = 0.0
    weight = 1.0
    for x in seq[:limit]:
        if x == nv:
            score += weight
        weight *= decay
    return score

def _sprint_average_gap(seq, nv):
    positions = [i for i, x in enumerate(seq) if x == nv]
    if len(positions) < 2:
        return None
    gaps = [b - a for a, b in zip(positions, positions[1:])]
    return sum(gaps) / len(gaps)

def _sprint_follow_probability(seq, prev_nv, nv):
    after = []
    for i in range(len(seq) - 1):
        if seq[i + 1] == prev_nv:
            after.append(seq[i])
    if not after:
        return 0.0
    return after.count(nv) / len(after)

def choose_free_cdtd(history, so_nv):
    seq = _sprint_history_sequence(history)
    if not seq:
        return random.sample(range(1, 7), so_nv)

    scores = {}
    total = len(seq)

    for nv in range(1, 7):
        score = 56.0

        # 1) Tần suất tổng thể
        wins = seq.count(nv)
        rate = wins / total
        score += (0.50 - rate) * 34

        # 2) Độ trễ kể từ lần xuất hiện gần nhất
        delay = _sprint_delay(seq, nv)
        if delay >= 18:
            score += 16
        elif delay >= 12:
            score += 12
        elif delay >= 8:
            score += 8
        elif delay >= 5:
            score += 4
        elif delay <= 1:
            score -= 7

        score += min(delay * 0.45, 8.5)

        # 3) Chuỗi hiện tại
        streak = _sprint_current_streak(seq, nv)
        if streak:
            score += min(streak * 6.5, 22)

        # 4) Xu hướng 30 ván gần nhất
        recent_score = _sprint_weighted_recent_hits(seq, nv, limit=30, decay=0.90)
        score += recent_score * 4.0

        # 5) Cửa sổ 10 ván gần
        last10 = seq[:10]
        count10 = sum(1 for x in last10 if x == nv)
        if count10 == 0:
            score += 5
        elif count10 == 1:
            score += 3
        elif count10 >= 4:
            score -= 9

        # 6) Mô hình sau người đang dẫn đầu gần nhất
        if len(seq) >= 2:
            prev_top = seq[0]
            score += _sprint_follow_probability(seq, prev_top, nv) * 32

        # 7) Chu kỳ xuất hiện
        avg_gap = _sprint_average_gap(seq, nv)
        if avg_gap:
            if delay >= avg_gap * 1.4:
                score += 8
            elif delay >= avg_gap:
                score += 4
            elif delay <= avg_gap * 0.55:
                score -= 4

        # 8) Tránh chọn mã quá nóng trong lịch sử dài
        history50 = seq[:50]
        if history50:
            wins50 = history50.count(nv)
            if wins50 >= 14:
                score -= 10
            elif wins50 == 0:
                score += 5

        # 9) Chống lặp gần nhất
        if len(seq) >= 2 and seq[0] == seq[1] == nv:
            score += 5

        scores[nv] = score

    min_score = min(scores.values())
    max_score = max(scores.values())
    if max_score != min_score:
        for nv in scores:
            scores[nv] = ((scores[nv] - min_score) / (max_score - min_score)) * 100

    return sorted(scores, key=scores.get, reverse=True)[:so_nv]

def choose_not_winner_free(history, so_nv):
    seq = _sprint_history_sequence(history)
    if not seq:
        return random.sample(range(1, 7), so_nv)

    scores = {}
    total = len(seq)

    for nv in range(1, 7):
        score = 52.0

        # 1) Ít có lịch sử vô địch thì điểm càng cao
        wins = seq.count(nv)
        rate = wins / total
        score += (1 - rate) * 40

        # 2) Độ trễ: càng lâu chưa thắng càng hợp để chọn "không quán quân"
        delay = _sprint_delay(seq, nv)
        if delay >= 20:
            score += 20
        elif delay >= 15:
            score += 16
        elif delay >= 10:
            score += 12
        elif delay >= 6:
            score += 7
        elif delay <= 1:
            score -= 10

        score += min(delay * 0.35, 7)

        # 3) Người vừa thắng hoặc đang có chuỗi thắng thì giảm mạnh
        streak = _sprint_current_streak(seq, nv)
        if streak:
            score -= min(streak * 7.5, 24)

        # 4) Xu hướng 30 ván gần nhất
        recent_score = _sprint_weighted_recent_hits(seq, nv, limit=30, decay=0.90)
        score -= recent_score * 5.0

        # 5) Cửa sổ 10 ván gần
        last10 = seq[:10]
        count10 = sum(1 for x in last10 if x == nv)
        if count10 == 0:
            score += 8
        elif count10 == 1:
            score += 4
        elif count10 >= 4:
            score -= 12

        # 6) Mô hình Markov: nếu sau người hiện tại hay ra nv thì nv không hợp để "không quán quân"
        if len(seq) >= 2:
            prev_top = seq[0]
            score -= _sprint_follow_probability(seq, prev_top, nv) * 34

        # 7) Chu kỳ: nếu đang gần đến nhịp thắng của nv thì giảm điểm
        avg_gap = _sprint_average_gap(seq, nv)
        if avg_gap:
            if delay >= avg_gap * 1.5:
                score += 8
            elif delay <= avg_gap * 0.7:
                score -= 6

        # 8) Lịch sử dài
        history50 = seq[:50]
        if history50:
            wins50 = history50.count(nv)
            if wins50 == 0:
                score += 10
            elif wins50 <= 3:
                score += 5
            elif wins50 >= 12:
                score -= 10

        # 9) Chống lặp
        if len(seq) >= 2 and seq[0] == seq[1] == nv:
            score -= 8

        scores[nv] = score

    min_score = min(scores.values())
    max_score = max(scores.values())
    if max_score != min_score:
        for nv in scores:
            scores[nv] = ((scores[nv] - min_score) / (max_score - min_score)) * 100

    return sorted(scores, key=scores.get, reverse=True)[:so_nv]

# ================== TỰ HỌC CHO LOGIC VIP CHẠY ĐUA TỐC ĐỘ ==================
CDTD_LEARNING_MIN_WEIGHT = 0.55
CDTD_LEARNING_MAX_WEIGHT = 1.55
CDTD_VIP_FEATURES = (
    "frequency", "delay", "streak", "recent", "markov1",
    "markov2", "last10", "long_history", "cycle", "repeat",
)


CDTD_LEARNING_STATE = None
CDTD_LEARNING_LOCK = threading.RLock()

def _cdtd_default_learning():
    return {
        "version": 1,
        "winner": {"features": {name: {"weight": 1.0, "correct": 0, "wrong": 0} for name in CDTD_VIP_FEATURES}},
        "not_winner": {"features": {name: {"weight": 1.0, "correct": 0, "wrong": 0} for name in CDTD_VIP_FEATURES}},
        "updated_at": None,
    }

def _cdtd_learning_state():
    global CDTD_LEARNING_STATE
    with CDTD_LEARNING_LOCK:
        if CDTD_LEARNING_STATE is None:
            CDTD_LEARNING_STATE = _cdtd_default_learning()
        return CDTD_LEARNING_STATE

def _cdtd_learning_weights(mode):
    data = _cdtd_learning_state()
    return {
        feature: float(data[mode]["features"][feature].get("weight", 1.0))
        for feature in CDTD_VIP_FEATURES
    }


def _cdtd_rank(feature_scores, so_nv):
    # Mỗi tín hiệu tự đưa ra danh sách mạnh nhất; dùng để học sau khi có top1 thật.
    items = list(feature_scores.items())
    random.shuffle(items)
    items.sort(key=lambda item: item[1], reverse=True)
    return [nv for nv, _ in items[:so_nv]]


def _cdtd_update_learning(mode, feature_predictions, actual_top1):
    if mode not in ("winner", "not_winner"):
        return
    try:
        actual_top1 = int(actual_top1)
    except Exception:
        return

    with CDTD_LEARNING_LOCK:
        data = _cdtd_learning_state()
        changed = False
        for feature in CDTD_VIP_FEATURES:
            prediction = feature_predictions.get(feature)
            if not prediction:
                continue
            item = data[mode]["features"][feature]
            if mode == "winner":
                correct = actual_top1 in prediction
            else:
                correct = actual_top1 not in prediction

            samples = int(item.get("correct", 0) or 0) + int(item.get("wrong", 0) or 0) + 1
            if correct:
                item["correct"] = int(item.get("correct", 0) or 0) + 1
                step = max(0.006, min(0.025, 0.025 / (1.0 + samples / 25.0)))
                item["weight"] = float(item.get("weight", 1.0)) + step
            else:
                item["wrong"] = int(item.get("wrong", 0) or 0) + 1
                step = max(0.004, min(0.018, 0.018 / (1.0 + samples / 25.0)))
                item["weight"] = float(item.get("weight", 1.0)) - step

            item["weight"] = round(
                max(CDTD_LEARNING_MIN_WEIGHT,
                    min(CDTD_LEARNING_MAX_WEIGHT, item["weight"])),
                6
            )
            changed = True

        if changed:
            data["version"] = 1
            data["updated_at"] = datetime.now().isoformat()


def _cdtd_weighted_select(feature_scores, so_nv, weights, base_score):
    total_scores = {nv: float(base_score) for nv in range(1, 7)}
    for feature, scores in feature_scores.items():
        weight = float(weights.get(feature, 1.0))
        for nv, value in scores.items():
            total_scores[nv] += value * weight
    items = list(total_scores.items())
    random.shuffle(items)
    items.sort(key=lambda item: item[1], reverse=True)
    return [nv for nv, _ in items[:so_nv]]


def choose_vip_cdtd(history, so_nv):
    seq = _sprint_history_sequence(history)
    if not seq:
        choose_vip_cdtd.last_feature_predictions = {}
        return random.sample(range(1, 7), so_nv)
    try:
        so_nv = max(1, min(6, int(so_nv)))
    except Exception:
        so_nv = 1
    total = len(seq)
    fs = {name: {nv: 0.0 for nv in range(1, 7)} for name in CDTD_VIP_FEATURES}
    for nv in range(1, 7):
        wins = seq.count(nv)
        rate = wins / total
        fs["frequency"][nv] = (0.50 - rate) * 46
        delay = _sprint_delay(seq, nv)
        d = min(delay * 1.0, 16)
        if delay >= 25: d += 18
        elif delay >= 18: d += 14
        elif delay >= 12: d += 10
        elif delay >= 6: d += 5
        elif delay <= 1: d -= 6
        fs["delay"][nv] = d
        streak = _sprint_current_streak(seq, nv)
        fs["streak"][nv] = min(streak * 8.0, 28) if streak else 0.0
        fs["recent"][nv] = _sprint_weighted_recent_hits(seq, nv, limit=50, decay=0.92) * 4.2
        if len(seq) >= 2:
            fs["markov1"][nv] = _sprint_follow_probability(seq, seq[0], nv) * 42
        if len(seq) >= 3:
            a, b = seq[1], seq[0]
            total_pair = hit = 0
            for i in range(len(seq) - 2):
                if seq[i + 2] == a and seq[i + 1] == b:
                    total_pair += 1
                    if seq[i] == nv: hit += 1
            if total_pair: fs["markov2"][nv] = (hit / total_pair) * 58
        count10 = sum(1 for x in seq[:10] if x == nv)
        fs["last10"][nv] = 8 if count10 == 0 else 4 if count10 == 1 else -12 if count10 >= 4 else 0
        long_score = 0.0
        h100 = seq[:100]
        if h100:
            w100 = h100.count(nv); r100 = w100 / len(h100)
            long_score += r100 * 20
            if w100 >= 30: long_score += 10
            elif w100 >= 20: long_score += 6
            elif w100 == 0: long_score -= 8
        h200 = seq[:200]
        if h200:
            w200 = h200.count(nv); r200 = w200 / len(h200)
            long_score += r200 * 14
            if w200 >= 50: long_score += 12
            elif w200 >= 35: long_score += 8
        fs["long_history"][nv] = long_score
        avg_gap = _sprint_average_gap(seq, nv)
        if avg_gap:
            fs["cycle"][nv] = 10 if delay >= avg_gap * 1.45 else 5 if delay >= avg_gap else -5 if delay <= avg_gap * 0.6 else 0
        if len(seq) >= 2 and seq[0] == seq[1] == nv:
            fs["repeat"][nv] = 6
    weights = _cdtd_learning_weights("winner")
    selected = _cdtd_weighted_select(fs, so_nv, weights, 96.0)
    choose_vip_cdtd.last_feature_predictions = {f: _cdtd_rank(fs[f], so_nv) for f in CDTD_VIP_FEATURES}
    return selected

choose_vip_cdtd.last_feature_predictions = {}


def choose_not_winner_vip(history, so_nv):
    seq = _sprint_history_sequence(history)
    if not seq:
        choose_not_winner_vip.last_feature_predictions = {}
        return random.sample(range(1, 7), so_nv)
    try:
        so_nv = max(1, min(6, int(so_nv)))
    except Exception:
        so_nv = 1
    total = len(seq)
    fs = {name: {nv: 0.0 for nv in range(1, 7)} for name in CDTD_VIP_FEATURES}
    for nv in range(1, 7):
        wins = seq.count(nv); rate = wins / total
        fs["frequency"][nv] = (1 - rate) * 42
        delay = _sprint_delay(seq, nv)
        d = min(delay * 0.45, 8)
        if delay >= 25: d += 20
        elif delay >= 18: d += 16
        elif delay >= 12: d += 11
        elif delay >= 6: d += 6
        elif delay <= 1: d -= 12
        fs["delay"][nv] = d
        streak = _sprint_current_streak(seq, nv)
        if streak: fs["streak"][nv] = -min(streak * 9.0, 30)
        fs["recent"][nv] = -_sprint_weighted_recent_hits(seq, nv, limit=50, decay=0.92) * 5.5
        if len(seq) >= 2:
            fs["markov1"][nv] = -_sprint_follow_probability(seq, seq[0], nv) * 40
        if len(seq) >= 3:
            a, b = seq[1], seq[0]; total_pair = hit = 0
            for i in range(len(seq) - 2):
                if seq[i + 2] == a and seq[i + 1] == b:
                    total_pair += 1
                    if seq[i] == nv: hit += 1
            if total_pair: fs["markov2"][nv] = -(hit / total_pair) * 60
        count10 = sum(1 for x in seq[:10] if x == nv)
        fs["last10"][nv] = 10 if count10 == 0 else 5 if count10 == 1 else -15 if count10 >= 4 else 0
        long_score = 0.0
        h100 = seq[:100]
        if h100:
            w100 = h100.count(nv); r100 = w100 / len(h100)
            long_score += (1 - r100) * 26
            if w100 == 0: long_score += 12
            elif w100 <= 3: long_score += 7
            elif w100 >= 20: long_score -= 12
        h200 = seq[:200]
        if h200:
            w200 = h200.count(nv); r200 = w200 / len(h200)
            long_score += (1 - r200) * 16
            if w200 >= 45: long_score -= 14
        fs["long_history"][nv] = long_score
        avg_gap = _sprint_average_gap(seq, nv)
        if avg_gap:
            fs["cycle"][nv] = 8 if delay >= avg_gap * 1.5 else -6 if delay <= avg_gap * 0.7 else 0
        if len(seq) >= 2 and seq[0] == seq[1] == nv:
            fs["repeat"][nv] = -8
    weights = _cdtd_learning_weights("not_winner")
    selected = _cdtd_weighted_select(fs, so_nv, weights, 104.0)
    choose_not_winner_vip.last_feature_predictions = {f: _cdtd_rank(fs[f], so_nv) for f in CDTD_VIP_FEATURES}
    return selected

choose_not_winner_vip.last_feature_predictions = {}

class SprintGame:

    def __init__(self):
        self.session = requests.Session()
        self.headers = {}
        self.coin = ""
        self.bet_amount = 0
        self.he_so = 0
        self.type_bet = ""
        self.so_nv = 0
        self.logic_type = "free"
        self.target_profit = 0.0
        self.stop_loss = 0.0
        self.rest_after_lose = 0
        self.anti_soi_after = 0
        self.auto_bet = True

    def home(self, coin):
        params = {
            "asset": coin
        }

        while True:
            try:
                response = self.session.get(
                    "https://api.sprintrun.win/sprint/home",
                    params=params,
                    headers=self.headers,
                    timeout=10
                )

                return response.text

            except requests.exceptions.RequestException as e:
                cprints("ruby", f"⚠️ Lỗi kết nối API: {e}")
                cprints("yellow", "🔄 Đang kết nối lại...")
                time.sleep(2)

    def info(self, ki, coin):
        while True:
            try:
                params = {
                    "issue": str(ki),
                    "asset": coin,
                }

                response = self.session.get(
                    "https://api.sprintrun.win/sprint/issue_result",
                    params=params,
                    headers=self.headers,
                    timeout=10
                )

                return json.loads(response.text)

            except Exception as e:
                cprints("ruby", f"⚠️ Lỗi lấy kết quả: {e}")
                time.sleep(2)

    def bet(self, ki, kq, coin, bet_amount, type_bet):
        try:
            json_data = {
                "issue_id": int(ki),
                "bet_group": type_bet,
                "asset_type": coin,
                "athlete_id": kq,
                "bet_amount": bet_amount,
            }

            response = self.session.post(
                "https://api.sprintrun.win/sprint/bet",
                headers=self.headers,
                json=json_data,
                timeout=10
            )

            res = json.loads(response.text)

            if res.get("code") == 0:
                return True

        except Exception as e:
            cprints("ruby", f"❌ Lỗi đặt cược {coin}: {e}")

        return False

    def random_result(self, so_nguoi):
        li = [1, 2, 3, 4, 5, 6]
        kq = []

        for _ in range(int(so_nguoi)):
            x = random.choice(li)
            kq.append(x)
            li.remove(x)

        return kq

    def check_result(self, coin, bot_chon, type_game):
        try:
            res = json.loads(self.home(coin))
        except Exception as e:
            cprints("ruby", f"❌ Lỗi lấy dữ liệu trận đấu: {e}")
            return None

        try:
            ki = res["data"]["issue_id"]
        except Exception:
            cprints("ruby", "❌ Không lấy được mã ván đấu")
            return None

        while True:
            try:
                res = json.loads(self.home(coin))
                raw_sec = int(res.get("data", {}).get("expire_seconds", 0))
                expire_sec = max(0, raw_sec - 1)
                CDTD_UI_STATE.update({"issue_id": ki, "countdown": expire_sec, "status": "CHỜ KẾT QUẢ", "selected": list(bot_chon)})
                _cdtd_ui_refresh()
                if expire_sec <= 1:
                    break
                time.sleep(1)
            except Exception as e:
                cprints("ruby", f"⚠️ Lỗi đếm thời gian: {e}")
                time.sleep(2)

        CDTD_UI_STATE.update({"countdown": None, "status": "ĐANG LẤY KẾT QUẢ"})
        _cdtd_ui_refresh()
        time.sleep(8)
        re_end = self.info(ki, coin)

        try:
            rank = [int(x) for x in re_end["data"]["athlete_rank"]]
            top1 = rank[0]
            award = re_end["data"]["my_total_award"]
            won = top1 in bot_chon if type_game == "winner" else top1 not in bot_chon
            CDTD_UI_STATE.update({"issue_id": re_end["data"].get("issue_id", ki), "winner": top1, "award": float(award or 0), "countdown": None, "status": "THẮNG" if won else "THUA", "result": "Thắng" if won else "Thua", "selected": list(bot_chon)})
            _cdtd_ui_refresh()

            return {
                "issue_id": re_end["data"]["issue_id"],
                "top1": top1,
                "my_total_bet": re_end["data"]["my_total_bet"],
                "my_total_award": re_end["data"]["my_total_award"],
                "kq": top1 in bot_chon if type_game == "winner" else top1 not in bot_chon,
                "bot_chon": bot_chon,
                "learning_mode": (getattr(self, "_cdtd_pending_learning", {}) or {}).get("mode"),
                "learning_features": (getattr(self, "_cdtd_pending_learning", {}) or {}).get("features", {}),
            }

        except Exception as e:
            cprints("ruby", f"❌ Lỗi xử lý kết quả: {e}")
            return None

    def vanchoi(self, coin, history, he_so, bet_amount0, type_bet, so_nv):

        if self.logic_type == "vip":
            try:
                is_valid, msg, is_vip = check_activation_valid()

                if not is_vip:
                    cprints("ruby", "❌ Key FREE không được sử dụng Logic VIP!")
                    self.logic_type = "free"

            except Exception:
                self.logic_type = "free"

        try:
            res = json.loads(self.home(coin))
            ki = res["data"]["issue_id"]

        except Exception as e:
            cprints("ruby", f"❌ Lỗi lấy ván hiện tại: {e}")
            return None

        analysis_time = 10
        CDTD_UI_STATE.update({"issue_id": ki, "coin": coin, "type_bet": type_bet, "logic_type": self.logic_type, "selected": [], "winner": None, "award": 0.0, "result": "—", "status": "ĐANG PHÂN TÍCH", "_start_countdown": None})
        _cdtd_ui_refresh()

        while True:
            try:
                timer = json.loads(self.home(coin))
                expire = int(timer.get("data", {}).get("expire_seconds", 0))
                CDTD_UI_STATE.update({"countdown": expire, "status": "ĐANG PHÂN TÍCH"})
                _cdtd_ui_refresh()
                if expire <= analysis_time:
                    break
                time.sleep(1)
            except Exception as e:
                cprints("ruby", f"⚠️ Lỗi đếm giờ: {e}")
                time.sleep(2)

        if type_bet == "winner":
            if self.logic_type == "free":
                bot_chon = choose_free_cdtd(history, int(so_nv))
            elif self.logic_type == "vip":
                bot_chon = choose_vip_cdtd(history, int(so_nv))
            else:
                bot_chon = self.random_result(int(so_nv))

        elif type_bet == "not_winner":
            if self.logic_type == "free":
                bot_chon = choose_not_winner_free(history, int(so_nv))
            elif self.logic_type == "vip":
                bot_chon = choose_not_winner_vip(history, int(so_nv))
            else:
                bot_chon = self.random_result(int(so_nv))
        else:
            bot_chon = self.random_result(int(so_nv))

        ten_nv = [NV.get(i, str(i)) for i in bot_chon]

        CDTD_UI_STATE.update({"selected": list(bot_chon), "status": "ĐÃ PHÂN TÍCH", "countdown": None})
        _cdtd_ui_refresh()

        # Chụp lại dự đoán của từng tín hiệu VIP trước khi sang ván mới.
        # Khi có top1 thật, lớp tự học sẽ chấm từng tín hiệu và điều chỉnh trọng số.
        self._cdtd_pending_learning = None
        if self.logic_type == "vip":
            try:
                if type_bet == "winner":
                    feature_predictions = dict(getattr(choose_vip_cdtd, "last_feature_predictions", {}) or {})
                elif type_bet == "not_winner":
                    feature_predictions = dict(getattr(choose_not_winner_vip, "last_feature_predictions", {}) or {})
                else:
                    feature_predictions = {}
                self._cdtd_pending_learning = {
                    "mode": type_bet,
                    "features": feature_predictions,
                }
            except Exception:
                self._cdtd_pending_learning = None

        bet_amount = bet_amount0 / len(bot_chon)

        if len(history) > 0 and history[0]["kq"] is False:
            bet_amount = (
                history[0]["my_total_bet"] * he_so
            ) / len(bot_chon)

        CDTD_UI_STATE["bet_amount"] = float((bet_amount * max(1, len(bot_chon))) or 0)
        _cdtd_ui_refresh()

        if self.auto_bet:
            # Ghi ngay vào lịch sử khi bắt đầu gửi cược, giống Vua Thoát Hiểm:
            # dòng này sẽ hiển thị "⏳ Đang cược" và được thay thế bằng kết quả thật sau ván.
            try:
                pending_record = {
                    "issue_id": int(ki),
                    "bot_chon": list(bot_chon),
                    "selected": list(bot_chon),
                    "top1": None,
                    "my_total_bet": float(bet_amount * len(bot_chon)),
                    "my_total_award": 0.0,
                    "kq": None,
                    "status": "ĐANG CƯỢC",
                    "logic_type": self.logic_type,
                    "_pending_cdtd": True,
                }
                history[:] = [h for h in history if not (isinstance(h, dict) and h.get("_pending_cdtd") and str(h.get("issue_id")) == str(ki))]
                history.insert(0, pending_record)
                CDTD_UI_STATE.update({
                    "issue_id": ki,
                    "selected": list(bot_chon),
                    "history": list(history),
                    "status": "ĐANG CƯỢC",
                })
                _cdtd_ui_refresh()
            except Exception as e:
                log_debug(f"CDTD pending history error: {e}")

            while True:
                try:
                    timer = json.loads(self.home(coin))
                    expire = int(timer.get("data", {}).get("expire_seconds", 0))
                    CDTD_UI_STATE.update({"countdown": expire, "status": "CHỜ ĐẶT CƯỢC"})
                    _cdtd_ui_refresh()
                    if expire <= 10:
                        break
                    time.sleep(1)
                except Exception as e:
                    cprints("ruby", f"⚠️ Lỗi đếm giờ: {e}")
                    time.sleep(2)

            try:
                res = json.loads(self.home(coin))
                ki = res["data"]["issue_id"]
            except Exception:
                ki = ki

            CDTD_UI_STATE.update({"status": "ĐANG CƯỢC", "countdown": 10})
            _cdtd_ui_refresh()
            placed_count = 0
            for i in bot_chon:
                try:
                    if self.bet(ki, i, coin, bet_amount, type_bet):
                        placed_count += 1
                except Exception as e:
                    log_debug(f"CDTD place bet error P{i}: {e}")

            # Cập nhật chính dòng lịch sử vừa tạo, không tạo thêm một dòng mới.
            try:
                for item in history:
                    if isinstance(item, dict) and item.get("_pending_cdtd") and str(item.get("issue_id")) == str(ki):
                        item["status"] = "ĐÃ ĐẶT CƯỢC" if placed_count > 0 else "CƯỢC THẤT BẠI"
                        item["my_total_bet"] = float(bet_amount * max(1, placed_count if placed_count else len(bot_chon)))
                        break
            except Exception as e:
                log_debug(f"CDTD pending history update error: {e}")

            CDTD_UI_STATE.update({
                "status": "ĐÃ ĐẶT CƯỢC" if placed_count > 0 else "CƯỢC THẤT BẠI",
                "countdown": None,
                "history": list(history),
            })
            _cdtd_ui_refresh()

        return self.check_result(
            coin,
            bot_chon,
            type_bet,
        )
        
    def user_asset(self):
        while True:
            try:
                json_data = {
                    "user_id": int(self.headers["user-id"]),
                    "source": "home",
                }

                response = self.session.post(
                    "https://wallet.3games.io/api/wallet/user_asset",
                    headers=self.headers,
                    json=json_data,
                    timeout=10,
                )

                res = json.loads(response.text)

                asset = {
                    "USDT": res["data"]["user_asset"]["USDT"],
                    "WORLD": res["data"]["user_asset"]["WORLD"],
                    "BUILD": res["data"]["user_asset"]["BUILD"],
                }

                return asset

            except requests.exceptions.RequestException as e:
                cprints("ruby", f"⚠️ Lỗi kết nối lấy số dư: {e}")
                cprints("yellow", "🔄 Đang thử lấy lại số dư...")
                time.sleep(2)

            except Exception as e:
                cprints("ruby", f"❌ Lỗi khi lấy số dư: {e}")
                time.sleep(2)

def _read_float_input(prompt: str, default: float = 0.0) -> float:
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return default
        try:
            return float(raw)
        except ValueError:
            cprints("ruby", "❌ Giá trị không hợp lệ, vui lòng nhập số.")

def _read_int_input(prompt: str, default: int = 0):
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return default
        try:
            return int(raw)
        except ValueError:
            cprints("ruby", "❌ Giá trị không hợp lệ, vui lòng nhập số nguyên.")

def _fmt_cdtd_number(value: Any, decimals: int = 6) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "0"
    text = f"{num:.{decimals}f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"

def _cdtd_capital_stop_reason(game, current_balance) -> tuple[bool, str]:
    try:
        current_balance = float(current_balance)
    except (TypeError, ValueError):
        return False, ""

    target_balance = float(getattr(game, "target_profit", 0.0) or 0.0)
    stop_balance = float(getattr(game, "stop_loss", 0.0) or 0.0)
    coin = str(getattr(game, "coin", "BUILD") or "BUILD")

    if target_balance > 0 and current_balance >= target_balance:
        return True, (
            f"🎉Đã đạt mục tiêu lãi ({_fmt_cdtd_number(current_balance)} {coin}). Dừng tool."
        )

    if stop_balance > 0 and current_balance <= stop_balance:
        return True, (
            f"💀Đã chạm cắt lỗ ({_fmt_cdtd_number(current_balance)} {coin}). Dừng tool."
        )

    return False, ""

def _chon_auto_cuoc_cdtd(game):
    """Cho phép bật/tắt tự động đặt cược cho Chạy Đua Tốc Độ."""
    while True:
        x = input("9. Bật auto cược? (y/n): ").strip().lower()
        if x in ("y", "yes"):
            game.auto_bet = True
            cprints("bright_green", "✅ Đã mở Auto cược.")
            return game
        if x in ("n", "no"):
            game.auto_bet = False
            cprints("gold", "⏸️ Đã tắt Auto cược.")
            return game
        cprints("ruby", "❌ Vui lòng nhập y để bật hoặc n để tắt.")

def _luu_auto_cuoc_cdtd(game):
    """Cập nhật lựa chọn auto cược vào config hiện tại, nếu file config tồn tại."""
    try:
        path = "config-cdtd.txt"
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["auto_bet"] = bool(getattr(game, "auto_bet", True))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def cauhinh_game(game):
    str_coin = """
╭──────────────────────────────╮
│      💰 CHỌN LOẠI TIỀN       │
╰──────────────────────────────╯

  [1] USDT
  [2] BUILD
  [3] WORLD
"""

    cprints("bright_green", str_coin)

    # ==========================
    # CHỌN LOẠI TIỀN
    # ==========================

    while True:
        cprints(
            "white",
            "👉 Nhập loại tiền bạn muốn chơi [1/2/3]:",
            end=" ",
        )

        x = input().strip()

        if x in ("1", "2", "3"):
            game.coin = {
                "1": "USDT",
                "2": "BUILD",
                "3": "WORLD",
            }[x]

            cprints(
                "bright_green",
                f"✅ Đã chọn loại tiền: {game.coin}",
            )
            break

        cprints(
            "ruby",
            "❌ Lựa chọn không hợp lệ, vui lòng nhập 1, 2 hoặc 3.",
        )

    # ==========================
    # CÀI ĐẶT TIỀN CƯỢC
    # ==========================

    while True:
        game.bet_amount = _read_float_input(
            f"1. Nhập số {game.coin} cược mỗi ván: ",
            0.0,
        )

        if game.bet_amount > 0:
            break

        cprints(
            "ruby",
            "❌ Tiền cược phải lớn hơn 0.",
        )

    while True:
        game.he_so = _read_float_input(
            "2. Nhập hệ số cược sau thua: ",
            1.0,
        )

        if game.he_so >= 1:
            break

        cprints(
            "ruby",
            "❌ Hệ số cược phải lớn hơn hoặc bằng 1.",
        )

    # ==========================
    # CHỌN LOẠI ĐẶT
    # ==========================

    cprints(
        "gold",
        """
==============================
      CHỌN LOẠI ĐẶT
==============================
1. 🏆 Ai là quán quân
2. 🚫 Ai không là quán quân
==============================
""",
    )

    while True:
        type_bet = input("3. Chọn loại đặt [1/2]: ").strip()

        if type_bet == "1":
            game.type_bet = "winner"

            cprints(
                "bright_green",
                "✅ Đã chọn: Ai là quán quân",
            )
            break

        if type_bet == "2":
            game.type_bet = "not_winner"

            cprints(
                "bright_green",
                "✅ Đã chọn: Ai không là quán quân",
            )
            break

        cprints(
            "ruby",
            "❌ Vui lòng chỉ nhập 1 hoặc 2.",
        )

    # ==========================
    # CHỌN SỐ NHÂN VẬT
    # ==========================

    console.print(
        f"[bold {VBTOOL_COLORS['white']}]"
        f"4. Đặt vào bao nhiêu người:"
        f"[/bold {VBTOOL_COLORS['white']}]",
        end=" ",
    )

    while True:
        game.so_nv = _read_int_input("", 1)

        if game.so_nv >= 1:
            break

        cprints(
            "ruby",
            "❌ Số người đặt phải lớn hơn hoặc bằng 1.",
        )

    # ==========================
    # QUẢN LÝ VỐN
    # ==========================

    cprints(
        "gold",
        """
==============================
     CÀI ĐẶT QUẢN LÝ VỐN
==============================
""",
    )

    game.target_profit = _read_float_input(
        "5. Mục tiêu lãi: Nhập số BUILD muốn đặt để dừng (Enter = tắt): ",
        0.0,
    )

    game.stop_loss = _read_float_input(
        "6. Cắt lỗ: Nhập số BUILD còn lại để dừng (Enter = tắt): ",
        0.0,
    )

    game.rest_after_lose = _read_int_input(
        "7. Nghỉ sau khi thua: Nghỉ bao nhiêu ván? (0 = Tắt): ",
        0,
    )

    game.anti_soi_after = _read_int_input(
        "8. Chống soi: Nghỉ 1 ván sau bao nhiêu ván cược? (0 = Tắt): ",
        0,
    )

    # Không cho các giá trị quản lý vốn bị âm
    game.target_profit = max(0.0, float(game.target_profit))
    game.stop_loss = max(0.0, float(game.stop_loss))
    game.rest_after_lose = max(0, int(game.rest_after_lose))
    game.anti_soi_after = max(0, int(game.anti_soi_after))

    # ==========================
    # LƯU CẤU HÌNH
    # ==========================

    json_config = {
        "Coin": game.coin,
        "he_so": game.he_so,
        "bet_amount0": game.bet_amount,
        "type_bet": game.type_bet,
        "So_nv": game.so_nv,
        "target_profit": game.target_profit,
        "stop_loss": game.stop_loss,
        "rest_after_lose": game.rest_after_lose,
        "anti_soi_after": game.anti_soi_after,
        "auto_bet": bool(getattr(game, "auto_bet", True)),
    }

    try:
        with open(
            "config-cdtd.txt",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                json_config,
                f,
                indent=4,
                ensure_ascii=False,
            )

        cprints(
            "bright_green",
            "✅ Đã lưu cấu hình.",
        )

    except OSError as e:
        cprints(
            "ruby",
            f"❌ Không thể lưu cấu hình: {e}",
        )

    return game

def main_cdtd():
    start_key_expiry_monitor()
    if not check_activation_valid()[0]:
        console.print("[bold red]❌ Key của bạn không còn hiệu lực.[/bold red]")
        time.sleep(2)
        return

    console.clear()
    console.print(show_ultimate_header())

    am = AccountManager()

    console.print(
        Panel(
            "📋 THÊM TÀI KHOẢN CHẠY ĐUA TỐC ĐỘ",
            title="CHẠY ĐUA TỐC ĐỘ",
            border_style=VBTOOL_COLORS["history_blue"],
            box=box.ROUNDED,
        )
    )

    user_id = None
    secret_key = None

    def format_number(value, max_decimal=10):
        try:
            value = float(value)

            if abs(value) < 1e-12:
                value = 0.0

            text = f"{value:.{max_decimal}f}".rstrip("0").rstrip(".")

            if text in ("", "-0"):
                return "0"

            return text

        except (TypeError, ValueError):
            return "0"

    def get_coin_balance(asset_data, coin_name):
        try:
            coin_name = str(coin_name).upper()
            return float(asset_data.get(coin_name, 0) or 0)

        except (TypeError, ValueError, AttributeError):
            return 0.0

    if os.path.exists("data-cdtd.txt"):
        cprints(
            "white",
            " Bạn có muốn sử dụng lại tài khoản đã lưu không? (y/n): ",
            end="",
        )

        x = input().strip().lower()

        if x != "n":
            try:
                with open("data-cdtd.txt", "r", encoding="utf-8") as f:
                    re_acc = json.load(f)

                user_id = str(
                    re_acc.get("user-id") or ""
                ).strip()

                secret_key = str(
                    re_acc.get("user-secret-key") or ""
                ).strip()

            except Exception:
                user_id = None
                secret_key = None

                cprints(
                    "ruby",
                    "❌ Không thể đọc tài khoản đã lưu.",
                )

    if not user_id or not secret_key:
        try:
            selected_account = am.add_account()

            if not selected_account:
                cprints(
                    "ruby",
                    "❌ Không nhận được thông tin tài khoản.",
                )
                return

            user_id = str(
                selected_account.get("user-id") or ""
            ).strip()

            secret_key = str(
                selected_account.get("user-secret-key") or ""
            ).strip()

            if not user_id or not secret_key:
                cprints(
                    "ruby",
                    "❌ Tài khoản thiếu user-id hoặc user-secret-key.",
                )
                return

            with open("data-cdtd.txt", "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "user-id": user_id,
                        "user-secret-key": secret_key,
                    },
                    f,
                    indent=4,
                    ensure_ascii=False,
                )

        except KeyboardInterrupt:
            return

        except Exception as e:
            cprints(
                "ruby",
                f"❌ Lỗi thêm tài khoản: {e}",
            )
            return

    game = SprintGame()

    game.headers = {
        "accept": "*/*",
        "accept-language": "vi,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://sprintrun.win",
        "user-agent": (
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/141.0.0.0 Mobile Safari/537.36"
        ),
        "user-id": str(user_id),
        "user-login": "login_v2",
        "user-secret-key": secret_key,
    }

    if os.path.exists("config-cdtd.txt"):
        cprints(
            "white",
            " Bạn có muốn sử dụng lại cấu hình đã lưu không? (y/n): ",
            end="",
        )

        x = input().strip().lower()

        if x == "n":
            game = cauhinh_game(game)

        else:
            try:
                with open(
                    "config-cdtd.txt",
                    "r",
                    encoding="utf-8",
                ) as f:
                    config = json.load(f)

                game.coin = config.get("Coin", "USDT")
                game.bet_amount = float(
                    config.get("bet_amount0", 0)
                )
                game.he_so = float(
                    config.get("he_so", 1)
                )
                game.type_bet = config.get(
                    "type_bet",
                    "winner",
                )
                game.so_nv = int(
                    config.get("So_nv", 1)
                )
                game.target_profit = float(
                    config.get("target_profit", 0.0) or 0.0
                )
                game.stop_loss = float(
                    config.get("stop_loss", 0.0) or 0.0
                )
                game.rest_after_lose = int(
                    config.get("rest_after_lose", 0) or 0
                )
                game.anti_soi_after = int(
                    config.get("anti_soi_after", 0) or 0
                )
                game.auto_bet = bool(config.get("auto_bet", True))

            except Exception as e:
                cprints(
                    "ruby",
                    f"❌ Cấu hình bị lỗi: {e}",
                )

                game = cauhinh_game(game)

    else:
        game = cauhinh_game(game)

    game.target_profit = float(
        getattr(game, "target_profit", 0.0) or 0.0
    )

    game.stop_loss = float(
        getattr(game, "stop_loss", 0.0) or 0.0
    )

    game.rest_after_lose = int(
        getattr(game, "rest_after_lose", 0) or 0
    )

    game.anti_soi_after = int(
        getattr(game, "anti_soi_after", 0) or 0
    )

    game.auto_bet = bool(getattr(game, "auto_bet", True))

    game.coin = str(
        getattr(game, "coin", "USDT") or "USDT"
    ).upper()

    # Cho phép bật/tắt auto cược ở mỗi lần chạy tool, không phụ thuộc cấu hình cũ.
    _chon_auto_cuoc_cdtd(game)
    _luu_auto_cuoc_cdtd(game)

    console.clear()
    console.print(show_ultimate_header())

    is_valid, msg, is_vip = check_activation_valid()

    cprints(
        "gold",
        """
==============================
          CHỌN LOGIC
==============================
1. FREE
2. VIP
==============================
""",
    )

    while True:
        choice = input("👉 Nhập lựa chọn (1/2): ").strip()

        if choice == "1":
            game.logic_type = "free"

            cprints(
                "bright_green",
                "✅ Đã chọn Logic FREE",
            )
            break

        elif choice == "2":
            if is_vip:
                game.logic_type = "vip"

                cprints(
                    "gold",
                    "👑 Đã chọn Logic VIP",
                )
                break

            else:
                cprints(
                    "ruby",
                    "❌ Key FREE không được sử dụng Logic VIP!",
                )

        else:
            cprints(
                "ruby",
                "❌ Lựa chọn không hợp lệ!",
            )

    stats = {
        "win": 0,
        "lose": 0,
        "win_streak": 0,
        "max_win_streak": 0,
        "lose_streak": 0,
        "max_lose_streak": 0,
        "earn": 0.0,
    }

    history = []
    bet_round_count = 0
    skip_rounds = 0

    start_balance = None
    current_balance = 0.0
    cumulative_round_profit = 0.0

    global CDTD_LIVE
    CDTD_UI_STATE.update({
        "user_id": str(user_id),
        "coin": game.coin,
        "type_bet": game.type_bet,
        "logic_type": game.logic_type,
        "key_type": "VIP" if is_vip else "FREE",
        "auto_bet": bool(game.auto_bet),
        "stats": dict(stats),
        "history": list(history),
        "status": "CHỜ KẾT NỐI",
        "selected": [],
        "winner": None,
        "award": 0.0,
        "result": "—",
        "bet_amount": float(getattr(game, "bet_amount", 0) or 0),
    })
    CDTD_LIVE = Live(make_cdtd_vth_layout(CDTD_UI_STATE), refresh_per_second=8, console=console, screen=True)
    CDTD_LIVE.start()
    _cdtd_ui_refresh()

    while True:
        if not check_activation_valid(exit_on_expired=False)[0]:
            CDTD_UI_STATE["status"] = "KEY HẾT HẠN"
            _cdtd_ui_refresh()
            time.sleep(1)
            _cdtd_ui_stop()
            return

        if skip_rounds > 0:
            CDTD_UI_STATE["status"] = f"TẠM NGHỈ • CÒN {skip_rounds} VÁN"
            CDTD_UI_STATE["countdown"] = None
            _cdtd_ui_refresh()
            skip_rounds -= 1
            time.sleep(3)
            continue

        try:
            asset = game.user_asset()

            if not isinstance(asset, dict):
                cprints(
                    "ruby",
                    "❌ Không lấy được dữ liệu số dư.",
                )

                time.sleep(3)
                continue

        except Exception as e:
            cprints(
                "ruby",
                f"❌ Lỗi cập nhật số dư: {e}",
            )

            time.sleep(3)
            continue

        current_balance = get_coin_balance(
            asset,
            game.coin,
        )

        if start_balance is None:
            start_balance = current_balance

        wallet_profit = current_balance - start_balance
        stats["earn"] = cumulative_round_profit

        CDTD_UI_STATE.update({
            "user_id": str(user_id),
            "coin": game.coin,
            "balances": {
                "USDT": get_coin_balance(asset, "USDT"),
                "WORLD": get_coin_balance(asset, "WORLD"),
                "BUILD": get_coin_balance(asset, "BUILD"),
            },
            "status": "ĐANG PHÂN TÍCH",
            "profit": float(cumulative_round_profit),
            "type_bet": game.type_bet,
            "logic_type": game.logic_type,
            "stats": dict(stats),
            "history": list(history),
            "auto_bet": bool(game.auto_bet),
            "key_type": "VIP" if is_vip else "FREE",
            "bet_amount": float(getattr(game, "bet_amount", 0) or 0),
        })
        _cdtd_ui_refresh()

        should_stop, stop_reason = _cdtd_capital_stop_reason(game, current_balance)
        if should_stop:
            CDTD_UI_STATE["status"] = "DỪNG THEO MỤC TIÊU"
            _cdtd_ui_refresh()
            time.sleep(2)
            _cdtd_ui_stop()
            return

        try:
            res = game.vanchoi(
                game.coin,
                history,
                game.he_so,
                game.bet_amount,
                game.type_bet,
                game.so_nv,
            )

        except KeyboardInterrupt:
            _cdtd_ui_stop()
            cprints("red", "Thoát...")
            return

        except Exception as e:
            cprints(
                "ruby",
                f"❌ Lỗi chạy ván: {e}",
            )

            time.sleep(3)
            continue

        if res is None:
            time.sleep(1)
            continue

        # ================== CẬP NHẬT TỰ HỌC VIP ==================
        if res.get("learning_mode") == "winner" and res.get("learning_features"):
            try:
                _cdtd_update_learning("winner", res.get("learning_features", {}), res.get("top1"))
            except Exception as e:
                log_debug(f"CDTD winner learning update error: {e}")
        elif res.get("learning_mode") == "not_winner" and res.get("learning_features"):
            try:
                _cdtd_update_learning("not_winner", res.get("learning_features", {}), res.get("top1"))
            except Exception as e:
                log_debug(f"CDTD not_winner learning update error: {e}")

        # Nếu đã có dòng "ĐANG CƯỢC", cập nhật đúng dòng đó thành kết quả;
        # không chèn thêm dòng trùng ván trong lịch sử.
        pending_updated = False
        try:
            result_issue = str(res.get("issue_id"))
            for idx, item in enumerate(history):
                if isinstance(item, dict) and item.get("_pending_cdtd") and str(item.get("issue_id")) == result_issue:
                    new_record = dict(res)
                    new_record.pop("_pending_cdtd", None)
                    new_record["status"] = "THẮNG" if res.get("kq") else "THUA"
                    history[idx] = new_record
                    pending_updated = True
                    break
        except Exception as e:
            log_debug(f"CDTD finalize history error: {e}")

        if not pending_updated:
            history.insert(0, res)

        CDTD_UI_STATE.update({"issue_id": res.get("issue_id"), "selected": list(res.get("bot_chon") or []), "winner": res.get("top1"), "result": "Thắng" if res.get("kq") else "Thua", "status": "THẮNG" if res.get("kq") else "THUA", "award": float(res.get("my_total_award") or 0), "history": list(history), "countdown": None})
        _cdtd_ui_refresh()

        if len(history) > 500:
            history = history[:500]

        try:
            round_bet = float(res.get("my_total_bet") or 0.0)
            round_award = float(res.get("my_total_award") or 0.0)
            cumulative_round_profit += (round_award - round_bet)
            stats["earn"] = cumulative_round_profit
        except Exception:
            pass

        # Lấy lại SỐ DƯ THỰC TẾ sau mỗi ván để kiểm tra mục tiêu/cắt lỗ.
        try:
            asset_after_round = game.user_asset()
            balance_after_round = get_coin_balance(asset_after_round, game.coin)
        except Exception:
            balance_after_round = None

        if balance_after_round is not None:
            should_stop, stop_reason = _cdtd_capital_stop_reason(game, balance_after_round)
            if should_stop:
                is_target_stop = (
                    float(getattr(game, "target_profit", 0.0) or 0.0) > 0
                    and float(balance_after_round) >= float(getattr(game, "target_profit", 0.0) or 0.0)
                )
                CDTD_UI_STATE["status"] = "ĐẠT MỤC TIÊU" if is_target_stop else "CHẠM CẮT LỖ"
                if balance_after_round is not None:
                    try:
                        CDTD_UI_STATE["balances"][game.coin] = float(balance_after_round)
                    except Exception:
                        pass
                _cdtd_ui_refresh()
                time.sleep(2)
                _cdtd_ui_stop()
                return

        bet_round_count += 1

        if res.get("kq"):
            stats["win"] += 1
            stats["win_streak"] += 1
            stats["lose_streak"] = 0

            stats["max_win_streak"] = max(
                stats["max_win_streak"],
                stats["win_streak"],
            )

        else:
            stats["lose"] += 1
            stats["lose_streak"] += 1
            stats["win_streak"] = 0

            stats["max_lose_streak"] = max(
                stats["max_lose_streak"],
                stats["lose_streak"],
            )

        CDTD_UI_STATE["stats"] = dict(stats)
        CDTD_UI_STATE["profit"] = float(cumulative_round_profit)
        CDTD_UI_STATE["history"] = list(history)
        CDTD_UI_STATE["winner"] = res.get("top1")
        CDTD_UI_STATE["selected"] = list(res.get("bot_chon") or [])
        CDTD_UI_STATE["award"] = float(res.get("my_total_award") or 0)
        CDTD_UI_STATE["status"] = "THẮNG" if res.get("kq") else "THUA"
        if balance_after_round is not None:
            try:
                CDTD_UI_STATE["balances"][game.coin] = float(balance_after_round)
            except Exception:
                pass
        _cdtd_ui_refresh()

        if (
            game.rest_after_lose > 0
            and stats["lose_streak"] >= game.rest_after_lose
        ):
            CDTD_UI_STATE["status"] = f"THUA LIÊN TIẾP {stats['lose_streak']} VÁN • NGHỈ 1 VÁN"
            _cdtd_ui_refresh()
            stats["lose_streak"] = 0
            skip_rounds = max(skip_rounds, 1)

        if (
            game.anti_soi_after > 0
            and bet_round_count % game.anti_soi_after == 0
        ):
            CDTD_UI_STATE["status"] = f"CHỐNG SOI • ĐÃ ĐẶT {bet_round_count} VÁN • NGHỈ 1 VÁN"
            _cdtd_ui_refresh()
            skip_rounds = max(skip_rounds, 1)

        time.sleep(3)
        CDTD_UI_STATE["status"] = "CHỜ VÁN MỚI"
        CDTD_UI_STATE["countdown"] = None
        _cdtd_ui_refresh()

# ================== TOOL 4: CANH CODE XWORLD ==================

XW_API_DETAIL = "https://web3task.3games.io/v1/task/redcode/detail"
XW_API_EXCHANGE = "https://web3task.3games.io/v1/task/redcode/exchange"
XW_API_ASSET = "https://wallet.3games.io/api/wallet/user_asset"

XW_HEADERS = {
    "accept": "*/*",
    "accept-language": "vi,en;q=0.9",
    "content-type": "application/json",
    "country-code": "vn",
    "origin": "https://xworld.info",
    "referer": "https://xworld.info/",
    "user-agent": (
        "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 "
        "Mobile Safari/537.36"
    ),
    "language": "vi-VN",
}

XW_MAX_RETRIES = 3
XW_LOG_FILE = "history_nhap_code.log"
XW_ACCOUNT_FILE = "data_xw_confirm_code.txt"

def xw_clear_screen() -> None:
    os.system("cls" if platform.system() == "Windows" else "clear")

def xw_rgb_print(r: int, g: int, b: int, text: object, end: str = "\n") -> None:
    print(f"\033[38;2;{r};{g};{b}m{text}\033[0m", end=end)

def xw_translate_message(message: object) -> str:
    """
    Dịch các thông báo lỗi/trạng thái phổ biến từ tiếng Anh/Trung sang tiếng Việt
    để CANH CODE XWORLD luôn hiển thị thông báo thuần Việt.
    """
    text = str(message or "").strip()
    if not text:
        return "Không xác định"

    lower = text.lower()

    rules = [
        (("success", "successful", "ok", "成功", "succeeded"), "Thành công"),
        (("already received", "already claimed", "already", "received", "đã nhận", "领取", "已领取", "已領取"), "Mã code này đã được nhận rồi"),
        (("out of", "not exist", "no exist", "not found", "empty", "hết", "không còn", "不存在", "无效", "已失效"), "Mã code đã hết hoặc không còn khả dụng"),
        (("limit", "max", "exceed", "giới hạn", "上限", "达到上限", "已达上限"), "Đã đạt giới hạn tài khoản"),
        (("expired", "hết hạn", "过期", "已过期"), "Đã hết hạn"),
        (("invalid", "không hợp lệ", "无效"), "Không hợp lệ"),
        (("network", "connect", "timeout", "timed out", "connection", "socket", "mạng", "网络", "连接"), "Lỗi kết nối mạng"),
        (("forbidden", "unauthorized", "unauth", "permission", "权限", "被拒绝"), "Không có quyền truy cập"),
        (("error", "failed", "failure", "lỗi", "失败"), "Đã xảy ra lỗi"),
    ]

    for keywords, vn in rules:
        if any(k in lower for k in keywords):
            return vn

    # Nếu thông báo còn lại có ký tự Latin hoặc CJK thì ẩn nội dung gốc
    if re.search(r"[A-Za-z一-鿿]", text):
        return "Thông báo không xác định từ máy chủ"

    return text

def xw_get_real_len(text: object):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return len(ansi_escape.sub("", str(text)))

def xw_print_banner() -> None:
    
    xw_clear_screen()
    console.print(show_ultimate_header())

def xw_print_square_table(title: str, headers: list[str], rows: list[list[object]]) -> None:
    normalized = [[str(cell) for cell in row] for row in rows]
    widths = []

    for i, header in enumerate(headers):
        values = [xw_get_real_len(row[i]) for row in normalized if i < len(row)]
        widths.append(max([xw_get_real_len(header), *values]) + 2)

    def border(left: str, middle: str, right: str) -> str:
        return left + middle.join("─" * (w + 2) for w in widths) + right

    total_width = sum(widths) + 3 * len(widths) + 1
    title_pad = max(0, total_width - xw_get_real_len(title) - 4)
    print(f"┌─ {title} {'─' * title_pad}┐")
    print(border("├", "┬", "┤"))

    header_str = "│ " + " │ ".join(
        str(h).center(widths[i]) for i, h in enumerate(headers)
    ) + " │"
    print(Fore.CYAN + header_str + Style.RESET_ALL)
    print(border("├", "┼", "┤"))

    for row in normalized:
        padded = []
        for i, cell in enumerate(row):
            pad = widths[i] - xw_get_real_len(cell)
            padded.append(cell + " " * max(0, pad))
        print("│ " + " │ ".join(padded) + " │")

    print(border("└", "┴", "┘"))

def xw_mask_uid(uid: object) -> str:
    value = str(uid)
    if len(value) <= 4:
        return "******" + value
    return "******" + value[-4:]

def xw_make_session(uid: str, secret: str) -> requests.Session:
    session = requests.Session()
    session.headers.update(XW_HEADERS)
    session.headers.update({
        "user-id": str(uid),
        "user-secret-key": str(secret),
    })
    return session

def xw_parse_account_link(link: str) -> tuple[str, str]:
    uid_match = re.search(r"[?&]userId=([^&]+)", link)
    secret_match = re.search(r"[?&]secretKey=([^&]+)", link)
    if not uid_match or not secret_match:
        raise ValueError("Link thiếu userId hoặc secretKey")
    return uid_match.group(1), secret_match.group(1)

def xw_load_accounts() -> list[dict]:
    xw_rgb_print(255, 215, 0, "🔐 QUẢN LÝ TÀI KHOẢN XWORLD")
    raw_accounts: list[tuple[str, str]] = []

    if os.path.exists(XW_ACCOUNT_FILE):
        choice = input(
            f"📁 Phát hiện {XW_ACCOUNT_FILE}. Dùng lại acc cũ? (y/n): "
        ).strip().lower()

        if choice == "y":
            with open(XW_ACCOUNT_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("|", 1)
                    if len(parts) == 2:
                        raw_accounts.append((parts[0], parts[1]))

    if not raw_accounts:
        while True:
            try:
                num = int(input("👉 Nhập số lượng acc cần chạy: ").strip())
                if num <= 0:
                    print("❌ Số lượng phải lớn hơn 0!")
                    continue
                break
            except ValueError:
                print("❌ Vui lòng nhập số hợp lệ!")

        for i in range(num):
            while True:
                xw_rgb_print(
                    255,
                    0,
                    0,
                    f"\n📌 Lấy link tài khoản thứ {i + 1} "
                    "(Vào https://xworld.info/vi-VN -> Vua thoát hiểm -> Copy link):",
                )

                link = input("👉 Dán Link vào đây: ").strip()

                try:
                    uid, secret = xw_parse_account_link(link)
                    raw_accounts.append((uid, secret))
                    print(f"✅ Thành công UID: {uid}")
                    break
                except (ValueError, IndexError):
                    print("❌ Link không hợp lệ, vui lòng nhập lại!")

        with open(XW_ACCOUNT_FILE, "w", encoding="utf-8") as f:
            for uid, secret in raw_accounts:
                f.write(f"{uid}|{secret}\n")

    accounts = []
    for uid, secret in raw_accounts:
        accounts.append({
            "uid": uid,
            "secret": secret,
            "session": xw_make_session(uid, secret),
            "status": "ACTIVE",
            "error_count": 0,
            "done_this_code": False,
        })

    return accounts

def xw_show_account_assets(accounts: list[dict]) -> None:
    xw_rgb_print(0, 255, 255, "💎 ĐANG KIỂM TRA TÀI KHOẢN...")

    def get_asset(acc: dict) -> dict:
        try:
            resp = acc["session"].post(
                XW_API_ASSET,
                json={"user_id": int(acc["uid"])},
                timeout=10,
            )
            data = resp.json()

            if data.get("code") != 0:
                return {
                    "uid": acc["uid"],
                    "BUILD": 0.0,
                    "status": "LIMIT",
                }

            asset = data.get("data", {}).get("user_asset", {})

            return {
                "uid": acc["uid"],
                "BUILD": float(asset.get("BUILD", 0.0)),
                "status": "ACTIVE",
            }

        except Exception:
            return {
                "uid": acc["uid"],
                "BUILD": 0.0,
                "status": "LIMIT",
            }

    results = []
    with ThreadPoolExecutor(max_workers=min(10, max(1, len(accounts)))) as executor:
        futures = [executor.submit(get_asset, acc) for acc in accounts]
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda x: int(x["uid"]))

    rows = []
    total_build = 0.0

    for i, item in enumerate(results, 1):
        total_build += item["BUILD"]

        status = (
            Fore.GREEN + "🟢 Hoạt động" + Style.RESET_ALL
            if item["status"] == "ACTIVE"
            else Fore.RED + "🔴 Giới hạn" + Style.RESET_ALL
        )

        rows.append([
            i,
            str(item["uid"]),      # Hiển thị đầy đủ UID
            f"{item['BUILD']:.2f}",
            status,
        ])

    rows.append([
        "",
        "TỔNG",
        f"{total_build:.2f}",
        f"{len(results)} ACC",
    ])

    xw_print_square_table(
        "DANH SÁCH TÀI KHOẢN",
        ["STT", "UID", "BUILD", "TRẠNG THÁI"],
        rows,
    )

def xw_get_code_info(code: str, session: requests.Session) -> dict:
    payload = {"platform": "android", "channel": "h5", "app": 3, "code": code}
    for attempt in range(XW_MAX_RETRIES):
        try:
            resp = session.post(XW_API_DETAIL, json=payload, timeout=10)
            data = resp.json()
            if data.get("code") == 0:
                d = data.get("data", {})
                total = int(d.get("user_cnt", 0) or 0)
                progress = int(d.get("progress", 0) or 0)
                return {
                    "code": code,
                    "value": float(d.get("value", 0) or 0),
                    "total": total,
                    "remaining": max(0, total - progress),
                    "progress": progress,
                }
            return {"error": xw_translate_message(data.get("message", "Lỗi không xác định"))}
        except Exception:
            if attempt + 1 < XW_MAX_RETRIES:
                time.sleep(0.1)
    return {"error": "Lỗi kết nối mạng, không thể kết nối được"}

def xw_redeem_code_fast(acc: dict, code: str) -> tuple[str, str, float, str]:
    """Spam siêu tốc qua Session đã tạo sẵn, phân loại lỗi chi tiết."""
    payload = {"platform": "android", "channel": "h5", "app": 3, "code": code}
    try:
        resp = acc["session"].post(XW_API_EXCHANGE, json=payload, timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            value = float(data.get("data", {}).get("value", 0) or 0)
            return acc["uid"], "SUCCESS", value, "OK"

        raw_msg = str(data.get("message", "")).lower()
        msg = xw_translate_message(data.get("message", ""))
        if any(x in raw_msg for x in ("received", "already", "đã nhận", "领取", "已领取", "已領取")):
            status = "ALREADY_RECEIVED"
        elif any(x in raw_msg for x in ("out of", "not exist", "hết", "empty", "不存在", "已失效")):
            status = "CODE_EMPTY"
        elif any(x in raw_msg for x in ("limit", "max", "giới hạn", "exceed", "上限", "达到上限", "已达上限")):
            status = "ACCOUNT_LIMIT"
        else:
            status = "ERROR"
        return acc["uid"], status, 0.0, msg
    except Exception as exc:
        return acc["uid"], "ERROR", 0.0, xw_translate_message(str(exc))

def xw_log_result(uid: str, code: str, threshold: int,
               build_received: float, success: bool) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if success else "FAILED"
    with open(XW_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(
            f"{timestamp}|{uid}|{code}|{threshold}|{build_received}|{status}\n"
        )

def xw_key_still_valid_or_exit() -> bool:
    """Kiểm tra key còn hiệu lực hay không.
    XWORLD dùng chế độ an toàn: key hết hạn thì chỉ báo lỗi và quay về menu, không thoát app.
    """
    is_valid, _, _ = check_activation_valid(exit_on_expired=False)
    return is_valid

def xw_watch_code(code: str, accounts: list[dict], threshold: int) -> str:
    code = str(code).strip()
    if not code:
        xw_rgb_print(255, 0, 0, "❌ Mã code không hợp lệ.")
        return "empty"

    if not accounts:
        xw_rgb_print(255, 0, 0, "❌ Không có tài khoản để canh code.")
        return "no_accounts"

    try:
        threshold = int(threshold)
    except Exception:
        threshold = 0
    threshold = max(0, threshold)

    xw_rgb_print(0, 255, 0, f"\n🚀 ĐANG CANH CODE: {code} -- NGƯỠNG: {threshold}")
    print(Fore.WHITE + "Nhấn Ctrl+C để hủy canh code này.\n" + Style.RESET_ALL)

    if not xw_key_still_valid_or_exit():
        xw_rgb_print(255, 215, 0, "🔙 Key đã hết hạn, quay về menu chính.")
        time.sleep(1)
        return "expired"

    scan_session = requests.Session()
    scan_session.headers.update(XW_HEADERS)
    results_history: list[list[object]] = []

    for acc in accounts:
        acc["done_this_code"] = False
        acc["error_count"] = 0

    code_empty = False
    stop_reason = "normal"

    try:
        while True:
            if not xw_key_still_valid_or_exit():
                xw_rgb_print(255, 215, 0, "🔙 Key đã hết hạn, quay về menu chính.")
                stop_reason = "expired"
                break

            try:
                info = xw_get_code_info(code, scan_session)
            except KeyboardInterrupt:
                stop_reason = "interrupt"
                break

            if "error" in info:
                sys.stdout.write(
                    f"\r{Fore.RED}⚠️ Lỗi kiểm tra code: {xw_translate_message(info['error'])} - Thử lại..."
                    f"{Style.RESET_ALL}        "
                )
                sys.stdout.flush()
                time.sleep(1)
                continue

            remaining = int(info.get("remaining", 0))
            current_time = datetime.now().strftime("%H:%M:%S")

            sys.stdout.write(
                f"\r🕒 [{current_time}] Lượt còn lại: {remaining} / {info.get('total', 0)} "
                f"(Đang chờ mốc {threshold})        "
            )
            sys.stdout.flush()

            if remaining > threshold:
                time.sleep(1)
                continue

            if not xw_key_still_valid_or_exit():
                stop_reason = "expired"
                break

            print(
                f"\n\n⚡ ĐÃ ĐẠT NGƯỠNG {threshold}! "
                "ĐỔI CODE LIÊN TỤC ĐẾN KHI HẾT CODE HOẶC ĐẠT GIỚI HẠN..."
            )

            active_accs = [
                acc for acc in accounts
                if acc.get("status") == "ACTIVE"
                and not acc.get("done_this_code")
                and acc.get("error_count", 0) < 3
            ]

            if not active_accs:
                print("\n⚠️ Tất cả tài khoản đã nhận, đạt giới hạn hoặc lỗi quá nhiều.")
                stop_reason = "empty"
                break

            executor = ThreadPoolExecutor(max_workers=min(10, len(active_accs)))
            try:
                futures = {
                    executor.submit(xw_redeem_code_fast, acc, code): acc
                    for acc in active_accs
                }

                pending = set(futures.keys())
                stop_now = False

                while pending:
                    if not xw_key_still_valid_or_exit():
                        stop_reason = "expired"
                        stop_now = True
                        break

                    try:
                        done, pending = wait(
                            pending,
                            timeout=0.2,
                            return_when=FIRST_COMPLETED,
                        )
                    except KeyboardInterrupt:
                        stop_reason = "interrupt"
                        stop_now = True
                        break

                    if not done:
                        continue

                    for future in done:
                        acc = futures[future]
                        try:
                            uid, status, build, msg = future.result()
                        except KeyboardInterrupt:
                            stop_reason = "interrupt"
                            stop_now = True
                            break
                        except Exception as exc:
                            uid, status, build, msg = "UNKNOWN", "ERROR", 0.0, str(exc)

                        if status == "SUCCESS":
                            acc["done_this_code"] = True
                            status_text = Fore.GREEN + "THÀNH CÔNG" + Style.RESET_ALL
                            xw_log_result(uid, code, threshold, build, True)

                        elif status == "ALREADY_RECEIVED":
                            acc["done_this_code"] = True
                            status_text = Fore.YELLOW + "ĐÃ NHẬN" + Style.RESET_ALL

                        elif status == "ACCOUNT_LIMIT":
                            acc["status"] = "LIMIT"
                            status_text = Fore.MAGENTA + "GIỚI HẠN" + Style.RESET_ALL
                            xw_log_result(uid, code, threshold, 0.0, False)

                        elif status == "CODE_EMPTY":
                            code_empty = True
                            stop_reason = "empty"
                            status_text = Fore.RED + "CODE ĐÃ HẾT" + Style.RESET_ALL
                            stop_now = True

                        else:
                            acc["error_count"] = acc.get("error_count", 0) + 1
                            status_text = Fore.RED + "LỖI" + Style.RESET_ALL

                        results_history.append([
                            str(uid),
                            status_text,
                            f"{build:.2f}",
                            msg,
                        ])

                        if stop_now:
                            break

                    if stop_now:
                        break

            finally:
                executor.shutdown(wait=False, cancel_futures=True)

            if results_history:
                xw_print_square_table(
                    "KẾT QUẢ NHẬP CODE",
                    ["UID", "Trạng thái", "BUILD", "Thông báo"],
                    results_history[-20:],
                )

            if code_empty:
                print("\n❌ Code đã hết lượt hoặc không còn khả dụng.")
                break

            if stop_reason in ("interrupt", "expired"):
                break

            time.sleep(0.1)

    finally:
        try:
            scan_session.close()
        except Exception:
            pass

    if stop_reason == "interrupt":
        sys.stdout.write("\n")
        sys.stdout.flush()
        print(Fore.YELLOW + "🛑 Đã hủy canh code." + Style.RESET_ALL)
    elif stop_reason == "expired":
        print(Fore.YELLOW + "\n🔙 Đã quay về menu." + Style.RESET_ALL)
    else:
        print(Fore.GREEN + "\n👋 Đã thoát canh code." + Style.RESET_ALL)

    return stop_reason

def xw_main() -> None:
    start_key_expiry_monitor()
    is_valid, reason, is_vip = check_activation_valid(exit_on_expired=False)
    if not is_valid:
        if "HẾT HẠN" in str(reason).upper() or "RESET" in str(reason).upper():
            xw_rgb_print(255, 215, 0, "🔙 Key đã hết hạn, quay về menu chính.")
        else:
            xw_rgb_print(255, 0, 0, f"❌ Không thể vào XWORLD: {xw_translate_message(reason)}")
        time.sleep(1.5)
        return
    if not is_vip:
        xw_rgb_print(255, 0, 0, "❌ CANH CODE XWORLD chỉ dành cho key VIP.")
        xw_rgb_print(255, 215, 0, "🔑 Hãy kích hoạt key VIP để sử dụng chức năng này.")
        time.sleep(2)
        return

    xw_print_banner()
    # Bỏ comment dòng dưới nếu muốn bắt buộc nhập key khi khởi động.
    # xw_check_key()

    accounts = xw_load_accounts()
    if not accounts:
        xw_rgb_print(255, 0, 0, "❌ Không có tài khoản nào để chạy.")
        sys.exit(1)

    temp_session = requests.Session()
    temp_session.headers.update(XW_HEADERS)
    xw_show_account_assets(accounts)

    while True:
        is_valid, reason, _ = check_activation_valid(exit_on_expired=False)
        if not is_valid:
            if "HẾT HẠN" in str(reason).upper() or "RESET" in str(reason).upper():
                xw_rgb_print(255, 215, 0, "🔙 Key đã hết hạn, quay về menu chính.")
            else:
                xw_rgb_print(255, 0, 0, f"❌ Không thể tiếp tục: {xw_translate_message(reason)}")
            time.sleep(1)
            return

        try:
            print()
            code = input(
                Fore.CYAN + "🎁 Nhập mã code cần canh (Nhấn Enter để dừng tool): "
                + Style.RESET_ALL
            ).strip()
        except KeyboardInterrupt:
            print(Fore.RED + "🛑 Đã hủy nhập mã code." + Style.RESET_ALL)
            return

        is_valid, reason, _ = check_activation_valid(exit_on_expired=False)
        if not is_valid:
            if "HẾT HẠN" in str(reason).upper() or "RESET" in str(reason).upper():
                xw_rgb_print(255, 215, 0, "🔙 Key đã hết hạn, quay về menu chính.")
            else:
                xw_rgb_print(255, 0, 0, f"❌ Không thể tiếp tục: {xw_translate_message(reason)}")
            time.sleep(1)
            return

        if not code:
            xw_rgb_print(0, 255, 0, "👋 Đã dừng tool. Hẹn gặp lại!")
            return

        xw_rgb_print(255, 215, 0, f">> Đang kiểm tra mã code: {code} ...")
        info = xw_get_code_info(code, temp_session)
        if "error" in info:
            print(Fore.RED + f"❌ Lỗi kiểm tra mã code: {xw_translate_message(info['error'])}" + Style.RESET_ALL)
            continue

        xw_print_square_table(
            "THÔNG TIN MÃ CODE",
            ["Mã Code", "Giá trị (BUILD)", "Tổng lượt", "Lượt còn lại"],
            [[
                info.get("code", code), f"{info.get('value', 0):.2f}",
                info.get("total", 0), info.get("remaining", 0)
            ]],
        )

        try:
            choice = input(">> Bạn có muốn canh mã code này không? (y/n): ").strip().lower()
        except KeyboardInterrupt:
            print(Fore.RED + "🛑 Đã hủy nhập mã code." + Style.RESET_ALL)
            return

        if not check_activation_valid(exit_on_expired=False)[0]:
            xw_rgb_print(255, 215, 0, "🔙 Key đã hết hạn, quay về menu chính.")
            time.sleep(1)
            return

        if choice != "y":
            continue

        try:
            threshold = int(input(
                "🎯 Nhập ngưỡng (số lượt còn lại để tự động kích hoạt nhập): "
            ).strip())
        except KeyboardInterrupt:
            print(Fore.RED + "🛑 Đã hủy nhập ngưỡng." + Style.RESET_ALL)
            continue
        except ValueError:
            print("❌ Ngưỡng phải là số nguyên!")
            continue

        if not check_activation_valid(exit_on_expired=False)[0]:
            xw_rgb_print(255, 215, 0, "🔙 Key đã hết hạn, quay về menu chính.")
            time.sleep(1)
            return

        try:
            result = xw_watch_code(code, accounts, threshold)
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            sys.stdout.flush()
            print(Fore.YELLOW + "🛑 Đã hủy canh code." + Style.RESET_ALL)
            continue

        if result == "interrupt":
            continue

        if result == "empty":
            xw_rgb_print(0, 255, 0, "👋 Mã code đã hết hoặc không còn khả dụng.")
            continue

        if result == "expired":
            return

        # Sau khi xử lý xong một mã code (normal/empty/interrupt),
        # luôn quay lại ô nhập mã code thay vì thoát khỏi XWORLD.
        continue


# ================== HILO TOOL  ==================

C_GREEN = '\033[92m'
C_RED = '\033[91m'
C_YELLOW = '\033[93m'
C_CYAN = '\033[96m'
C_WHITE = '\033[97m'
C_NEON_PINK = '\033[95m'
C_RESET = '\033[0m'
C_DIM = '\033[2m'

def hilo_show_temp_error(message, seconds=3):
    # Hien thi loi tam thoi roi xoa khoi terminal.
    lines = str(message).splitlines() or [""]
    print("\n".join(lines), flush=True)
    time.sleep(seconds)

    # Xoa cac dong loi da in va dua con tro ve vi tri nhap.
    for index in range(len(lines)):
        print("\033[2K\r", end="")
        if index < len(lines) - 1:
            print("\033[1A", end="")
    print("\r", end="", flush=True)
def hilo_get_device_fingerprint(identifier):
    hash_id = int(hashlib.md5(str(identifier).encode()).hexdigest(), 16)
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
    ]
    return uas[hash_id % len(uas)]

def hilo_build_secure_session(user_agent, proxy_url=None, token=None, apikey=None):
    session = requests.Session()
    is_mobile = "Mobile" in user_agent
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=utf-8",
        "User-Agent": user_agent,
        "Origin": "https://hilo.turbogg4u.online",
        "Referer": "https://hilo.turbogg4u.online/",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Ch-Ua-Mobile": "?1" if is_mobile else "?0",
        "Sec-Ch-Ua-Platform": "\"Android\"" if "Android" in user_agent else ("\"iOS\"" if "iPhone" in user_agent else "\"Windows\"")
    }
    
    if token:
        headers["authorization"] = token
    if apikey:
        headers["apikey"] = apikey
        headers["metadata"] = json.dumps({"device": "mobile" if is_mobile else "desktop", "manual": True})
        headers["subpartnerid"] = ""
        
    session.headers.update(headers)
    
    retry_strategy = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=50, pool_maxsize=50)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    if proxy_url:
        session.proxies.update({"http": proxy_url, "https": proxy_url})
        
    return session

def hilo__response_json(response, endpoint="API"):
    """Kiểm tra HTTP và parse JSON an toàn."""
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError as exc:
        preview = (response.text or "")[:300].replace("\n", " ")
        raise RuntimeError(f"{endpoint} trả về JSON không hợp lệ: {preview}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"{endpoint} trả về kiểu dữ liệu không hợp lệ: {type(data).__name__}")
    return data


def hilo__extract_card(value, fallback=None):
    """Chuẩn hóa lá bài từ các dạng phổ biến của API/game."""
    if value is None:
        return fallback

    if isinstance(value, dict):
        # Ưu tiên đúng các field lá bài trước.
        for key in (
            "card", "value", "rank", "number", "point",
            "cardValue", "cardRank", "currentCard",
            "drawnCard", "newCard", "resultCard", "initialCard",
        ):
            if value.get(key) is not None:
                found = hilo__extract_card(value.get(key), None)
                if found is not None:
                    return found

        # Hỗ trợ payload bọc trong data/result/game/round/state/payload.
        for key in ("data", "result", "game", "round", "state", "payload"):
            if value.get(key) is not None:
                found = hilo__extract_card(value.get(key), None)
                if found is not None:
                    return found

        return fallback

    if isinstance(value, list):
        for item in value:
            found = hilo__extract_card(item, None)
            if found is not None:
                return found
        return fallback

    if isinstance(value, bool):
        return fallback

    if isinstance(value, (int, float)):
        value = int(value)
        return value if 1 <= value <= 13 else fallback

    text = str(value).strip()
    if not text:
        return fallback

    upper = text.upper()
    face_to_number = {"A": 1, "J": 11, "Q": 12, "K": 13}
    if upper in face_to_number:
        return face_to_number[upper]

    try:
        number = int(text)
        return number if 1 <= number <= 13 else fallback
    except ValueError:
        return fallback


def hilo__get_game_card(payload, fallback=None):
    """
    Lấy lá bài theo đúng thứ tự ưu tiên:
    response server -> các lớp payload lồng nhau -> fallback.
    """
    card = hilo__extract_card(payload, None)
    if card is not None:
        return card
    return hilo__extract_card(fallback, None)


def hilo_get_card_value(card):
    """Chuẩn hóa thứ hạng Hilo về số: A=1, J=11, Q=12, K=13."""
    normalized = hilo__extract_card(card)
    try:
        value = int(normalized)
    except (TypeError, ValueError):
        return 7

    return value if 1 <= value <= 13 else 7


def hilo_action_label(action):
    """Hiển thị hướng cược theo đúng tên API: HI / LO."""
    labels = {
        "hi": "HI",
        "lo": "LO",
    }
    normalized = str(action).lower()
    return labels.get(normalized, normalized.upper())


def hilo_compare_card_result(previous_card, drawn_card):
    """Xác định quan hệ 2 lá để hiển thị: CAO / NHỎ / BẰNG."""
    if previous_card is None or drawn_card is None:
        return None
    try:
        previous_value = hilo_get_card_value(previous_card)
        drawn_value = hilo_get_card_value(drawn_card)
    except Exception:
        return None

    if drawn_value > previous_value:
        return "CAO"
    if drawn_value < previous_value:
        return "NHỎ"
    return "BẰNG"


# =========================
# LOGIC FREE / VIP
# =========================

def hilo__clean_history(history, limit=60):
    """Chuẩn hóa lịch sử để phân tích.

    Giá trị hiển thị/API: A=1, 2..10, J=11, Q=12, K=13.
    Giá trị nội bộ khi so sánh Hilo: 2..K=2..13, A=14.
    """
    if not history:
        return []

    values = []
    for card in history[-limit:]:
        try:
            value = hilo_get_card_value(card)
        except Exception:
            continue

        if not 1 <= value <= 13:
            continue

        # API/display dùng 1 cho A, nhưng A là rank cao nhất khi phân tích.
        values.append(14 if value == 1 else value)

    return values


def hilo__outcome_between(previous_value, next_value):
    """Quan hệ giữa 2 lá: hi / lo / draw."""
    if next_value > previous_value:
        return "hi"
    if next_value < previous_value:
        return "lo"
    return "draw"


def hilo__direction_counts(values):
    """Đếm nhẹ hướng CAO/NHỎ/BẰNG trong chuỗi lịch sử."""
    hi = lo = draw = 0
    for previous_value, next_value in zip(values, values[1:]):
        outcome = hilo__outcome_between(previous_value, next_value)
        if outcome == "hi":
            hi += 1
        elif outcome == "lo":
            lo += 1
        else:
            draw += 1
    return hi, lo, draw


def hilo__weighted_direction_score(values, decay=0.82):
    """
    Điểm xu hướng theo thời gian.
    Mẫu càng gần hiện tại có trọng số càng lớn.
    Trả về >0 thiên CAO, <0 thiên NHỎ.
    """
    pairs = list(zip(values, values[1:]))
    if not pairs:
        return 0.0

    score = 0.0
    weight = 1.0
    total_weight = 0.0

    for previous_value, next_value in reversed(pairs):
        outcome = hilo__outcome_between(previous_value, next_value)
        if outcome == "hi":
            score += weight
        elif outcome == "lo":
            score -= weight
        # BẰNG = 0, không ép hướng.
        total_weight += weight
        weight *= decay

    if total_weight <= 0:
        return 0.0
    return score / total_weight


def hilo__streak_score(values, max_streak=5):
    """
    Tạo tín hiệu rất nhỏ từ chuỗi liên tiếp gần nhất.
    Không coi streak là quy luật chắc chắn; chỉ dùng như tín hiệu phụ.
    """
    pairs = list(zip(values, values[1:]))
    if not pairs:
        return 0.0

    last_outcome = hilo__outcome_between(*pairs[-1])
    if last_outcome == "draw":
        return 0.0

    streak = 0
    for previous_value, next_value in reversed(pairs):
        outcome = hilo__outcome_between(previous_value, next_value)
        if outcome != last_outcome:
            break
        streak += 1
        if streak >= max_streak:
            break

    # Streak quá dài được giảm trọng số để tránh đuổi cầu.
    strength = min(streak / max_streak, 1.0)
    return strength if last_outcome == "hi" else -strength


def hilo__markov_score(values):
    """
    Ước lượng chuyển trạng thái CAO/NHỎ từ lịch sử bằng Laplace smoothing.
    Chỉ dùng khi có đủ dữ liệu; tránh phản ứng mạnh với vài ván đầu.
    """
    pairs = list(zip(values, values[1:]))
    if len(pairs) < 5:
        return 0.0

    transitions = {
        "hi": {"hi": 1.0, "lo": 1.0},
        "lo": {"hi": 1.0, "lo": 1.0},
    }

    last_direction = None
    for previous_value, next_value in pairs:
        current_direction = hilo__outcome_between(previous_value, next_value)
        if current_direction not in ("hi", "lo"):
            continue
        if last_direction in transitions:
            transitions[last_direction][current_direction] += 1.0
        last_direction = current_direction

    if last_direction not in transitions:
        return 0.0

    row = transitions[last_direction]
    total = row["hi"] + row["lo"]
    p_hi = row["hi"] / total
    return (p_hi - 0.5) * 2.0


def hilo__current_card_edge(current_card):
    """Lợi thế cơ bản theo đúng thứ tự Hilo: 2 < ... < K < A.

    Có 13 hạng; bỏ trường hợp BẰNG khi chuẩn hóa xác suất hướng.
    Với rank v (2..14):
      cao hơn = 14-v
      thấp hơn = v-2
    """
    value = hilo_get_card_value(current_card)
    rank_value = 14 if value == 1 else value
    hi = 14 - rank_value
    lo = rank_value - 2
    total_non_draw = hi + lo

    if total_non_draw <= 0:
        return 0.0

    return (hi - lo) / total_non_draw


def hilo__recent_balance_score(values, window=10):
    """
    Tín hiệu cân bằng rất nhẹ.
    Không giả định rằng 'thiếu CAO' bắt buộc phải xuất hiện tiếp theo.
    Chỉ phản ánh mức lệch ngắn hạn để giảm quyết định quá cực đoan.
    """
    recent = values[-window:]
    if not recent:
        return 0.0

    hi = sum(1 for value in recent if value >= 8)
    lo = sum(1 for value in recent if value <= 6)
    active = hi + lo

    if active == 0:
        return 0.0

    imbalance = (hi - lo) / active
    return -imbalance * 0.25


def hilo__resolve_direction(hi_score, lo_score, fallback="hi"):
    """Chọn hướng ổn định, tránh trả None."""
    if hi_score > lo_score:
        return "hi"
    if lo_score > hi_score:
        return "lo"
    return fallback


def hilo_predict_action_basic(current_card):
    """Điểm nền theo đúng thứ tự Hilo: 2 < ... < K < A."""
    value = hilo_get_card_value(current_card)
    rank_value = 14 if value == 1 else value
    if rank_value >= 14:   # A lớn nhất
        return "lo"
    if rank_value <= 2:    # 2 nhỏ nhất
        return "hi"
    if rank_value <= 6:
        return "hi"
    if rank_value >= 8:
        return "lo"
    # 7 là vùng cân bằng; fallback CAO.
    return "hi"


def hilo_predict_action_free(current_card, history=None):
    """
    LOGIC FREE - đa tín hiệu, nhẹ và ổn định.

    Trọng số:
      60% lợi thế từ lá hiện tại
      25% xu hướng có trọng số theo thời gian
      10% cân bằng gần đây
       5% streak

    Mục tiêu là tốt hơn logic một điều kiện nhưng vẫn tránh "đuổi cầu".
    """
    values = hilo__clean_history(history, limit=30)

    current_edge = hilo__current_card_edge(current_card)
    trend = hilo__weighted_direction_score(values, decay=0.78)
    balance = hilo__recent_balance_score(values, window=8)
    streak = hilo__streak_score(values, max_streak=4)

    total_score = (
        0.60 * current_edge
        + 0.25 * trend
        + 0.10 * balance
        + 0.05 * streak
    )

    # Lá 8 là tâm đối xứng của dải 2..A khi xét 2 hướng CAO/NHỎ.
    # Gần vùng cân bằng thì dùng lịch sử làm tie-break.
    if abs(current_edge) < 0.01 and abs(total_score) < 0.08:
        if values:
            hi_count, lo_count, _ = hilo__direction_counts(values[-12:])
            if hi_count != lo_count:
                return "lo" if hi_count < lo_count else "hi"
        return "hi"

    return "hi" if total_score >= 0 else "lo"


def hilo_predict_action_vip(current_card, history=None):
    """
    LOGIC VIP - ensemble nhiều mô hình heuristic.

    Thành phần:
      40% lợi thế trực tiếp từ lá hiện tại
      20% Markov chuyển trạng thái
      15% xu hướng recency
      10% cân bằng gần đây
      10% streak
       5% xu hướng trung hạn

    Có cơ chế giảm ảnh hưởng lịch sử khi dữ liệu quá ít hoặc quá nhiễu.
    Không tuyên bố đảm bảo thắng; kết quả vẫn phụ thuộc RNG/server.
    """
    values = hilo__clean_history(history, limit=60)

    current_edge = hilo__current_card_edge(current_card)
    weighted_trend = hilo__weighted_direction_score(values, decay=0.88)
    short_trend = hilo__weighted_direction_score(values[-12:], decay=0.72)
    markov = hilo__markov_score(values)
    balance = hilo__recent_balance_score(values, window=12)
    streak = hilo__streak_score(values, max_streak=5)

    # Tín hiệu trung hạn: so sánh nửa gần với nửa trước để bắt thay đổi nhịp,
    # nhưng trọng số thấp để tránh overfit.
    medium_shift = 0.0
    if len(values) >= 12:
        first = values[-12:-6]
        second = values[-6:]
        first_score = hilo__weighted_direction_score(first, decay=0.85)
        second_score = hilo__weighted_direction_score(second, decay=0.85)
        medium_shift = max(-1.0, min(1.0, second_score - first_score))

    n = len(values)
    if n < 6:
        # Chưa có đủ dữ liệu: ưu tiên lá hiện tại, không cố "đọc cầu".
        hi_score = max(current_edge, 0.0)
        lo_score = max(-current_edge, 0.0)
        return hilo__resolve_direction(hi_score, lo_score, hilo_predict_action_basic(current_card))

    # Khi history dài hơn, ảnh hưởng lịch sử được phép tăng nhẹ.
    history_factor = min(1.0, n / 20.0)

    history_score = (
        0.28 * markov
        + 0.26 * short_trend
        + 0.16 * weighted_trend
        + 0.12 * balance
        + 0.10 * streak
        + 0.08 * medium_shift
    )

    combined_score = (
        (0.40 * current_edge)
        + (0.60 * history_factor * history_score)
    )

    # Không để lịch sử lấn át hoàn toàn lợi thế của lá hiện tại.
    current_weight = 0.55 if abs(current_edge) >= 0.50 else 0.45
    combined_score = (
        current_weight * current_edge
        + (1.0 - current_weight) * history_factor * history_score
    )

    # Vùng quá cân bằng: dùng current-card edge làm quyết định cuối,
    # giúp VIP không trả về None và không đảo hướng liên tục.
    if abs(combined_score) < 0.035:
        return hilo_predict_action_basic(current_card)

    return "hi" if combined_score > 0 else "lo"

def hilo_select_analysis_logic():
    """Chọn logic HILO theo loại key đang kích hoạt.

    KEY FREE: chỉ được phép chọn LOGIC FREE.
    KEY VIP: được phép chọn LOGIC FREE hoặc LOGIC VIP.
    """
    try:
        is_valid, reason, is_vip = check_activation_valid(exit_on_expired=False)
    except Exception as exc:
        is_valid, reason, is_vip = False, str(exc), False

    if not is_valid:
        console.print(f"[bold red]❌ Key không hợp lệ: {reason}[/bold red]")
        return None

    print(f"\n{C_NEON_PINK}========== CHỌN LOGIC HILO ================{C_RESET}")
    print(f"{C_GREEN}1. LOGIC FREE{C_RESET}")
    if is_vip:
        print(f"{C_RED}2. LOGIC VIP{C_RESET}")
    else:
        print(f"{C_DIM}2. LOGIC VIP (chỉ Key VIP){C_RESET}")
    print(f"{C_NEON_PINK}============================================{C_RESET}")

    while True:
        choice = input(f"{C_WHITE}👉 Chọn Logic (1/2): {C_RESET}").strip()

        if choice == "1":
            print(f"{C_GREEN}✅ Đã chọn HILO LOGIC FREE{C_RESET}")
            return "free"

        if choice == "2":
            if is_vip:
                print(f"{C_RED}✅ Đã chọn HILO LOGIC VIP{C_RESET}")
                return "vip"

            hilo_show_temp_error(f"{C_RED}❌ LOGIC VIP chỉ dành cho Key VIP.{C_RESET}")
            continue

        hilo_show_temp_error(f"{C_RED}❌ Chỉ được chọn 1 hoặc 2.{C_RESET}")

def hilo_get_multiline_json():
    print(f"{C_WHITE}👉 Dán Payload JSON vào đây:{C_RESET}")

    while True:
        raw = input().strip()

        if not raw:
            hilo_show_temp_error(f"{C_YELLOW}⚠️ JSON đang trống. Vui lòng dán lại.{C_RESET}")
            continue

        try:
            payload = json.loads(raw)

            if not isinstance(payload, dict):
                hilo_show_temp_error(f"{C_RED}JSON hợp lệ nhưng phải là một object/dict.{C_RESET}")
                continue

            return payload

        except json.JSONDecodeError as e:
            hilo_show_temp_error(
                f"{C_RED}❌ JSON không hợp lệ. "
                f"Vui lòng dán lại và bấm Enter.{C_RESET}"
            )

        except Exception as e:
            hilo_show_temp_error(f"{C_RED}❌ Lỗi khi đọc JSON. Vui lòng kiểm tra lại dữ liệu.{C_RESET}")

def hilo__prompt_number(prompt, cast=float, min_value=None, allow_zero=True):
    """Nhập số; nhập sai thì yêu cầu nhập lại thay vì thoát chương trình."""
    while True:
        raw = input(prompt).strip()
        try:
            value = cast(raw)
            if isinstance(value, float) and not __import__('math').isfinite(value):
                raise ValueError("giá trị phải là số hữu hạn")
            if min_value is not None and value < min_value:
                hilo_show_temp_error(f"{C_RED}❌ Giá trị phải >= {min_value}. Vui lòng nhập lại.{C_RESET}")
                continue
            if not allow_zero and value == 0:
                hilo_show_temp_error(f"{C_RED}❌ Giá trị không được bằng 0. Vui lòng nhập lại.{C_RESET}")
                continue
            return value
        except (ValueError, TypeError):
            hilo_show_temp_error(f"{C_RED}❌ Nhập sai định dạng. Vui lòng nhập lại.{C_RESET}")


def hilo_setup_config():
    os.system('clear' if os.name == 'posix' else 'cls')

    while True:
        use_proxy = input(f"{C_WHITE}Bạn có muốn sử dụng Proxy không? (y/n): {C_RESET}").strip().lower()
        if use_proxy in ('y', 'n'):
            break
        hilo_show_temp_error(f"{C_RED}❌ Chỉ được nhập y hoặc n. Vui lòng nhập lại.{C_RESET}")

    proxy_url = None
    if use_proxy == 'y':
        while True:
            proxy_url = input(f"{C_WHITE} Nhập Proxy (VD: http://user:pass@ip:port): {C_RESET}").strip()
            if not proxy_url:
                hilo_show_temp_error(f"{C_RED}❌ Proxy đang trống. Vui lòng nhập lại.{C_RESET}")
                continue

            print(f"{C_DIM}>> Đang kiểm tra Proxy...{C_RESET}")
            try:
                test_sess = requests.Session()
                test_sess.proxies.update({"http": proxy_url, "https": proxy_url})
                test_sess.get("https://hilo.turbogg4u.online", timeout=10)
                print(f"{C_GREEN}>> Proxy hoạt động tốt.{C_RESET}")
                break
            except Exception:
                hilo_show_temp_error(f"{C_RED}❌ Proxy lỗi. Vui lòng kiểm tra lại Proxy.{C_RESET}")
                while True:
                    retry_proxy = input(f"{C_WHITE} Bạn có muốn thử lại Proxy không? (y/n): {C_RESET}").strip().lower()
                    if retry_proxy in ('y', 'n'):
                        break
                    hilo_show_temp_error(f"{C_RED}❌ Chỉ được nhập y hoặc n. Vui lòng nhập lại.{C_RESET}")
                if retry_proxy == 'n':
                    proxy_url = None
                    print(f"{C_YELLOW} Tiếp tục không sử dụng Proxy.{C_RESET}")
                    break

    login_payload = hilo_get_multiline_json()
    identifier = "termux_user"
    user_agent = hilo_get_device_fingerprint(identifier)

    print(f"{C_DIM}>> Đang xác thực tài khoản...{C_RESET}")
    auth_session = hilo_build_secure_session(user_agent, proxy_url)

    while True:
        try:
            response = auth_session.post(
                "https://hilo.turbogg4u.online/api/common/profile",
                json=login_payload,
                timeout=(10, 15)
            )
            res = hilo__response_json(response, "PROFILE")

            if 'id' in res and 'token' in res:
                apikey = res['id']
                token = res['token']
                currency = res.get('currency', 'bld')
                balance = float(res.get('balance', 0))
                name = res.get('playerName', 'Unknown')
                print(f"{C_GREEN}✅ Đăng nhập thành công!{C_RESET}")
                print(f"{C_WHITE}👤 Tài khoản: {name}{C_RESET}")
                print(f"{C_WHITE}💰 Số dư: {balance} {currency}{C_RESET}\n")
                break
            else:
                hilo_show_temp_error(f"{C_RED}❌ Không thể xác thực. Vui lòng kiểm tra lại Payload JSON.{C_RESET}")

        except Exception as e:
            hilo_show_temp_error(f"{C_RED}❌ Lỗi kết nối/xác thực. Vui lòng thử lại.{C_RESET}")

        login_payload = hilo_get_multiline_json()
        print(f"{C_DIM}>> Đang xác thực lại tài khoản...{C_RESET}")

    # Chọn LOGIC theo menu HILO cũ; KEY FREE bị khóa LOGIC VIP.
    analysis_logic = hilo_select_analysis_logic()
    if analysis_logic not in ("free", "vip"):
        raise RuntimeError("Không xác định được quyền LOGIC từ KEY hiện tại.")

    base_bet = hilo__prompt_number(f"{C_WHITE}1. Số BUILD cược mỗi ván: {C_RESET}", float, min_value=0, allow_zero=False)
    target_profit = hilo__prompt_number(f"{C_WHITE}2. Nhập số BUILD muốn lãi: {C_RESET}", float, min_value=0)
    stop_loss = hilo__prompt_number(f"{C_WHITE}3. Ngưỡng cắt lỗ: {C_RESET}", float, min_value=0)
    loss_multiplier = hilo__prompt_number(f"{C_WHITE}4. Hệ số gấp thếp khi thua: {C_RESET}", float, min_value=0, allow_zero=False)
    target_opens = hilo__prompt_number(f"{C_WHITE}5. Số lá mở an toàn tối đa 1 ván: {C_RESET}", int, min_value=1)
    delay_bet = hilo__prompt_number(f"{C_WHITE}6. Delay đánh bài (giây): {C_RESET}", float, min_value=0)
    delay_win = hilo__prompt_number(f"{C_WHITE}7. Delay sau khi thắng (giây): {C_RESET}", float, min_value=0)
    delay_loss = hilo__prompt_number(f"{C_WHITE}8. Delay sau khi thua (giây): {C_RESET}", float, min_value=0)

    return {
        'proxy_url': proxy_url,
        'login_payload': login_payload,
        'analysis_logic': analysis_logic,
        'apikey': apikey,
        'token': token,
        'currency': currency,
        'original_balance': balance,
        'current_balance': balance,
        'player_name': name,
        'base_bet': base_bet,
        'target_profit': target_profit,
        'stop_loss': stop_loss,
        'loss_multiplier': loss_multiplier,
        'target_opens': target_opens,
        'delay_bet': delay_bet,
        'delay_win': delay_win,
        'delay_loss': delay_loss,
        'user_agent': user_agent
    }

# ================== GIAO DIỆN TOOL HILO ==================

HILO_COLORS = VBTOOL_COLORS
HILO_ICONS = ICONS
HILO_LOGO = LOGO_VBTOOL


def hilo_build_logo_with_gradient(logo_text: str) -> Text:

    return build_logo_with_gradient(logo_text)


def hilo_make_vbtool_header() -> Group:
    return show_ultimate_header()


def hilo__hilo_rank_label(card):

    try:
        normalized = hilo__extract_card(card, None)
        if normalized is None:
            return "—"

        if isinstance(normalized, str):
            upper = normalized.strip().upper()
            face_to_number = {"A": 1, "J": 11, "Q": 12, "K": 13}
            if upper in face_to_number:
                return str(face_to_number[upper])
            return str(int(upper)) if upper.isdigit() else upper
        value = int(normalized)
        return str(value)
    except Exception:
        return str(card) if card is not None else "—"


def hilo__update_hilo_hotcold(history):
    counts = Counter()
    for rec in history:
        for k in ("current_card", "drawn_card"):
            val = rec.get(k)
            if val is not None:
                try:
                    counts[hilo_get_card_value(val)] += 1
                except Exception:
                    pass
    return counts


def hilo_make_vbtool_compact_panel(state: Dict) -> Panel:
    balance = state.get("balance")
    original = state.get("original_balance", balance)
    try:
        bal_text = f"{float(balance):.2f}" if balance is not None else "—"
    except Exception:
        bal_text = "—"

    try:
        diff = float(balance) - float(original) if balance is not None and original is not None else 0.0
    except Exception:
        diff = 0.0

    sign = "+" if diff > 0 else ""

    if diff > 0:
        arrow, profit_style = "🚀", f"bold {HILO_COLORS['emerald']}"
    elif diff < 0:
        arrow, profit_style = "💔", f"bold {HILO_COLORS['ruby']}"
    else:
        arrow, profit_style = "➡️", HILO_COLORS["gold"]

    stats = state.get("model_stats", {})
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    total = stats.get("predictions", 0)
    win_rate = (wins / total * 100.0) if total else 0.0

    t = Text()

    t.append(f"{HILO_ICONS['user']} User: {state.get('account_id', '—')}", style=HILO_COLORS["history_blue"])
    t.append("  |  ", style="dim")
    t.append(f"{HILO_ICONS['money']} BLD: {bal_text} ", style=f"bold {HILO_COLORS['emerald']}")
    t.append("\n" + "━" * 68 + "\n", style=HILO_COLORS["gold"])
    
    t.append(f"📊 Kết quả #{state.get('last_issue', '—')}: {state.get('last_result', '—')}", style=HILO_COLORS["platinum"])
    t.append("  |  Tỷ lệ: ", style="dim")
    t.append(f"{win_rate:.0f}%", style=f"bold {HILO_COLORS['history_blue']}")
    t.append("  |  ", style="dim")
    t.append(f"{arrow} {sign}{diff:.2f}", style=profit_style)

    t.append("\n" + "─" * 68 + "\n", style="dim")

    t.append(f"{HILO_ICONS['chart']} Tổng: ", style="dim")
    t.append(f"{total} ván", style=HILO_COLORS["platinum"])
    t.append("  |  🏆 Win ", style="dim")
    t.append(str(wins), style=HILO_COLORS["emerald"])
    t.append("  💀 Lose ", style="dim")
    t.append(str(losses), style=HILO_COLORS["ruby"])

    current_bet = state.get("current_bet", 0.0)
    t.append("\n", "")
    t.append(f"{HILO_ICONS['money']} Đã cược: ", style="dim")
    t.append(f"{current_bet:.2f} BLD", style=HILO_COLORS["gold"])
    t.append("  |  📊 Lãi/Lỗ: ", style="dim")
    t.append(f"{sign}{diff:.2f} BLD", style=profit_style)

    log_text = state.get("log_text", "—")
    t.append("\n" + "─" * 68 + "\n", style="dim")
    t.append(log_text, style=HILO_COLORS["platinum"])
    t.append("\n", "")

    return Panel(
        t,
        border_style=HILO_COLORS["bright_cyan"],
        box=box.SIMPLE_HEAVY,
        padding=(0, 1)
    )


def hilo_make_vbtool_history_cards(history: List[Dict], limit: int = 5, highlight_issue=None) -> Panel:
    recent = list(reversed(history[-limit:]))
    cards = []

    for rec in recent:
        issue = rec.get("issue_id", "—")

        # Lấy giờ từ timestamp
        timestamp = str(rec.get("timestamp", ""))
        if " " in timestamp:
            short_ts = timestamp.split(" ")[-1][:8]
        elif "T" in timestamp:
            short_ts = timestamp.split("T")[-1][:8]
        else:
            short_ts = timestamp[-8:] if timestamp else "—"

        current_card = hilo__hilo_rank_label(rec.get("current_card"))
        drawn_card = hilo__hilo_rank_label(rec.get("drawn_card"))
        result = str(rec.get("result", "—"))

        if result == "THẮNG":
            result_icon, result_style = "🟢", f"bold white on {HILO_COLORS['emerald']}"
            pl_style = f"bold {HILO_COLORS['emerald']}"
        elif result == "THUA":
            result_icon, result_style = "🔴", f"bold white on {HILO_COLORS['ruby']}"
            pl_style = f"bold {HILO_COLORS['ruby']}"
        else:
            result_icon, result_style = "🟡", f"bold black on {HILO_COLORS['gold']}"
            pl_style = HILO_COLORS["gold"]

        try:
            pl = float(rec.get("profit", 0.0))
            pl_text = f"{pl:+.2f}"
        except Exception:
            pl_text = "—"

        bs = (
            HILO_COLORS["gold"]
            if highlight_issue is not None and issue == highlight_issue
            else HILO_COLORS["onyx"]
        )

        card = Panel(
            Align.left(
                Text.assemble(
                    Text(
                        f"#{str(issue)[-4:]}\n",
                        style=f"bold {HILO_COLORS['history_blue']}",
                    ),
                    Text(
                        f"{short_ts}\n",
                        style="dim",
                    ),
                    Text(
                        f"{current_card} → {drawn_card}\n",
                        style="bold white",
                    ),
                    Text(
                        f"{result_icon} ",
                        style=result_style,
                    ),
                    Text(
                        f"{result}  ",
                        style=result_style,
                    ),
                    Text(
                        pl_text,
                        style=pl_style,
                    ),
                )
            ),
            box=box.ROUNDED,
            padding=(0, 1),
            width=14,
            border_style=bs,
        )

        cards.append(card)

    if not cards:
        return Panel(
            Text("Không có lịch sử", style="dim"),
            border_style=HILO_COLORS["onyx"],
        )

    return Panel(
        Columns(
            cards,
            equal=False,
            expand=False,
            padding=(0, 0),
        ),
        title="LỊCH SỬ GẦN ĐÂY",
        border_style=HILO_COLORS["history_blue"],
        box=box.ROUNDED,
    )


def hilo_make_vbtool_layout(state: Dict) -> Layout:
    layout = Layout(name="root")
    layout.split_column(
        Layout(name="header", size=8),
        Layout(name="hilo_main", ratio=1),
        Layout(name="history", size=12),
    )
    layout["header"].update(hilo_make_vbtool_header())
    layout["hilo_main"].update(hilo_make_vbtool_compact_panel(state))
    layout["history"].update(hilo_make_vbtool_history_cards(
        state.get("history", []), limit=5, highlight_issue=state.get("last_issue")
    ))
    return layout


def hilo__history_append(state, issue, current_card, drawn_card, result, profit):
    state["history"].append({
        "issue_id": issue,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_card": current_card,
        "drawn_card": drawn_card,
        "result": result,
        "profit": profit,
    })
    if len(state["history"]) > 30:
        del state["history"][:-30]


def hilo_main():
    cfg = hilo_setup_config()
    session = hilo_build_secure_session(
        cfg['user_agent'],
        cfg['proxy_url'],
        cfg['token'],
        cfg['apikey']
    )

    current_bet = cfg['base_bet']
    last_result = 'none'
    analysis_history = []
    stats = {"predictions": 0, "wins": 0, "losses": 0}

    state = {
        "account_id": cfg.get("player_name") or cfg.get("login_payload", {}).get("username", "—"),
        "balance": cfg.get("current_balance", 0.0),
        "original_balance": cfg.get("original_balance", 0.0),
        "last_issue": "—",
        "last_result": "CHƯA CÓ",
        "current_card": None,
        "next_prediction": "—",
        "current_bet": current_bet,
        "history": [],
        "model_stats": stats,
        "log_text": "Sẵn sàng ✅",
    }

    # Khi chốt lời/cắt lỗ đạt ngưỡng, lưu lý do để hiển thị SAU KHI Live đóng.
    # Nếu in trong Live rồi break ngay, screen=True sẽ xóa nội dung trước khi menu game hiện ra.
    stop_reason = None

    with Live(hilo_make_vbtool_layout(state), console=console, refresh_per_second=8, screen=True) as live:
        while True:
            if last_result == 'win':
                time.sleep(cfg['delay_win'])
            elif last_result == 'loss':
                time.sleep(cfg['delay_loss'])
            else:
                time.sleep(0.5)

            state["current_bet"] = current_bet
            state["balance"] = cfg["current_balance"]
            state["log_text"] = "Đang chuẩn bị ván mới..."
            live.update(hilo_make_vbtool_layout(state))

            if current_bet > cfg['current_balance']:
                if cfg['current_balance'] >= cfg['base_bet']:
                    current_bet = cfg['base_bet']
                else:
                    state["log_text"] = "Số dư không đủ để cược. Dừng tool!"
                    live.update(hilo_make_vbtool_layout(state))
                    break

            initial_card = random.randint(1, 13)
            create_payload = {
                "clientSeed": str(uuid.uuid4()),
                "nonce": int(time.time() * 1000) % 100000,
                "initialCard": initial_card,
            }

            try:
                response = session.post(
                    "https://hilo.turbogg4u.online/api/games/create",
                    json=create_payload,
                    timeout=(10, 30)
                )
                res_create = hilo__response_json(response, "CREATE")
                if 'roundId' not in res_create:
                    state["log_text"] = f"Đang kết nối lại"
                    live.update(hilo_make_vbtool_layout(state))
                    time.sleep(2)
                    continue

                round_id = res_create['roundId']
                actual_card = hilo__get_game_card(
                    res_create,
                    create_payload.get('initialCard')
                )
                current_play_card = actual_card
                state["last_issue"] = round_id
                state["current_card"] = actual_card
                state["next_prediction"] = "—"
                state["last_result"] = "ĐANG CHẠY"
                state["log_text"] = f"Ván #{round_id} | Bài gốc: {hilo__hilo_rank_label(actual_card)}"
                live.update(hilo_make_vbtool_layout(state))

            except Exception:
                state["log_text"] = "Lỗi tạo ván. Vui lòng thử lại!"
                live.update(hilo_make_vbtool_layout(state))
                time.sleep(3)
                continue

            game_active = True
            opened_cards = 0
            while game_active:
                time.sleep(cfg['delay_bet'])

                # Kiểm tra key hiện tại để bảo đảm LOGIC VIP không bị dùng bởi KEY FREE.
                try:
                    key_valid, key_reason, key_is_vip = check_activation_valid(exit_on_expired=False)
                except Exception as exc:
                    key_valid, key_reason, key_is_vip = False, str(exc), False

                if not key_valid:
                    state["log_text"] = f"KEY không hợp lệ: {key_reason}"
                    live.update(hilo_make_vbtool_layout(state))
                    game_active = False
                    break

                # Giữ nguyên logic mà người dùng đã chọn trong menu HILO cũ.
                runtime_logic = str(cfg.get("analysis_logic", "free")).lower()
                if runtime_logic not in ("free", "vip"):
                    runtime_logic = "free"

                # KEY FREE tuyệt đối không được chạy LOGIC VIP.
                if runtime_logic == "vip" and not key_is_vip:
                    state["log_text"] = "❌ LOGIC VIP chỉ dành cho Key VIP."
                    live.update(hilo_make_vbtool_layout(state))
                    game_active = False
                    break

                if runtime_logic == "vip":
                    action = hilo_predict_action_vip(current_play_card, analysis_history)
                else:
                    action = hilo_predict_action_free(current_play_card, analysis_history)
                action_text = hilo_action_label(action)

                stats["predictions"] += 1
                state["model_stats"] = stats
                state["next_prediction"] = action_text
                state["current_bet"] = current_bet
                state["log_text"] = f"Phân tích: {hilo__hilo_rank_label(current_play_card)} → {action_text}"
                live.update(hilo_make_vbtool_layout(state))

                place_payload = {
                    "action": action,
                    "roundId": round_id,
                    "theme": "default",
                    "currency": cfg['currency'],
                    "amount": current_bet
                }

                try:
                    response = session.post(
                        "https://hilo.turbogg4u.online/api/bets/place",
                        json=place_payload,
                        timeout=(10, 15)
                    )
                    res_place = hilo__response_json(response, "PLACE")
                    if 'status' not in res_place:
                        state["log_text"] = "Ván kết thúc."
                        live.update(hilo_make_vbtool_layout(state))
                        game_active = False
                        continue
                except requests.exceptions.ReadTimeout:
                    state["log_text"] = "Kết nối không ổn định."
                    live.update(hilo_make_vbtool_layout(state))
                    game_active = False
                    last_result = 'none'
                    time.sleep(3)
                    continue
                except requests.exceptions.RequestException:
                    state["log_text"] = "Lỗi mạng khi đặt cược. Ván kết thúc."
                    live.update(hilo_make_vbtool_layout(state))
                    game_active = False
                    last_result = 'none'
                    time.sleep(3)
                    continue
                except Exception:
                    state["log_text"] = "Lỗi đặt cược. Ván kết thúc."
                    live.update(hilo_make_vbtool_layout(state))
                    game_active = False
                    last_result = 'none'
                    time.sleep(3)
                    continue

                status = res_place.get('status')
                drawn_card = hilo__get_game_card(res_place)

                try:
                    if res_place.get('balance') is not None:
                        cfg['current_balance'] = float(res_place['balance'])
                        state['balance'] = cfg['current_balance']
                except (TypeError, ValueError):
                    pass

                if status == 0:
                    # Một số response THUA không trả lại lá vừa mở.
                    # Không hiển thị "KHÔNG XÁC ĐỊNH"; chỉ hiện quan hệ khi có đủ 2 lá.
                    relation = hilo_compare_card_result(current_play_card, drawn_card)
                    state["last_result"] = f"THUA ({relation})" if relation else "THUA"
                    stats["losses"] += 1
                    stats["predictions"] = max(stats["predictions"], stats["wins"] + stats["losses"])
                    state["model_stats"] = stats
                    hilo__history_append(state, round_id, current_play_card, drawn_card, "THUA", -float(current_bet))
                    state["balance"] = cfg['current_balance']
                    drawn_label = hilo__hilo_rank_label(drawn_card) if drawn_card is not None else "—"
                    if relation:
                        state["log_text"] = f"💀 THUA | {hilo__hilo_rank_label(current_play_card)} → {drawn_label} ({relation})"
                    else:
                        state["log_text"] = f"💀 THUA | {hilo__hilo_rank_label(current_play_card)} → {drawn_label}"
                    live.update(hilo_make_vbtool_layout(state))
                    last_result = 'loss'
                    try:
                        profile_response = session.post(
                            "https://hilo.turbogg4u.online/api/common/profile",
                            json=cfg['login_payload'], timeout=(10, 10)
                        )
                        profile = hilo__response_json(profile_response, "PROFILE")
                        cfg['current_balance'] = float(profile.get('balance', cfg['current_balance']))
                        state['balance'] = cfg['current_balance']
                    except Exception:
                        pass
                    current_bet *= cfg['loss_multiplier']
                    state["current_bet"] = current_bet
                    game_active = False

                elif status == 1:
                    opened_cards += 1
                    next_coeffs = res_place.get('coefficients', {}).get('next', {})
                    previous_card = current_play_card
                    relation = hilo_compare_card_result(previous_card, drawn_card)
                    if drawn_card is not None:
                        current_play_card = drawn_card
                        state["current_card"] = drawn_card
                        analysis_history.append(drawn_card)
                        if len(analysis_history) > 100:
                            analysis_history = analysis_history[-100:]
                    state["last_result"] = f"MỞ {opened_cards}"
                    state["log_text"] = f"TIẾP TỤC | {action_text} → {hilo__hilo_rank_label(drawn_card)} ({relation or '—'})"
                    live.update(hilo_make_vbtool_layout(state))

                    if not next_coeffs or opened_cards >= cfg['target_opens']:
                        cashout_payload = {"roundId": round_id}
                        try:
                            response = session.post(
                                "https://hilo.turbogg4u.online/api/bets/cashout",
                                json=cashout_payload,
                                timeout=(10, 15)
                            )
                            res_cashout = hilo__response_json(response, "CASHOUT")
                            payout = float(res_cashout.get('payout', 0.0))
                            # He so thang: uu tien he so API neu co, neu khong thi tinh tu payout / bet.
                            raw_multiplier = (
                                res_cashout.get('multiplier')
                                or res_cashout.get('coefficient')
                                or res_cashout.get('coefficients', {}).get('current')
                                if isinstance(res_cashout.get('coefficients', {}), dict)
                                else None
                            )
                            try:
                                win_multiplier = float(raw_multiplier) if raw_multiplier is not None else (payout / current_bet if current_bet else 0.0)
                            except (TypeError, ValueError, ZeroDivisionError):
                                win_multiplier = payout / current_bet if current_bet else 0.0
                            last_result = 'win'
                            stats["wins"] += 1
                            stats["predictions"] = max(stats["predictions"], stats["wins"] + stats["losses"])
                            state["model_stats"] = stats
                            try:
                                profile_response = session.post(
                                    "https://hilo.turbogg4u.online/api/common/profile",
                                    json=cfg['login_payload'], timeout=(10, 10)
                                )
                                profile = hilo__response_json(profile_response, "PROFILE")
                                cfg['current_balance'] = float(profile.get('balance', cfg['current_balance']))
                            except Exception:
                                pass
                            state['balance'] = cfg['current_balance']
                            profit_now = cfg['current_balance'] - cfg['original_balance']
                            hilo__history_append(state, round_id, actual_card, current_play_card, "THẮNG", payout - current_bet)
                            state["last_result"] = "THẮNG"
                            state["log_text"] = f"✅ CHỐT LỜI | Nhân: x{win_multiplier:.2f} | Nhận: {payout:.2f} | Lãi/Lỗ: {profit_now:+.2f}"
                            current_bet = cfg['base_bet']
                            state["current_bet"] = current_bet
                            live.update(hilo_make_vbtool_layout(state))
                            game_active = False
                        except Exception:
                            state["log_text"] = "Lỗi chốt lời. Ván kết thúc."
                            live.update(hilo_make_vbtool_layout(state))
                            game_active = False
                else:
                    state["last_result"] = "KẾT THÚC"
                    state["log_text"] = f"không thể đặt cược"
                    live.update(hilo_make_vbtool_layout(state))
                    last_result = 'none'
                    game_active = False

            state["balance"] = cfg['current_balance']
            state["current_bet"] = current_bet
            current_profit = cfg['current_balance'] - cfg['original_balance']

            if cfg['target_profit'] > 0 and current_profit >= cfg['target_profit']:
                stop_reason = f"🎉 ĐÃ ĐẠT CHỈ TIÊU CHỐT LỜI (+{current_profit:.2f}). DỪNG TOOL!"
                state["log_text"] = stop_reason
                state["last_result"] = "CHỐT LỜI"
                live.update(hilo_make_vbtool_layout(state))
                break

            if cfg['stop_loss'] > 0 and current_profit <= -cfg['stop_loss']:
                stop_reason = f"💀 ĐÃ ĐẠT NGƯỠNG CẮT LỖ ({current_profit:.2f}). DỪNG TOOL AN TOÀN!"
                state["log_text"] = stop_reason
                state["last_result"] = "CẮT LỖ"
                live.update(hilo_make_vbtool_layout(state))
                break

    if stop_reason:
        console.print("\n")
        if "CHỐT LỜI" in stop_reason:
            console.print(
                Panel(
                    Text(stop_reason, justify="center"),
                    title="[bold green]🎉 CHỐT LỜI[/bold green]",
                    border_style=VBTOOL_COLORS["emerald"],
                    box=box.DOUBLE,
                    padding=(1, 3),
                    expand=False,
                )
            )
        else:
            console.print(
                Panel(
                    Text(stop_reason, justify="center"),
                    title="[bold red]💀 CẮT LỖ[/bold red]",
                    border_style=VBTOOL_COLORS["ruby"],
                    box=box.DOUBLE,
                    padding=(1, 3),
                    expand=False,
                )
            )

        time.sleep(3)
        return

# ================== PHẦN 5: MAIN ==================
def main():
    start_key_expiry_monitor()
    while True:
        console.clear()
        console.print(show_ultimate_header())
        console.print()

        is_valid, _, _ = show_key_menu()

        if not is_valid:
            console.print("[bold red]❌ Không thể kích hoạt.[/bold red]")
            time.sleep(2)
            continue

        while True:
            console.clear()
            choice = show_tool_selection()

            if choice == "1":
                console.print(
                    ">>> Loading...",
                    style=f"bold {VBTOOL_COLORS['white']}"
                )
                time.sleep(2)

                try:
                    main_vth()
                except KeyboardInterrupt:
                    raise

                # Quay lại menu chọn game thay vì rơi về màn nhập key.
                continue

            elif choice == "2":
                console.print(
                    ">>> Loading...",
                    style=f"bold {VBTOOL_COLORS['white']}"
                )
                time.sleep(2)

                try:
                    main_lotto()
                except KeyboardInterrupt:
                    pass

                # Quay lại menu chọn game sau khi thoát LOTTO.
                continue

            elif choice == "3":
                console.print(
                    ">>> Loading...",
                    style=f"bold {VBTOOL_COLORS['white']}"
                )
                time.sleep(2)

                try:
                    main_cdtd()
                except KeyboardInterrupt:
                    pass

                # Quay lại menu chọn game sau khi dừng tool 3.
                continue

            elif choice == "4":
                _, _, is_vip = check_activation_valid(exit_on_expired=False)
                if not is_vip:
                    console.print("[bold red]❌ CANH CODE XWORLD chỉ dành cho key VIP.[/bold red]")
                    console.print("[bold yellow]🔑 Hãy kích hoạt key VIP để sử dụng chức năng này.[/bold yellow]")
                    time.sleep(2)
                    continue

                console.print(
                    ">>> Loading...",
                    style=f"bold {VBTOOL_COLORS['white']}"
                )
                time.sleep(2)

                try:
                    xw_main()
                except KeyboardInterrupt:
                    raise

                # Khi dừng CANH CODE XWORLD, quay lại menu chọn game,
                # không quay ngược về menu nhập key.
                continue

            elif choice == "5":
                is_valid, _, _ = check_activation_valid(exit_on_expired=False)
                if not is_valid:
                    continue

                console.print(
                    ">>> Loading...",
                    style=f"bold {VBTOOL_COLORS['white']}"
                )
                time.sleep(2)

                try:
                    hilo_main()
                except KeyboardInterrupt:
                    pass

                continue

            else:
                console.print(
                    "[bold red]❌ Lựa chọn không hợp lệ.[/bold red]"
                )
                time.sleep(1)
                                
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Thoát.[/bold red]")
        force_exit_vbtool(0)
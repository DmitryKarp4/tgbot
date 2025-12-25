# check.py
import time
import requests
from config import VT_TOKEN

VT_UPLOAD_FILE_URL = "https://www.virustotal.com/api/v3/files"
VT_SUBMIT_URL_URL = "https://www.virustotal.com/api/v3/urls"
VT_ANALYSIS_URL = "https://www.virustotal.com/api/v3/analyses/{}"

HEADERS = {
    "x-apikey": VT_TOKEN
}

_PENDING_FILE_CHECK: set[int] = set()


def is_waiting_file(user_id: int) -> bool:
    return user_id in _PENDING_FILE_CHECK


def set_waiting_file(user_id: int, value: bool) -> None:
    if value:
        _PENDING_FILE_CHECK.add(user_id)
    else:
        _PENDING_FILE_CHECK.discard(user_id)


def _poll_analysis(analysis_id: str, timeout_sec: int = 60) -> dict | None:
    deadline = time.time() + timeout_sec

    while time.time() < deadline:
        r = requests.get(
            VT_ANALYSIS_URL.format(analysis_id),
            headers=HEADERS,
            timeout=30
        )

        if r.status_code != 200:
            time.sleep(2)
            continue

        data = r.json().get("data", {})
        attrs = data.get("attributes", {})
        if attrs.get("status") == "completed":
            return attrs

        time.sleep(2)

    return None


def _format_stats(attrs: dict, title: str) -> str:
    stats = attrs.get("stats", {})
    return (
        f"🛡 {title}\n"
        f"❌ Вредоносных: {stats.get('malicious', 0)}\n"
        f"⚠️ Подозрительных: {stats.get('suspicious', 0)}\n"
        f"✅ Безопасных: {stats.get('harmless', 0)}\n"
        f"➖ Не определено: {stats.get('undetected', 0)}"
    )


def check_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return "❌ Формат: /check https://example.com"

    r = requests.post(
        VT_SUBMIT_URL_URL,
        headers=HEADERS,
        data={"url": url},
        timeout=30
    )

    if r.status_code not in (200, 201):
        return f"❌ Ошибка VirusTotal (HTTP {r.status_code})"

    analysis_id = r.json()["data"]["id"]
    attrs = _poll_analysis(analysis_id)

    if not attrs:
        return "⚠️ Анализ ссылки не завершился вовремя."

    return _format_stats(attrs, f"Проверка ссылки:\n{url}")


def check_file_bytes(filename: str, content: bytes) -> str:
    r = requests.post(
        VT_UPLOAD_FILE_URL,
        headers=HEADERS,
        files={"file": (filename, content)},
        timeout=60
    )

    if r.status_code not in (200, 201):
        return f"❌ Ошибка загрузки файла (HTTP {r.status_code})"

    analysis_id = r.json()["data"]["id"]
    attrs = _poll_analysis(analysis_id, timeout_sec=90)

    if not attrs:
        return "⚠️ Анализ файла не завершился вовремя."

    return _format_stats(attrs, f"Проверка файла: {filename}")

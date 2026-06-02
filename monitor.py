"""Claude 状态监控 — 云端版（GitHub Actions 定时触发，每次运行一次即退出）"""

import json
import os
import sys
import io
from datetime import datetime, timezone
from urllib.request import Request, urlopen

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

STATUS_URL = "https://status.claude.com/api/v2/status.json"
STATE_FILE = "state.json"
TIMEOUT = 10
NTFY_SERVER = "https://ntfy.sh"

STATUS_MAP = {
    "none":     ("一切正常",  0),
    "minor":    ("轻微降级",  1),
    "major":    ("服务中断",  2),
    "critical": ("严重故障",  3),
}

EMOJI = {"none": "✅", "minor": "⚠️", "major": "🔴", "critical": "💀"}


def fetch_status():
    req = Request(STATUS_URL, headers={"User-Agent": "ClaudeMonitor/1.0"})
    with urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read())
    return data["status"]["indicator"], data["status"]["description"]


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"indicator": None, "description": ""}


def save_state(indicator: str, description: str):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"indicator": indicator, "description": description}, f)


def push_ntfy(topic: str, title: str, body: str, is_bad: bool):
    """通过 ntfy.sh 推送通知到 iPhone"""
    url = f"{NTFY_SERVER}/{topic}"
    data = body.encode("utf-8")
    # 标题只用 ASCII，中文放正文里（HTTP 头不支持中文）
    ascii_title = title.encode("ascii", errors="ignore").decode("ascii") or "Claude Status"
    headers = {
        "Title": ascii_title,
        "Priority": "5" if is_bad else "3",
        "Tags": "rotating_light" if is_bad else "white_check_mark",
    }
    try:
        req = Request(url, data=data, method="POST")
        with urlopen(req, timeout=10) as resp:
            ok = resp.status == 200
            print(f"[ntfy] {'成功' if ok else '失败'}: {ascii_title}")
            return ok
    except Exception as e:
        print(f"[ntfy] 异常: {e}")
        return False


def main():
    print(f"==> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC 开始检查...")

    topic = os.environ.get("NTFY_TOPIC", "")
    if not topic:
        print("[ntfy] NTFY_TOPIC 未配置，跳过推送")

    try:
        indicator, desc = fetch_status()
    except Exception as e:
        print(f"[错误] 获取状态失败: {e}")
        sys.exit(1)

    label, severity = STATUS_MAP.get(indicator, (indicator, 99))
    emoji = EMOJI.get(indicator, "?")
    print(f"[状态] {emoji} {label} — {desc}")

    prev = load_state()
    prev_indicator = prev.get("indicator")
    prev_desc = prev.get("description", "")

    save_state(indicator, desc)

    if prev_indicator is None:
        print("[首次运行] 已记录初始状态")
        if topic:
            push_ntfy(topic, "Claude Monitor ON", f"{emoji} {label}\n{desc}\nA社状态变化时实时推送。", is_bad=False)
        return

    if indicator == prev_indicator:
        print("[无变化] 状态保持一致")
        return

    _, prev_sev = STATUS_MAP.get(prev_indicator, ("?", 99))
    improved = prev_sev > severity

    now_str = datetime.now(timezone.utc).strftime("%m-%d %H:%M UTC")

    if improved:
        title = "Claude UP"
        body = f"{emoji} {label}\n{now_str}\n之前: {prev_desc}\n现在: {desc}"
        if topic:
            push_ntfy(topic, title, body, is_bad=False)
        print(f"[恢复] {prev_indicator} → {indicator}")
    elif severity > prev_sev:
        title = "Claude DOWN"
        body = f"{emoji} {label}\n{now_str}\n{desc}"
        if topic:
            push_ntfy(topic, title, body, is_bad=True)
        print(f"[故障] {prev_indicator} → {indicator}")
    else:
        print(f"[状态变更] {prev_indicator} → {indicator}（严重度未变）")


if __name__ == "__main__":
    main()

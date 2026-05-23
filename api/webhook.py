import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler


SYSTEM_PROMPT = (
    "Ты — интеллектуальный ассистент администратора JSON-RPC шлюза интеграции "
    "с платформой 1С:Предприятие. Помогаешь разбираться в работе системы. "
    "Отвечай чётко, кратко и по делу. Используй русский язык."
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


def tg_send(chat_id: int, text: str) -> None:
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
    r = urllib.request.Request(
        f"{TELEGRAM_API}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(r, timeout=10)


def groq_ask(text: str) -> str:
    payload = json.dumps({
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "max_tokens": 512,
    }).encode()
    r = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
        },
    )
    resp = json.loads(urllib.request.urlopen(r, timeout=30).read())
    return resp["choices"][0]["message"]["content"]


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        msg = body.get("message") or body.get("edited_message") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        text = (msg.get("text") or "").strip()

        if chat_id and text:
            if text.startswith("/debug"):
                key_len = len(GROQ_API_KEY)
                key_start = GROQ_API_KEY[:8] if key_len > 8 else "пусто"
                reply = f"GROQ_API_KEY: длина={key_len}, начало={key_start}"
            elif text.startswith("/start"):
                reply = (
                    "Привет! Я ассистент администратора JSON-RPC шлюза.\n\n"
                    "Задай вопрос о работе шлюза, интеграции с 1С, "
                    "настройке соединения или статусах транзакций."
                )
            else:
                try:
                    reply = groq_ask(text)
                except Exception as e:
                    reply = f"Ошибка AI: {e}"

            try:
                tg_send(chat_id, reply)
            except Exception:
                pass

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        pass

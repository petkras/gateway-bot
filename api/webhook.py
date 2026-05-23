import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler

from groq import Groq

SYSTEM_PROMPT = (
    "Ты — интеллектуальный ассистент администратора JSON-RPC шлюза интеграции "
    "с платформой 1С:Предприятие. Помогаешь разбираться в работе системы.\n\n"
    "Отвечаешь на вопросы о:\n"
    "- Протоколе JSON-RPC 2.0: структура запросов/ответов, коды ошибок\n"
    "- Настройке соединения: IP-адрес, порт, таймаут, авторизация\n"
    "- Статусах транзакций: success, error, pending — что означают\n"
    "- Интеграции с 1С: методы API, обработка ошибок, синхронизация\n"
    "- Мониторинге шлюза: метрики RPS, соединения, журнал транзакций\n\n"
    "Отвечай чётко, кратко и по делу. Используй русский язык."
)

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def tg_send(chat_id: int, text: str) -> None:
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
    r = urllib.request.Request(
        f"{TELEGRAM_API}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(r, timeout=10)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        msg = body.get("message") or body.get("edited_message") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        text = (msg.get("text") or "").strip()

        if chat_id and text:
            if text.startswith("/start"):
                reply = (
                    "Привет! Я ассистент администратора JSON-RPC шлюза.\n\n"
                    "Задай вопрос о работе шлюза, интеграции с 1С, "
                    "настройке соединения или статусах транзакций."
                )
            else:
                try:
                    completion = groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": text},
                        ],
                        max_tokens=512,
                    )
                    reply = completion.choices[0].message.content
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

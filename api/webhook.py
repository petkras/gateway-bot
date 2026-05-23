import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler


SYSTEM_PROMPT = (
    "Ты — интеллектуальный ассистент администратора JSON-RPC шлюза интеграции "
    "с платформой 1С:Предприятие. Помогаешь разбираться в работе системы. "
    "Отвечай чётко, кратко и по делу. Используй русский язык.\n\n"
    "У шлюза есть веб-панель администратора со следующими разделами:\n"
    "1. ГЛАВНАЯ ПАНЕЛЬ — показывает KPI в реальном времени: статус подключения (ONLINE/OFFLINE), "
    "транзакций за 24ч, запросов в минуту, ошибок обмена. "
    "Содержит архитектурную схему (Telegram Bot → JSON-RPC Gateway → 1С), "
    "кнопку «Отправить Ping» для проверки соединения и карточку AI-ассистента.\n"
    "2. ЖУРНАЛ ТРАНЗАКЦИЙ — таблица всех запросов к шлюзу: ID, тип операции, "
    "статус (Успешно/Ошибка/В очереди), длительность, дата и время. "
    "Есть поиск по тексту, фильтр по статусу и постраничная навигация.\n"
    "3. НАСТРОЙКИ — форма конфигурации подключения к серверу 1С: IP-адрес (IPv4), "
    "порт (1–65535), логин (только латиница/цифры/_, 3–20 символов), "
    "пароль (минимум 8 символов), API-токен. "
    "Кнопки: Сохранить (с валидацией), Тест соединения, Сбросить к дефолтам.\n"
    "Если пользователь спрашивает про настройку, мониторинг или журнал — "
    "объясняй со ссылкой на нужный раздел панели."
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
            "User-Agent": "Mozilla/5.0 (compatible; GatewayBot/1.0)",
        },
    )
    try:
        resp = json.loads(urllib.request.urlopen(r, timeout=30).read())
    except urllib.error.HTTPError as e:
        raise Exception(f"Groq {e.code}: {e.read().decode()[:300]}")
    return resp["choices"][0]["message"]["content"]


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

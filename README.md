# Gateway Bot

Telegram-бот для сопровождения администратора JSON-RPC шлюза интеграции с 1С:Предприятие.  
Использует языковую модель Llama 3.1 (Groq API) для ответов на вопросы о протоколе,
настройке соединения и диагностике ошибок.

## Архитектура

```
Telegram → POST /api/webhook → Vercel (Python) → Groq API → ответ в Telegram
```

## Требования

- Аккаунт Vercel ([vercel.com](https://vercel.com))
- Telegram Bot Token (получить через @BotFather)
- Groq API Key ([console.groq.com](https://console.groq.com))

## Переменные окружения

| Переменная       | Описание                  |
|------------------|---------------------------|
| `TELEGRAM_TOKEN` | Токен бота от @BotFather  |
| `GROQ_API_KEY`   | API-ключ сервиса Groq     |

## Развёртывание

1. Загрузить содержимое проекта в корень репозитория GitHub.
2. В Vercel → **Add New Project** → выбрать репозиторий.
3. Указать переменные окружения (см. таблицу выше).
4. После деплоя зарегистрировать webhook:

```
GET https://api.telegram.org/bot<TELEGRAM_TOKEN>/setWebhook?url=https://<PROJECT>.vercel.app/api/webhook
```

Ожидаемый ответ: `{"ok":true,"result":true}`

## Использование

Отправьте боту команду `/start` или любой вопрос об интеграции JSON-RPC / 1С.

# Launch Preflight Checker

**Launch Preflight Checker** — небольшой инструмент для технического специалиста запусков. Перед публикацией он принимает URL посадочной / Mini App и автоматически проверяет типовые точки отказа, которые обычно приходится проходить руками перед запуском.

## Что проверяет

- HTTP-доступность, редиректы и финальный URL;
- CTA регистрации;
- форму и наличие полей **Имя / Телефон / Email**;
- FAQ / accordion;
- UTM-метки и отдельно значение **`dojim`**;
- ключевые секции лендинга;
- даты, конфликт месяцев и уже прошедшие даты;
- до 30 HTTP(S)-ссылок на ошибки;
- mobile viewport;
- отдельно формирует ручной checklist для popup, отправки формы и NotiBot-дожимов 5/10 минут.

Результат: score `/100`, verdict (`READY`, `ATTENTION`, `BLOCKED`, `NOT_READY`) и карточки с evidence. Отчёт можно скопировать или скачать как JSON.

## Почему это отдельный инструмент

Он **не заменяет NotiBot** и не переписывает Mini App. Его задача — автоматизировать preflight/QA вокруг уже собранного запуска: быстро поймать забытый CTA, неполную форму, конфликт дат, потерянную UTM или битую ссылку до того, как пойдёт трафик.

## Telegram Mini Apps

`t.me/...?...startapp=...` может отдавать Telegram-обёртку, а не фактический DOM Mini App. Checker распознаёт такой URL и честно помечает ограничение. Для точной DOM-проверки лучше передать прямой **Web URL** из NotiBot: отправить `/weburl` подключённому боту и взять ссылку **«лендинг»**.

## Безопасность

Checker делает серверные HTTP-запросы, поэтому блокирует localhost, private/link-local/reserved IP и URL с credentials, валидирует каждый redirect, ограничивает таймаут, число ссылок и размер HTML. Подробнее: [`SECURITY.md`](SECURITY.md).

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Открыть: `http://localhost:8080`

## Docker

```bash
docker compose up -d --build
```

## API

```http
GET /api/check?url=https%3A%2F%2Fexample.com&max_links=20
```

Healthcheck:

```http
GET /health
```

## Тесты

```bash
python -m unittest discover -s tests -v
```

GitHub Actions запускает unit-тесты и HTTP smoke-test на каждый push/PR.

## Scope ручной проверки

Автоматически нельзя надёжно подтвердить бизнес-логику внутри Telegram/NotiBot без пользовательской сессии, поэтому checker отдельно напоминает проверить:

- открытие hero/popup;
- accordion/card interactions;
- успешную отправку формы;
- CTA → нужную страницу;
- автосообщения 5/10 минут;
- условие «форма не заполнена»;
- отсутствие дожимов после регистрации.

## Финальная перепроверка тестового

Подтверждённые пункты, manual-only ограничения Telegram WebView и найденный конфликт дат собраны в [`FINAL_QA.md`](FINAL_QA.md).

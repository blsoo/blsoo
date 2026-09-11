# Architecture

## Поток проверки

`Browser -> FastAPI -> URL validation -> HTTP fetch -> HTML parser -> checks -> JSON/UI report`

Основные компоненты:

- `app/main.py` — HTTP API, healthcheck и web UI;
- `app/checker.py` — URL validation, fetch, parsing, scoring и checks;
- `app/templates/index.html` — минимальный mobile-friendly интерфейс;
- `tests/` — unit tests для критичных helper'ов;
- `.github/workflows/` — CI;
- `Dockerfile` / `docker-compose.yml` / `render.yaml` — воспроизводимый запуск и деплой.

## Принцип проектирования

Инструмент не пытается симулировать Telegram и не выдаёт догадки за успешный QA. То, что можно доказать по HTTP/DOM, проверяется автоматически. То, что зависит от Telegram WebView, реальной пользовательской сессии или бизнес-логики NotiBot, явно маркируется как manual check.

## Scoring

Core checks формируют score `/100`. Критический fail даёт `BLOCKED`; предупреждения снижают score; ручные проверки остаются видимыми отдельно.

## Почему без headless browser

Первая версия намеренно использует статический HTTP/DOM анализ: это быстрее, дешевле и безопаснее для preflight большинства лендингов. Для SPA / динамического Mini App checker добавляет предупреждение о динамическом DOM. Следующий production-шаг — изолированный Playwright worker с жёсткой egress policy.

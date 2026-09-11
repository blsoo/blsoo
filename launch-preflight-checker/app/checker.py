from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

MAX_BODY_BYTES = 2_000_000
TIMEOUT = httpx.Timeout(8.0, connect=5.0)
USER_AGENT = "LaunchPreflightChecker/0.2 (+candidate-test-project)"

CTA_RE = re.compile(r"(зарегистрир|регистрац|register|sign\s*up|оставить\s*заявк|участв)", re.I)
FAQ_RE = re.compile(r"(faq|часто\s+задаваем|вопрос.{0,5}ответ)", re.I)
NAME_RE = re.compile(r"(^|[^a-z])(name|имя)([^a-z]|$)", re.I)
PHONE_RE = re.compile(r"(phone|tel|телефон|номер)", re.I)
EMAIL_RE = re.compile(r"(email|e-mail|почт)", re.I)
RANGE_NUMERIC_RE = re.compile(
    r"(?<!\d)(?P<d1>0?[1-9]|[12]\d|3[01])\s*[-–—]\s*(?P<d2>0?[1-9]|[12]\d|3[01])"
    r"[./-](?P<m>0?[1-9]|1[0-2])[./-](?P<y>20\d{2})(?!\d)"
)
SINGLE_NUMERIC_RE = re.compile(
    r"(?<!\d)(?P<d>0?[1-9]|[12]\d|3[01])[./-](?P<m>0?[1-9]|1[0-2])[./-](?P<y>20\d{2})(?!\d)"
)
MONTHS_RU = {
    "январ": 1,
    "феврал": 2,
    "март": 3,
    "апрел": 4,
    "ма": 5,
    "июн": 6,
    "июл": 7,
    "август": 8,
    "сентябр": 9,
    "октябр": 10,
    "ноябр": 11,
    "декабр": 12,
}
TEXTUAL_DATE_RE = re.compile(
    r"(?<!\d)(?P<d1>0?[1-9]|[12]\d|3[01])\s*[-–—]\s*(?P<d2>0?[1-9]|[12]\d|3[01])\s+"
    r"(?P<month>январ\w*|феврал\w*|март\w*|апрел\w*|ма[йя]\w*|июн\w*|июл\w*|август\w*|сентябр\w*|октябр\w*|ноябр\w*|декабр\w*)"
    r"(?:\s+(?P<year>20\d{2}))?",
    re.I,
)

CORE_CHECK_KEYS = {"availability", "cta", "form", "faq", "utm", "dates", "blocks", "links"}


@dataclass
class Check:
    key: str
    title: str
    status: str
    detail: str
    evidence: list[str]


@dataclass
class Report:
    input_url: str
    final_url: str | None
    checked_at: str
    score: int
    verdict: str
    summary: dict[str, int]
    checks: list[Check]
    discovered_links: int
    checked_links: int

    def to_dict(self) -> dict:
        return asdict(self)


def _host_is_public(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return False
    if not infos:
        return False
    for info in infos:
        raw = info[4][0]
        try:
            ip = ipaddress.ip_address(raw)
        except ValueError:
            return False
        if not ip.is_global:
            return False
    return True


def validate_target(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Разрешены только http/https URL")
    if not parsed.hostname:
        raise ValueError("URL не содержит домен")
    if parsed.username or parsed.password:
        raise ValueError("URL с логином/паролем не поддерживаются")
    if not _host_is_public(parsed.hostname):
        raise ValueError("Локальные/приватные адреса запрещены")
    return parsed.geturl()


async def _fetch_html(client: httpx.AsyncClient, url: str) -> tuple[httpx.Response, str]:
    current = validate_target(url)
    for _ in range(6):
        async with client.stream("GET", current, follow_redirects=False) as response:
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise ValueError("Редирект без Location")
                current = validate_target(urljoin(current, location))
                continue
            response.raise_for_status()
            ctype = response.headers.get("content-type", "").lower()
            if "text/html" not in ctype and "application/xhtml" not in ctype:
                raise ValueError(f"Ожидался HTML, получен Content-Type: {ctype or 'unknown'}")
            chunks: list[bytes] = []
            size = 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > MAX_BODY_BYTES:
                    raise ValueError("Страница больше 2 MB — проверка остановлена")
                chunks.append(chunk)
            body = b"".join(chunks)
            encoding = response.encoding or "utf-8"
            return response, body.decode(encoding, errors="replace")
    raise ValueError("Слишком много редиректов")


def _visible_text(soup: BeautifulSoup) -> str:
    clone = BeautifulSoup(str(soup), "html.parser")
    for tag in clone(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return " ".join(clone.stripped_strings)


def _field_text(tag) -> str:
    bits = [
        tag.get("name", ""),
        tag.get("id", ""),
        tag.get("type", ""),
        tag.get("placeholder", ""),
        tag.get("aria-label", ""),
    ]
    field_id = tag.get("id")
    if field_id:
        label = tag.find_previous("label", attrs={"for": field_id})
        if label:
            bits.append(label.get_text(" ", strip=True))
    parent_label = tag.find_parent("label")
    if parent_label:
        bits.append(parent_label.get_text(" ", strip=True))
    return " ".join(str(x) for x in bits if x)


def _extract_dates(text: str) -> list[str]:
    found: list[str] = []
    for m in TEXTUAL_DATE_RE.finditer(text):
        month_word = m.group("month").lower()
        month = next((v for k, v in MONTHS_RU.items() if month_word.startswith(k)), None)
        if month:
            y = m.group("year") or "????"
            found.append(f"{int(m.group('d1')):02d}-{int(m.group('d2')):02d}.{month:02d}.{y}")
    for m in RANGE_NUMERIC_RE.finditer(text):
        found.append(f"{int(m.group('d1')):02d}-{int(m.group('d2')):02d}.{int(m.group('m')):02d}.{m.group('y')}")
    for m in SINGLE_NUMERIC_RE.finditer(text):
        prefix = text[max(0, m.start() - 3) : m.start()]
        if "-" in prefix or "–" in prefix or "—" in prefix:
            continue
        found.append(f"{int(m.group('d')):02d}.{int(m.group('m')):02d}.{m.group('y')}")
    return list(dict.fromkeys(found))


def _date_end(token: str) -> date | None:
    if "????" in token:
        return None
    try:
        if "-" in token.split(".", 1)[0]:
            day_range, month, year = token.split(".")
            end_day = int(day_range.split("-")[-1])
            return date(int(year), int(month), end_day)
        day, month, year = token.split(".")
        return date(int(year), int(month), int(day))
    except (ValueError, IndexError):
        return None


def _candidate_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    out: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        url = urljoin(base_url, href)
        p = urlparse(url)
        if p.scheme in {"http", "https"} and p.hostname:
            out.append(url)
    return list(dict.fromkeys(out))


def _utm_evidence(links: list[str]) -> tuple[list[str], list[str]]:
    utm_links: list[str] = []
    dojim_links: list[str] = []
    for link in links:
        query = parse_qs(urlparse(link).query)
        utm_values: list[str] = []
        for key, values in query.items():
            if key.lower().startswith("utm_"):
                utm_values.extend(values)
        if utm_values:
            utm_links.append(link)
            if any("dojim" in value.lower() for value in utm_values):
                dojim_links.append(link)
    return utm_links, dojim_links


async def _safe_status(client: httpx.AsyncClient, url: str, method: str = "HEAD") -> int:
    current = validate_target(url)
    for _ in range(6):
        headers = {"Range": "bytes=0-512"} if method == "GET" else None
        response = await client.request(method, current, follow_redirects=False, headers=headers)
        if response.is_redirect:
            location = response.headers.get("location")
            if not location:
                return response.status_code
            current = validate_target(urljoin(current, location))
            continue
        return response.status_code
    raise ValueError("Слишком много редиректов")


async def _check_link(client: httpx.AsyncClient, url: str) -> tuple[str, int | None, str | None]:
    try:
        status = await _safe_status(client, url, "HEAD")
        if status in {405, 501}:
            status = await _safe_status(client, url, "GET")
        return url, status, None
    except Exception as exc:
        return url, None, str(exc)


def _telegram_wrapper_check(url: str) -> Check | None:
    parsed = urlparse(url)
    if parsed.hostname in {"t.me", "telegram.me", "www.t.me"} and "startapp" in parse_qs(parsed.query):
        return Check(
            "telegram_wrapper",
            "Telegram Mini App wrapper",
            "manual",
            "Это t.me/startapp-ссылка. Telegram может не отдавать фактический DOM Mini App серверному checker'у. Для точной DOM-проверки лучше прямой Web URL из NotiBot.",
            [url],
        )
    return None


async def inspect_url(url: str, max_links: int = 20) -> Report:
    target = validate_target(url)
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    checks: list[Check] = []

    wrapper = _telegram_wrapper_check(target)
    if wrapper:
        checks.append(wrapper)

    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers, max_redirects=5) as client:
        try:
            response, html = await _fetch_html(client, target)
        except Exception as exc:
            checks.append(Check("availability", "Страница открывается", "fail", str(exc), []))
            return _report(target, None, checks, 0, 0)

        final_url = str(response.url)
        checks.append(Check("availability", "Страница открывается", "pass", f"HTTP {response.status_code}; финальный URL: {final_url}", [final_url]))

        soup = BeautifulSoup(html, "html.parser")
        text = _visible_text(soup)
        lower = text.lower()

        ctas: list[str] = []
        for tag in soup.find_all(["a", "button", "input"]):
            candidate = tag.get_text(" ", strip=True) if tag.name != "input" else tag.get("value", "")
            if candidate and CTA_RE.search(candidate):
                ctas.append(candidate.strip())
        checks.append(Check("cta", "CTA регистрации найден", "pass" if ctas else "fail", f"Найдено CTA: {len(ctas)}" if ctas else "Не найден текст кнопки/ссылки регистрации", ctas[:5]))

        forms = soup.find_all("form")
        fields = soup.find_all(["input", "textarea", "select"])
        field_texts = [_field_text(field) for field in fields]
        has_name = any(NAME_RE.search(value) for value in field_texts)
        has_phone = any(PHONE_RE.search(value) or (field.name == "input" and field.get("type") == "tel") for field, value in zip(fields, field_texts))
        has_email = any(EMAIL_RE.search(value) or (field.name == "input" and field.get("type") == "email") for field, value in zip(fields, field_texts))
        matched_fields = [f"Имя: {'да' if has_name else 'нет'}", f"Телефон: {'да' if has_phone else 'нет'}", f"Email: {'да' if has_email else 'нет'}"]
        required_count = sum(1 for field in fields if field.has_attr("required"))
        matched_fields.append(f"HTML required: {required_count}/{len(fields)} полей")
        if has_name and has_phone and has_email:
            form_status = "pass"
            form_detail = f"Форм: {len(forms)}; комплект Имя/Телефон/Email найден"
        elif fields:
            form_status = "warn"
            form_detail = f"Поля формы найдены, но комплект Имя/Телефон/Email неполный; форм: {len(forms)}"
        else:
            form_status = "fail"
            form_detail = "HTML-поля формы не найдены"
        checks.append(Check("form", "Форма регистрации", form_status, form_detail, matched_fields))

        faq_hits = [value for value in soup.stripped_strings if FAQ_RE.search(value)]
        faqish = bool(faq_hits) or bool(soup.find_all(["details", "summary"]))
        checks.append(Check("faq", "FAQ найден", "pass" if faqish else "warn", "FAQ/accordion найден" if faqish else "FAQ не найден автоматически — нужна ручная проверка динамического блока", faq_hits[:5]))

        links = _candidate_links(soup, final_url)
        utm_links, dojim_links = _utm_evidence(links)
        if dojim_links:
            utm_status = "pass"
            utm_detail = f"Найдено ссылок с UTM dojim: {len(dojim_links)}"
            utm_evidence = dojim_links[:5]
        elif utm_links:
            utm_status = "warn"
            utm_detail = f"UTM есть ({len(utm_links)}), но значение dojim не найдено"
            utm_evidence = utm_links[:5]
        else:
            utm_status = "warn"
            utm_detail = "UTM в ссылках страницы не найдены"
            utm_evidence = []
        checks.append(Check("utm", "UTM / dojim", utm_status, utm_detail, utm_evidence))

        dates = _extract_dates(text)
        month_signatures = {match.group(1) for token in dates if (match := re.search(r"\.(\d{2})\.", token)) is not None}
        explicit_ends = [parsed for token in dates if (parsed := _date_end(token)) is not None]
        all_explicit_past = bool(explicit_ends) and all(value < datetime.now(timezone.utc).date() for value in explicit_ends)
        evidence_dates = dates[:10]
        if len(month_signatures) > 1:
            date_status = "warn"
            date_detail = "Найдены даты с разными месяцами — возможное противоречие"
        elif all_explicit_past:
            date_status = "warn"
            date_detail = "Распознанные даты уже прошли — проверьте актуальность запуска"
        elif dates:
            date_status = "pass"
            date_detail = f"Найдено вариантов дат: {len(dates)}"
        else:
            date_status = "manual"
            date_detail = "Дата не распознана автоматически"
        if all_explicit_past:
            evidence_dates.append("⚠ Все даты с указанным годом уже в прошлом")
        checks.append(Check("dates", "Согласованность дат", date_status, date_detail, evidence_dates))

        required_phrases = {
            "Времена стабильного трафика прошли": "Времена стабильного трафика прошли",
            "Что будет на конференции": "Что будет на конференции",
            "Спикерский состав": "Спикерский состав",
        }
        missing = [label for label, phrase in required_phrases.items() if phrase.lower() not in lower]
        checks.append(Check("blocks", "Ключевые блоки", "pass" if not missing else "warn", "Все ключевые секции найдены" if not missing else "Не найдены автоматически: " + ", ".join(missing), [label for label in required_phrases if label not in missing]))

        viewport = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})
        checks.append(Check("mobile", "Mobile viewport", "pass" if viewport and "width=device-width" in viewport.get("content", "") else "warn", "Mobile viewport настроен" if viewport else "meta viewport не найден — проверьте mobile-first отображение", [viewport.get("content", "")] if viewport else []))

        sample = links[: max(0, min(max_links, 30))]
        results = await asyncio.gather(*[_check_link(client, link) for link in sample]) if sample else []
        broken = [f"{link} — {error or status}" for link, status, error in results if error or (status is not None and status >= 400)]
        checks.append(Check("links", "Ссылки работают", "pass" if results and not broken else ("warn" if not results else "fail"), f"Проверено {len(results)} ссылок, битых не найдено" if results and not broken else ("На странице нет проверяемых http(s)-ссылок" if not results else f"Проблемных ссылок: {len(broken)}"), broken[:10]))

        script_count = len(soup.find_all("script"))
        if len(text) < 120 and script_count >= 3:
            checks.append(Check("dynamic_dom", "Динамический DOM", "manual", "Страница похожа на JS-приложение: часть блоков может появляться только после выполнения JavaScript. Результат DOM-проверки нужно подтвердить вручную.", [f"Видимого текста: {len(text)} символов", f"script-тегов: {script_count}"]))

        checks.append(Check("interactive", "Интерактив: popup / accordion / отправка формы", "manual", "Проверь в Telegram Mini App: hero/popup, раскрытие карточек и FAQ, успешную отправку формы и возврат по CTA.", []))
        checks.append(Check("followups", "Дожимы 5/10 минут", "manual", "Проверь в NotiBot: триггер открытия страницы, условие «форма не заполнена», задержки 5/10 минут, активность обоих сообщений и UTM dojim.", []))

    return _report(target, final_url, checks, len(links), len(sample))


def _report(input_url: str, final_url: str | None, checks: list[Check], discovered: int, checked: int) -> Report:
    weights = {"pass": 1.0, "warn": 0.55, "manual": 0.7, "fail": 0.0}
    scored = [check for check in checks if check.key in CORE_CHECK_KEYS]
    score = round(100 * sum(weights[check.status] for check in scored) / max(1, len(scored)))
    summary = {status: sum(1 for check in checks if check.status == status) for status in ("pass", "warn", "fail", "manual")}
    if any(check.status == "fail" for check in scored):
        verdict = "BLOCKED"
    elif score >= 85:
        verdict = "READY"
    elif score >= 65:
        verdict = "ATTENTION"
    else:
        verdict = "NOT_READY"
    return Report(input_url=input_url, final_url=final_url, checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds"), score=score, verdict=verdict, summary=summary, checks=checks, discovered_links=discovered, checked_links=checked)

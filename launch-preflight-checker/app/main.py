from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .checker import inspect_url

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(
    title="Launch Preflight Checker",
    description="Preflight QA for landing pages and Telegram Mini Apps before a launch.",
    version="0.2.1",
)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/health")
async def health():
    return {"ok": True, "version": app.version}


@app.get("/api/check")
async def check(url: str = Query(..., min_length=8), max_links: int = Query(20, ge=0, le=30)):
    try:
        report = await inspect_url(url, max_links=max_links)
        # A t.me/startapp page is only a Telegram wrapper, not proof that the
        # Mini App DOM itself passed QA. Never expose a misleading READY verdict
        # for that input even if Telegram's public wrapper HTML looks healthy.
        if any(item.key == "telegram_wrapper" for item in report.checks) and report.verdict == "READY":
            report.verdict = "ATTENTION"
        return report.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

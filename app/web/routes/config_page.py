from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.web.server import templates

router = APIRouter()


@router.get("/config", response_class=HTMLResponse)
async def config_view(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "config.html",
        {"active": "config", "page_title": "Config"},
    )

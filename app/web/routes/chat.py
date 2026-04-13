from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.web.server import templates

router = APIRouter()


@router.get("/chat", response_class=HTMLResponse)
async def chat(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "chat.html",
        {"active": "chat", "page_title": "Chat"},
    )

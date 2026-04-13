from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.web.server import templates

router = APIRouter()


@router.get("/documents", response_class=HTMLResponse)
async def documents(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "documents.html",
        {"active": "documents", "page_title": "Documents"},
    )

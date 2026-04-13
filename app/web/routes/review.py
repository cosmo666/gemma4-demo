from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.web.server import templates

router = APIRouter()


@router.get("/review", response_class=HTMLResponse)
async def review(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "review.html",
        {"active": "review", "page_title": "Review queue", "pending_count": 0},
    )

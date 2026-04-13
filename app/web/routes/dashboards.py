from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.web.server import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
@router.get("/dashboards", response_class=HTMLResponse)
async def dashboards(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "dashboards/index.html",
        {"active": "dashboards", "page_title": "Dashboards"},
    )

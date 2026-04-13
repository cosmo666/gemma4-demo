from fastapi import APIRouter

from app.web.routes import chat, config_page, dashboards, documents, review

router = APIRouter()
router.include_router(dashboards.router)
router.include_router(review.router)
router.include_router(documents.router)
router.include_router(chat.router)
router.include_router(config_page.router)

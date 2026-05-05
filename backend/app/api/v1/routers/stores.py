import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.store_repository import StoreRepository
from app.schemas.store import StoreRead

router = APIRouter(prefix="/stores", tags=["stores"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[StoreRead])
async def list_stores(db: Session = Depends(get_db)) -> list[StoreRead]:
    logger.info("api_list_stores")
    stores = StoreRepository(db).list_all()
    return [StoreRead.model_validate(store) for store in stores]

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Search
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Any
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class SearchResponse(BaseModel):
    source_people_ids: Any
    source_id: int
    name: Any
    updated_at: datetime
    source_company_ids: List[str]
    id: int
    created_at: datetime


@router.get("/searches/{search_id}")
def get_search(
    search_id: int,
    _=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        search = db.query(Search).where(Search.id == search_id).first()

        if not search:
            raise HTTPException(status_code=404, detail="Search not found")

        return search

    except SQLAlchemyError as e:
        print(f"SQLAlchemyError: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Company, Person, Signal
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from pydantic import BaseModel
from typing import Dict
from datetime import datetime
from typing import Any


router = APIRouter()


class SourceData(BaseModel):
    entity_text: List[str]
    event_text: List[str]
    crawled_at: str
    doc_cluster_id: str
    doc_id: str
    doc_sentiment: float
    doc_source: str
    doc_title: str
    doc_type: str
    doc_url: str
    entity_accern_id: str
    entity_hits: List[str]
    entity_name: str
    entity_relevance: float
    entity_sentiment: float
    entity_ticker: str
    entity_type: str
    event: str
    event_accern_id: str
    event_group: str
    event_hits: List[str]
    event_relevance: float
    event_sentiment: float
    harvested_at: str
    primary_signal: bool
    provider_id: int
    published_at: str
    signal_id: str
    signal_relevance: float
    signal_sentiment: float
    signal_tag: str


class NerTags(BaseModel):
    person: Dict[str, Any]
    org: Dict[str, Any]
    gpe: Dict[str, Any]


class ModelItem(BaseModel):
    name: Any
    id: int
    source_company_ids: List[str]
    source_people_ids: Any
    updated_at: datetime
    source_id: int
    source_data: SourceData
    ner_tags: NerTags
    created_at: datetime


@router.get("/signals/{signal_id}")
def get_signal(
    signal_id: int,
    _=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        signal = db.query(Signal).where(Signal.id == signal_id).first()

        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")

        return signal
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

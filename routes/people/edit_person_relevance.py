from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from auth import get_current_user
from database import get_db
from models import Person

router = APIRouter()


class PersonRelevanceUpdate(BaseModel):
    id: int
    relevence_stage: str


@router.post("/edit_person_relevence", status_code=status.HTTP_200_OK)
async def edit_person_relevance(
    person_data: PersonRelevanceUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        # Find the person by ID
        person = db.query(Person).filter(Person.id == person_data.id).first()

        if not person:
            raise HTTPException(status_code=404, detail="Person not found")

        source_person_id = person.source_person_id

        db.query(Person).filter(Person.source_person_id == source_person_id).update(
            {Person.relevence_stage: person_data.relevence_stage},
            synchronize_session=False,
        )
        db.commit()

        return {
            "message": "Relevance stage updated successfully for all related persons"
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while updating the relevance stage.",
        )

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

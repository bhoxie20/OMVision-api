from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from pydantic import BaseModel
from auth import get_current_user
from database import get_db
from models import Person
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from models import Person

router = APIRouter()


class HidePeopleRequest(BaseModel):
    ids: List[int]


@router.post("/peoples/hide", response_model=dict)
def hide_people(
    request: HidePeopleRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        people = db.query(Person).filter(Person.id.in_(request.ids)).all()

        if not people:
            raise HTTPException(status_code=404, detail="People not found")

        source_person_ids = {
            person.source_person_id for person in people if person.source_person_id
        }

        if source_person_ids:
            people_to_hide = (
                db.query(Person)
                .filter(Person.source_person_id.in_(source_person_ids))
                .all()
            )

            for person in people_to_hide:
                person.is_hidden = True

        for person in people:
            person.is_hidden = True

        db.commit()

        return {"message": "People hidden successfully"}

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

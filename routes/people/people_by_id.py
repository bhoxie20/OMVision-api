from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Person
from fastapi import HTTPException

router = APIRouter()


@router.get("/peoples/{person_id}")
def get_person(
    person_id: int,
    _=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    person = db.query(Person).where(Person.id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    return person

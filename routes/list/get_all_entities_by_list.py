from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from auth import get_current_user
from models import Company, List as DBList, ListEntityAssociation, Person
from database import get_db

router = APIRouter()


class CompanyResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class PersonResponse(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class EntitiesByListResponse(BaseModel):
    companies: Optional[List[CompanyResponse]] = None
    people: Optional[List[PersonResponse]] = None


@router.get("/lists/{list_id}/entities", response_model=EntitiesByListResponse)
def get_entities_by_list(
    list_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    db_list = db.query(DBList).filter(DBList.id == list_id).first()

    if not db_list:
        raise HTTPException(status_code=404, detail="List not found.")

    companies = None
    people = None

    if db_list.type == "company":
        company_models = (
            db.query(Company)
            .join(ListEntityAssociation, ListEntityAssociation.entity_id == Company.id)
            .filter(
                ListEntityAssociation.list_id == list_id,
                ListEntityAssociation.entity_type == "company",
            )
            .all()
        )
        companies = [company for company in company_models]

    elif db_list.type == "person":
        person_models = (
            db.query(Person)
            .join(ListEntityAssociation, ListEntityAssociation.entity_id == Person.id)
            .filter(
                ListEntityAssociation.list_id == list_id,
                ListEntityAssociation.entity_type == "person",
            )
            .all()
        )
        people = [person for person in person_models]

    else:
        raise HTTPException(status_code=400, detail="Invalid list type.")

    return EntitiesByListResponse(companies=companies, people=people)

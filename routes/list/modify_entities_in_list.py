from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Literal
from auth import get_current_user
from models import (
    List as DBList,
    ListEntityAssociation,
    Company,
    Person,
)
from database import get_db
from datetime import datetime

router = APIRouter()


class ModifyListRequest(BaseModel):
    operation: Literal["add", "remove"] = Field(
        ..., description="Operation to perform: 'add' or 'remove'"
    )
    item_ids: List[int] = Field(
        ..., description="List of item (company/person) IDs to add or remove"
    )


class ModifyListResponse(BaseModel):
    message: str
    already_exists: int


@router.post("/lists/{list_id}/modify", response_model=ModifyListResponse)
def modify_list(
    list_id: int,
    modify_data: ModifyListRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    print("modify_data", modify_data)
    # Fetch the list
    db_list = db.query(DBList).filter(DBList.id == list_id).first()

    if not db_list:
        raise HTTPException(status_code=404, detail="List not found.")

    if modify_data.operation not in ["add", "remove"]:
        raise HTTPException(
            status_code=400, detail="Invalid operation. Must be 'add' or 'remove'."
        )

    already_exists = 0

    # Handle company lists
    if db_list.type == "company":
        companies = db.query(Company).filter(Company.id.in_(modify_data.item_ids)).all()

        if not companies:
            raise HTTPException(
                status_code=404, detail="No companies found with given IDs."
            )

        if modify_data.operation == "add":
            # Get existing associations for this list
            existing_associations = (
                db.query(ListEntityAssociation)
                .filter(
                    ListEntityAssociation.list_id == list_id,
                    ListEntityAssociation.entity_type == "company",
                )
                .all()
            )
            existing_company_ids = set(
                assoc.entity_id for assoc in existing_associations
            )

            for company in companies:
                if company.id in existing_company_ids:
                    already_exists += 1
                    continue
                else:
                    association = ListEntityAssociation(
                        list_id=list_id,
                        entity_id=company.id,
                        entity_type="company",
                    )
                    db.add(association)
        elif modify_data.operation == "remove":
            db.query(ListEntityAssociation).filter(
                ListEntityAssociation.list_id == list_id,
                ListEntityAssociation.entity_id.in_(
                    [company.id for company in companies]
                ),
                ListEntityAssociation.entity_type == "company",
            ).delete(synchronize_session=False)

    # Handle person lists
    elif db_list.type == "person":
        people = db.query(Person).filter(Person.id.in_(modify_data.item_ids)).all()

        if not people:
            raise HTTPException(
                status_code=404, detail="No people found with given IDs."
            )

        if modify_data.operation == "add":
            # Get existing associations for this list
            existing_associations = (
                db.query(ListEntityAssociation)
                .filter(
                    ListEntityAssociation.list_id == list_id,
                    ListEntityAssociation.entity_type == "person",
                )
                .all()
            )
            existing_person_ids = set(
                assoc.entity_id for assoc in existing_associations
            )

            for person in people:
                if person.id in existing_person_ids:
                    already_exists += 1
                    continue
                else:
                    association = ListEntityAssociation(
                        list_id=list_id,
                        entity_id=person.id,
                        entity_type="person",
                    )
                    db.add(association)
        elif modify_data.operation == "remove":
            db.query(ListEntityAssociation).filter(
                ListEntityAssociation.list_id == list_id,
                ListEntityAssociation.entity_id.in_([person.id for person in people]),
                ListEntityAssociation.entity_type == "person",
            ).delete(synchronize_session=False)

    db.commit()

    return ModifyListResponse(
        message=f"Successfully {modify_data.operation}ed items to/from the list.",
        already_exists=already_exists,
    )

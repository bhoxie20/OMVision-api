from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    create_engine,
    Column,
    String,
    Integer,
    Float,
    Text,
    JSON,
    ForeignKey,
    Table,
    func,
)
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime as SQLAlchemyDateTime

from database import Base, engine


# Custom UTC timestamp function for SQLAlchemy
class utcnow(expression.FunctionElement):
    type = SQLAlchemyDateTime()
    inherit_cache = True


@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kw):
    return "timezone('utc', current_timestamp)"


# Association table for many-to-many relationship between people and companies
person_company_association = Table(
    "person_company_association",
    Base.metadata,
    Column("person_id", Integer, ForeignKey("person.id")),
    Column("company_id", Integer, ForeignKey("company.id")),
)


class Source(Base):
    __tablename__ = "source"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    description = Column(String)
    base_url = Column(Text)
    channels = Column(ARRAY(JSON))
    created_at = Column(DateTime, default=utcnow(), nullable=False)
    updated_at = Column(DateTime, default=utcnow(), onupdate=utcnow(), nullable=True)

    # One-to-many relationship with signals and searches
    signals = relationship("Signal", backref="source")
    searches = relationship("Search", backref="source")


class Search(Base):
    __tablename__ = "search"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("source.id"))
    name = Column(Text)
    source_company_ids = Column(ARRAY(Text))
    source_people_ids = Column(ARRAY(Text))
    created_at = Column(DateTime, default=utcnow(), nullable=False)
    updated_at = Column(DateTime, default=utcnow(), onupdate=utcnow(), nullable=True)


class Signal(Base):
    __tablename__ = "signal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("source.id"))
    source_data = Column(JSON)
    name = Column(Text)
    ner_tags = Column(JSON)
    source_company_ids = Column(ARRAY(Text))
    source_people_ids = Column(ARRAY(Text))
    created_at = Column(DateTime, default=utcnow(), nullable=False)
    updated_at = Column(DateTime, default=utcnow(), onupdate=utcnow(), nullable=True)


class Company(Base):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    search_id = Column(Integer)
    signal_id = Column(Integer)
    source_company_id = Column(Integer)
    type = Column(Text)
    name = Column(Text)
    name_aliases = Column(ARRAY(Text))
    legal_name = Column(Text)
    description = Column(Text)
    contact = Column(JSON)
    founding_date = Column(JSON)
    website_urls = Column(JSON)
    logo_url = Column(Text)
    ownership_status = Column(Text)
    location = Column(JSON)
    tags = Column(ARRAY(JSON))
    socials = Column(JSON)
    comments = Column(Text)
    relevence_stage = Column(Text)
    is_hidden = Column(Boolean, default=False)
    rank = Column(Float)
    related_companies = Column(JSON)
    created_at = Column(DateTime, default=utcnow(), nullable=False)
    updated_at = Column(DateTime, default=utcnow(), onupdate=utcnow(), nullable=True)

    # Many-to-many relationship with people
    people = relationship(
        "Person", secondary=person_company_association, back_populates="companies"
    )
    lists = relationship(
        "ListEntityAssociation",
        primaryjoin=(
            "and_("
            "ListEntityAssociation.entity_id == foreign(Company.id), "
            "ListEntityAssociation.entity_type == 'company'"
            ")"
        ),
        back_populates="company",
        viewonly=True,
    )


class CompanyMetric(Base):
    __tablename__ = "company_metric"

    highlights = Column(ARRAY(JSON))
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company.id"))
    stage = Column(Text)
    headcount = Column(Integer)
    traction_metrics = Column(JSON)
    funding = Column(JSON)
    employees = Column(JSON)
    employee_highlights = Column(ARRAY(JSON))
    investor_urn = Column(Text)
    funding_rounds = Column(ARRAY(JSON))
    created_at = Column(DateTime, default=utcnow(), nullable=False)
    updated_at = Column(DateTime, default=utcnow(), onupdate=utcnow(), nullable=True)


class Person(Base):
    __tablename__ = "person"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(Text)
    last_name = Column(Text)
    profile_picture_url = Column(Text)
    contact = Column(JSON)
    location = Column(JSON)
    education = Column(ARRAY(JSON))
    socials = Column(JSON)
    experience = Column(ARRAY(JSON))
    highlights = Column(ARRAY(JSON))
    linkedin_headline = Column(Text)
    source_person_id = Column(Integer)
    search_id = Column(Integer)
    signal_id = Column(Integer)
    awards = Column(ARRAY(Text))
    recommendations = Column(ARRAY(Text))
    current_company_urns = Column(ARRAY(Text))
    linkedin_profile_visibility_type = Column(Text)
    comments = Column(Text)
    relevence_stage = Column(Text)
    is_hidden = Column(Boolean, default=False)
    last_refreshed_at = Column(DateTime)
    last_checked_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow(), nullable=False)
    updated_at = Column(DateTime, default=utcnow(), onupdate=utcnow(), nullable=True)

    # Many-to-many relationship with companies
    companies = relationship(
        "Company", secondary=person_company_association, back_populates="people"
    )
    lists = relationship(
        "ListEntityAssociation",
        primaryjoin=(
            "and_("
            "ListEntityAssociation.entity_id == foreign(Person.id), "
            "ListEntityAssociation.entity_type == 'person'"
            ")"
        ),
        back_populates="person",
        viewonly=True,
    )


class List(Base):
    __tablename__ = "list"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String, index=True)
    created_at = Column(DateTime, default=utcnow(), nullable=False)
    updated_at = Column(DateTime, default=utcnow(), onupdate=utcnow(), nullable=True)

    entities = relationship(
        "ListEntityAssociation", back_populates="list", cascade="all, delete-orphan"
    )


class ListEntityAssociation(Base):
    __tablename__ = "list_entity_association"

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_id = Column(Integer, ForeignKey("list.id"), nullable=False)
    entity_id = Column(Integer, nullable=False)
    entity_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=utcnow(), nullable=False)

    list = relationship("List", back_populates="entities")

    # Relationships to Company and Person
    company = relationship(
        "Company",
        primaryjoin=(
            "and_("
            "ListEntityAssociation.entity_id == foreign(Company.id), "
            "ListEntityAssociation.entity_type == 'company'"
            ")"
        ),
        viewonly=True,
    )

    person = relationship(
        "Person",
        primaryjoin=(
            "and_("
            "ListEntityAssociation.entity_id == foreign(Person.id), "
            "ListEntityAssociation.entity_type == 'person'"
            ")"
        ),
        viewonly=True,
    )

    __mapper_args__ = {
        "polymorphic_on": entity_type,
    }

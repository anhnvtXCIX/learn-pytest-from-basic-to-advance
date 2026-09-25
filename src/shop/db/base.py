"""The declarative base, shared by every mapped table.

The explicit naming convention matters for testing: without it, SQLAlchemy lets the
database pick constraint names, which come out different on SQLite vs Postgres. That
divergence makes Alembic's autogenerate produce different migrations depending on
which engine you happened to run it against -- exactly the kind of "works on my
(SQLite) machine" bug this repo's two-tier test strategy exists to catch.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

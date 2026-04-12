from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from .database import BookTable


def get_books(db: Session) -> list[BookTable]:
    return list(db.scalars(select(BookTable).options(selectinload(BookTable.genres)).order_by(BookTable.id)).all())
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from .database import BookTable


def get_books(db: Session) -> list[BookTable]:
    # selectinload избегает n+1 запросов и подгружает все жанры всего лишь вторым запросом
    return list(db.scalars(select(BookTable).
                options(selectinload(BookTable.genres)).
                order_by(BookTable.id)).
                all()
                )

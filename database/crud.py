from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from .database import BookTable, GenreTable


def get_books(db: Session) -> list[BookTable]:
    # selectinload избегает n+1 запросов и подгружает все жанры всего лишь вторым запросом
    return list(db.scalars(select(BookTable).
                options(selectinload(BookTable.genres)).
                order_by(BookTable.id)).
                all()
                )


def get_genres(db: Session) -> list[GenreTable]:
    return list(db.scalars(select(GenreTable).
                order_by(GenreTable.id)).
                all()
                )

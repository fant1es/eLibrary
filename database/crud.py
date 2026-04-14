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


def add_genre(db: Session, genre_name: str):
    new_genre = GenreTable(name=genre_name)
    db.add(new_genre)
    db.commit()


def delete_genres(db: Session, genre_ids: list[int]):
    for genre_id in genre_ids:
        genre = db.get(GenreTable, genre_id)
        if genre:
            db.delete(genre)
    db.commit()
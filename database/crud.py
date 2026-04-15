from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from .database import BookTable, GenreTable

import os
from dotenv import load_dotenv

load_dotenv()

COVERS_DIR = os.getenv("COVERS_DIR", "content/covers")
BOOKS_DIR = os.getenv("BOOKS_DIR", "content/books")

def get_books(db: Session) -> list[BookTable]:
    # selectinload избегает n+1 запросов и подгружает все жанры всего лишь вторым запросом
    return list(db.scalars(select(BookTable).
                options(selectinload(BookTable.genres)).
                order_by(BookTable.id)).
                all()
                )


def add_book(db: Session, new_book: BookTable):
    db.add(new_book)
    db.commit()


def delete_book(db: Session, del_id: int):
    del_book = db.get(BookTable, del_id)
    if del_book:
        if del_book.cover_path:
            os.remove(os.path.join(COVERS_DIR, str(del_book.cover_path)))
        if del_book.file_path:
            os.remove(os.path.join(BOOKS_DIR, str(del_book.file_path)))

        db.delete(del_book)
        db.commit()
        return True

    return False


def get_genres(db: Session) -> list[GenreTable]:
    return list(db.scalars(select(GenreTable).
                order_by(GenreTable.id)).
                all()
                )


def get_genre(db: Session, genre_id: int):
    return db.get(GenreTable, genre_id)


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


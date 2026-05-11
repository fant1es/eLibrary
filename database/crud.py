from datetime import datetime
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from .database import BookTable, GenreTable
from .database import UserTable, UserRole
import os
import bcrypt
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
    # Обновляем для получения автоинкрменета на id и актуальных значений
    db.refresh(new_book)


def delete_book(db: Session, del_id: int):
    del_book = db.get(BookTable, del_id)
    if del_book:
        try:
            if del_book.cover_path:
                os.remove(os.path.join(COVERS_DIR, str(del_book.cover_path)))
            if del_book.file_path:
                os.remove(os.path.join(BOOKS_DIR, str(del_book.file_path)))
        except FileNotFoundError:
            pass

        db.delete(del_book)
        db.commit()
        return True

    return False


def update_book(db: Session, payload: dict, new_book_filename: str | None, new_cover_filename: str | None):
    book = db.get(BookTable, payload["id"])
    if not book:
        return False

    book.name = payload["name"]
    book.author = payload["author"]
    book.summary = payload["summary"]
    book.rating = payload["rating"]
    book.public_date = datetime.strptime(payload["public_date"], "%d.%m.%Y").date()

    # Обновляем жанры
    genres = [get_genre(db, gid) for gid in payload.get("genre_ids", [])]
    book.genres = [g for g in genres if g]

    # Обновляем файл книги, если передан новый
    if new_book_filename:
        if book.file_path:
            try:
                os.remove(os.path.join(BOOKS_DIR, str(book.file_path)))
            except FileNotFoundError:
                pass
        book.file_path = new_book_filename

    # Обновляем обложку, если передана новая
    if new_cover_filename:
        if book.cover_path:
            try:
                os.remove(os.path.join(COVERS_DIR, str(book.cover_path)))
            except FileNotFoundError:
                pass
        book.cover_path = new_cover_filename

    db.commit()
    return True


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


def authenticate_user(session, username, password):
    user = session.query(UserTable).filter(UserTable.username == username).first()

    if user:
        # bcrypt.checkpw ожидает байты, поэтому используем .encode()
        password_bytes = password.encode('utf-8')
        hashed_bytes = user.password_hash.encode('utf-8') if isinstance(user.password_hash, str) else user.password_hash

        if bcrypt.checkpw(password_bytes, hashed_bytes):
            return user
    return None


def register_user(session, username, password):
    # Проверяем, существует ли пользователь
    existing_user = session.query(UserTable).filter(UserTable.username == username).first()
    if existing_user:
        return False, "Пользователь с таким именем уже существует"

    try:
        # Генерируем соль для пароля
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

        new_user = UserTable(
            username=username,
            password_hash=hashed_password.decode('utf-8'),
            role=UserRole.user
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return True, new_user

    except Exception as e:
        session.rollback()
        return False, f"Ошибка при регистрации: {e}"
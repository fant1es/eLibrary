from datetime import date
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship, sessionmaker
from sqlalchemy import String, Text, Date, Float, Table, Column, ForeignKey, create_engine
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

# Загружаем переменные из .env в систему
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise ValueError("Не все переменные окружения загружены. Проверь .env файл.")

DATABASE_URL = f"postgresql+psycopg2://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


# Класс для работы со всеми таблицами
class Base(DeclarativeBase):
    pass


# Для ассоциации книг с жанрами и наоборот
book_genre_association = Table(
    "book_genre_association",
    Base.metadata,
    Column("book_id", ForeignKey("books.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True),
)


# Класс для жанров (есть т.к. жанров у книги может быть несколько)
class GenreTable(Base):
    __tablename__ = "genres"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    # Класс в кавычках потому что на данной строке он еще не объявлен
    books: Mapped[list["BookTable"]] = relationship(
        secondary=book_genre_association,
        back_populates="genres"
    )


# Общий класс для работы с таблицей и окном клиента
class BookTable(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    cover_path: Mapped[str] = mapped_column(String(255), nullable=True)
    public_date: Mapped[date] = mapped_column(Date, nullable=False)

    genres: Mapped[list[GenreTable]] = relationship(
        secondary=book_genre_association,
        back_populates="books"
    )

    def __repr__(self):
        book_date = self.public_date.strftime("%d.%m.%Y")
        return (f"[Книга #{self.id!r}: {self.name!r},"
                f" Автор: {self.author!r}, Дата издания: {book_date}")


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Таблицы проверены/созданы.")

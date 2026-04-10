from datetime import date
from typing import AsyncGenerator
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import String, Text, Date

DATABASE_URL = "postgresql+asyncpg://postgre:mypassword@localhost:5432/booksDB"
engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    # Движок для создания
    engine,
    # Тип сессии
    class_=AsyncSession,
    # Объекты не "протухают" после commit
    expire_on_commit=False
)


# Метод для передачи сессии в crud
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# Класс для работы со всеми таблицами
class Base(DeclarativeBase):
    pass


# Общий класс для работы с таблицей и окном клиента
class BookTable(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    cover_path: Mapped[str] = mapped_column(String(255), nullable=True)
    public_date: Mapped[date] = mapped_column(Date, nullable=False)

    def __repr__(self):
        book_date = self.public_date.strftime("%d.%m.%Y")
        return (f"[Книга #{self.id!r}: {self.name!r},"
                f" Автор: {self.author!r}, Дата издания: {book_date}")


async def init_db():
    async with engine.begin() as conn:
        # run_sync нужен, так как metadata.create_all по своей природе синхронна
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы проверены/созданы.")

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .database import BookTable


async def get_books(db: AsyncSession) -> list[BookTable]:
    query = select(BookTable).order_by(BookTable.id)
    result = await db.execute(query)
    return list(result.scalars().all())

from sqlalchemy import text

from database.models import Base
from database.session import engine


async def create_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )

        result = await connection.execute(
            text("PRAGMA table_info(users)")
        )

        existing_columns = {
            row[1]
            for row in result.fetchall()
        }

        if "main_message_id" not in existing_columns:
            await connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN main_message_id INTEGER"
                )
            )
            
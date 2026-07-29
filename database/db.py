from sqlalchemy import text

from database.models import Base
from database.session import engine


async def create_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

        users_result = await connection.execute(
            text("PRAGMA table_info(users)")
        )

        user_columns = {
            row[1]
            for row in users_result.fetchall()
        }

        if "main_message_id" not in user_columns:
            await connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN main_message_id INTEGER"
                )
            )

        transactions_result = await connection.execute(
            text("PRAGMA table_info(transactions)")
        )

        transaction_columns = {
            row[1]
            for row in transactions_result.fetchall()
        }

        if "is_credit_card" not in transaction_columns:
            await connection.execute(
                text(
                    "ALTER TABLE transactions "
                    "ADD COLUMN is_credit_card "
                    "BOOLEAN NOT NULL DEFAULT 0"
                )
            )

        credit_cards_result = await connection.execute(
            text("PRAGMA table_info(credit_cards)")
        )

        credit_card_columns = {
            row[1]
            for row in credit_cards_result.fetchall()
        }

        if "credit_limit" not in credit_card_columns:
            await connection.execute(
                text(
                    "ALTER TABLE credit_cards "
                    "ADD COLUMN credit_limit "
                    "INTEGER NOT NULL DEFAULT 220000"
                )
            )
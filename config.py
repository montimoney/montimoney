from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    database_url: str


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    database_url = os.getenv("DATABASE_URL")

    if not token:
        raise ValueError("BOT_TOKEN не найден в .env")

    if not database_url:
        raise ValueError("DATABASE_URL не найден в .env")

    return Config(
        bot_token=token,
        database_url=database_url,
    )


config = load_config()

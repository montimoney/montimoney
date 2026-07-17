from sqlalchemy.ext.asyncio import AsyncSession

from database.repository import find_category_keyword

from utils.categories_dict import CATEGORIES


INCOME_WORDS = (
    "зарплата",
    "аванс",
    "премия",
    "вернули",
    "вернул",
    "подарок",
    "доход",
)


def detect_operation_type(text: str) -> str:

    text = text.lower()

    for word in INCOME_WORDS:
        if word in text:
            return "income"

    return "expense"



async def detect_category(
    session: AsyncSession,
    user_id: int,
    text: str,
) -> str | None:

    text = text.lower()


    # 1. Проверяем личные запомненные слова

    words = text.split()

    for word in words:

        saved_category = await find_category_keyword(
            session=session,
            user_id=user_id,
            keyword=word,
        )

        if saved_category:
            return saved_category



    # 2. Проверяем стандартные категории

    for category, keywords in CATEGORIES.items():

        for keyword in keywords:

            if keyword in text:
                return category



    # 3. Не нашли

    return None

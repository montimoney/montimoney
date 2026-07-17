import re
from dataclasses import dataclass


INCOME_WORDS = {
    "зарплата",
    "зп",
    "аванс",
    "премия",
    "доход",
    "получила",
    "получил",
}

CATEGORY_KEYWORDS = {
    "Рестораны": {
        "кофе",
        "кафе",
        "ресторан",
        "роллы",
        "суши",
        "пицца",
        "бургер",
        "шаурма",
        "доставка",
        "вкусно и точка",
        "kfc",
        "rostic",
        "surf",
    },
    "Продукты": {
        "магнит",
        "пятерочка",
        "пятёрочка",
        "перекресток",
        "перекрёсток",
        "лента",
        "ашан",
        "продукты",
        "магазин",
        "самокат",
    },
    "Транспорт": {
        "такси",
        "яндекс go",
        "автобус",
        "проезд",
        "билет",
    },
    "Авто": {
        "бензин",
        "заправка",
        "лукойл",
        "роснефть",
        "парковка",
        "мойка",
    },
    "Покупки": {
        "озон",
        "ozon",
        "вайлдберриз",
        "wildberries",
        "wb",
        "покупка",
        "одежда",
    },
    "Красота": {
        "маникюр",
        "шугаринг",
        "брови",
        "ресницы",
        "парикмахер",
        "волосы",
        "косметика",
    },
    "Здоровье": {
        "аптека",
        "лекарства",
        "врач",
        "анализы",
        "стоматолог",
    },
    "Монти": {
        "монти",
        "кот",
        "корм",
        "наполнитель",
        "ветеринар",
    },
    "Развлечения": {
        "кино",
        "театр",
        "концерт",
        "игра",
        "развлечения",
    },
}


@dataclass(slots=True)
class ParsedOperation:
    operation_type: str
    amount: int
    description: str
    category: str | None


def extract_amount(text: str) -> int | None:
    matches = re.findall(
        r"(?<!\d)(\d[\d\s]*)(?:[.,]\d{1,2})?\s*(?:₽|р|руб(?:лей|ля|ль)?)?",
        text.lower(),
    )

    if not matches:
        return None

    raw_amount = matches[-1].replace(" ", "")

    try:
        amount = int(raw_amount)
    except ValueError:
        return None

    return amount if amount > 0 else None


def clean_description(text: str, amount: int) -> str:
    cleaned = re.sub(
        rf"(?<!\d){amount}(?:[.,]\d{{1,2}})?\s*(?:₽|р|руб(?:лей|ля|ль)?)?",
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\b(за|на|потратила|потратил|заплатила|заплатил)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-")

    return cleaned.capitalize() or "Без описания"


def detect_category(text: str) -> str:
    normalized = text.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category

    return "Другое"


def parse_operation(text: str) -> ParsedOperation | None:
    normalized = text.lower().strip()
    amount = extract_amount(normalized)

    if amount is None:
        return None

    is_income = any(word in normalized for word in INCOME_WORDS)

    operation_type = "income" if is_income else "expense"
    description = clean_description(text, amount)

    category = None
    if operation_type == "expense":
        category = detect_category(normalized)

    return ParsedOperation(
        operation_type=operation_type,
        amount=amount,
        description=description,
        category=category,
    )

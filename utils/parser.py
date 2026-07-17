import re


def parse_amount(text: str) -> int | None:
    cleaned_text = text.replace(" ", "")

    numbers = re.findall(r"\d+", cleaned_text)

    if not numbers:
        return None

    return int(numbers[-1])


def parse_description(text: str) -> str:
    description = re.sub(
        r"\d[\d\s]*",
        "",
        text,
    )

    description = re.sub(
        r"\bс кредитки\b",
        "",
        description,
        flags=re.IGNORECASE,
    )

    return description.strip()


def is_credit_card_expense(text: str) -> bool:
    normalized = text.lower()

    return (
        "с кредитки" in normalized
        or "кредиткой" in normalized
    )


def is_credit_card_payment(text: str) -> bool:
    normalized = text.lower()

    payment_words = (
        "погасила кредитку",
        "погасил кредитку",
        "оплатила кредитку",
        "оплатил кредитку",
        "внесла на кредитку",
        "внес на кредитку",
    )

    return any(
        phrase in normalized
        for phrase in payment_words
    )

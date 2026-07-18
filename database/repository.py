from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    CreditCard,
    MandatoryExpense,
    MandatoryTemplate,
    Transaction,
    User,
    SavingGoal,
)



DEFAULT_MANDATORY_TEMPLATES = (
    ("Маникюр", 2700),
    ("Шугаринг", 2700),
    ("Рассрочка", 7000),
)


async def ensure_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: str | None,
) -> None:
    user = await session.get(User, telegram_id)

    if user is None:
        session.add(
            User(
                telegram_id=telegram_id,
                first_name=first_name,
            )
        )

    credit_card = await session.get(CreditCard, telegram_id)

    if credit_card is None:
        session.add(
            CreditCard(
                user_id=telegram_id,
                balance=0,
            )
        )

    await session.commit()


async def ensure_default_mandatory_templates(
    session: AsyncSession,
    user_id: int,
) -> None:

    existing = list(
        (
            await session.scalars(
                select(MandatoryTemplate).where(
                    MandatoryTemplate.user_id == user_id
                )
            )
        ).all()
    )

    existing_names = {
        item.name.lower()
        for item in existing
    }

    for name, amount in DEFAULT_MANDATORY_TEMPLATES:
        if name.lower() not in existing_names:
            session.add(
                MandatoryTemplate(
                    user_id=user_id,
                    name=name,
                    amount=amount,
                    is_active=True,
                )
            )

    await session.commit()


async def ensure_monthly_mandatory_expenses(
    session: AsyncSession,
    user_id: int,
) -> None:

    today = date.today()

    await ensure_default_mandatory_templates(
        session,
        user_id,
    )

    templates = list(
        (
            await session.scalars(
                select(MandatoryTemplate).where(
                    MandatoryTemplate.user_id == user_id,
                    MandatoryTemplate.is_active.is_(True),
                )
            )
        ).all()
    )

    existing = list(
        (
            await session.scalars(
                select(MandatoryExpense).where(
                    MandatoryExpense.user_id == user_id,
                    MandatoryExpense.month == today.month,
                    MandatoryExpense.year == today.year,
                )
            )
        ).all()
    )

    existing_ids = {
        item.template_id
        for item in existing
    }

    for template in templates:

        if template.id not in existing_ids:
            session.add(
                MandatoryExpense(
                    user_id=user_id,
                    template_id=template.id,
                    name=template.name,
                    amount=template.amount,
                    paid_amount=0,
                    paid_at=None,
                    month=today.month,
                    year=today.year,
                )
            )

    await session.commit()


async def add_mandatory_template(
    session: AsyncSession,
    user_id: int,
    name: str,
    amount: int,
) -> MandatoryTemplate:

    template = MandatoryTemplate(
        user_id=user_id,
        name=name,
        amount=amount,
        is_active=True,
    )

    session.add(template)

    await session.commit()
    await session.refresh(template)

    today = date.today()

    session.add(
        MandatoryExpense(
            user_id=user_id,
            template_id=template.id,
            name=name,
            amount=amount,
            paid_amount=0,
            paid_at=None,
            month=today.month,
            year=today.year,
        )
    )

    await session.commit()

    return template


async def update_mandatory_template(
    session: AsyncSession,
    template: MandatoryTemplate,
    new_amount: int,
) -> MandatoryTemplate:

    template.amount = new_amount

    today = date.today()

    current_expense = await session.scalar(
        select(MandatoryExpense).where(
            MandatoryExpense.template_id == template.id,
            MandatoryExpense.month == today.month,
            MandatoryExpense.year == today.year,
        )
    )

    if current_expense and current_expense.paid_amount == 0:
        current_expense.amount = new_amount

    await session.commit()
    await session.refresh(template)

    return template


async def disable_mandatory_template(
    session: AsyncSession,
    template: MandatoryTemplate,
) -> MandatoryTemplate:

    template.is_active = False

    await session.commit()
    await session.refresh(template)

    return template


async def add_transaction(
    session: AsyncSession,
    user_id: int,
    operation_type: str,
    amount: int,
    description: str,
    category: str | None = None,
) -> Transaction:

    transaction = Transaction(
        user_id=user_id,
        operation_type=operation_type,
        amount=amount,
        description=description,
        category=category,
    )

    session.add(transaction)

    await session.commit()
    await session.refresh(transaction)

    return transaction


async def clear_test_data(
    session: AsyncSession,
    user_id: int,
) -> None:

    # удаляем тестовые доходы и расходы
    await session.execute(
        Transaction.__table__.delete().where(
            Transaction.user_id == user_id
        )
    )

    # удаляем платежи текущего месяца
    await session.execute(
        MandatoryExpense.__table__.delete().where(
            MandatoryExpense.user_id == user_id
        )
    )

    await session.commit()

    # создаём обязательные платежи заново
    await ensure_monthly_mandatory_expenses(
        session,
        user_id,
    )


async def get_balance(
    session: AsyncSession,
    user_id: int,
) -> int:

    income = int(
        await session.scalar(
            select(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).where(
                Transaction.user_id == user_id,
                Transaction.operation_type == "income",
            )
        )
        or 0
    )

    expenses = int(
        await session.scalar(
            select(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).where(
                Transaction.user_id == user_id,
                Transaction.operation_type == "expense",
            )
        )
        or 0
    )

    return income - expenses


async def get_credit_card_balance(
    session: AsyncSession,
    user_id: int,
) -> int:

    credit_card = await session.get(
        CreditCard,
        user_id,
    )

    return credit_card.balance if credit_card else 0


async def get_monthly_mandatory_expenses(
    session: AsyncSession,
    user_id: int,
) -> list[MandatoryExpense]:

    today = date.today()


    await ensure_monthly_mandatory_expenses(
        session,
        user_id,
    )


    result = await session.scalars(
        select(MandatoryExpense)
        .join(
            MandatoryTemplate,
            MandatoryExpense.template_id == MandatoryTemplate.id,
        )
        .where(
            MandatoryExpense.user_id == user_id,
            MandatoryExpense.month == today.month,
            MandatoryExpense.year == today.year,
            MandatoryTemplate.is_active == True,
        )
        .order_by(
            MandatoryExpense.id
        )
    )


    return list(result.all())

async def find_mandatory_expense(
    session: AsyncSession,
    user_id: int,
    text: str,
) -> MandatoryExpense | None:

    expenses = await get_monthly_mandatory_expenses(
        session,
        user_id,
    )

    print("========")
    print("TEXT:", text)

    for expense in expenses:
        print(
            expense.name,
            expense.amount,
            expense.paid_amount,
        )

    text = text.lower()

    for expense in expenses:
        if expense.name.lower() in text:
            print("FOUND:", expense.name)
            return expense

    print("NOT FOUND")

    return None


async def pay_mandatory_expense(
    session: AsyncSession,
    expense: MandatoryExpense,
    payment_amount: int,
) -> int:

    remaining = max(
        expense.amount - expense.paid_amount,
        0,
    )

    applied = min(
        payment_amount,
        remaining,
    )

    expense.paid_amount += applied

    if expense.paid_amount >= expense.amount:
        expense.paid_amount = expense.amount
        expense.paid_at = datetime.now()

    await session.commit()
    await session.refresh(expense)

    return applied
async def get_main_message_id(
    session: AsyncSession,
    user_id: int,
) -> int | None:

    user = await session.get(
        User,
        user_id,
    )

    if user is None:
        return None

    return user.main_message_id


async def save_main_message_id(
    session: AsyncSession,
    user_id: int,
    message_id: int,
) -> None:

    user = await session.get(
        User,
        user_id,
    )

    if user is None:
        return

    user.main_message_id = message_id

    await session.commit()


async def get_category_statistics(
    session: AsyncSession,
    user_id: int,
) -> list[tuple[str, int]]:

    result = await session.execute(
        select(
            Transaction.category,
            func.sum(Transaction.amount),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.operation_type == "expense",
        )
        .group_by(Transaction.category)
        .order_by(
            func.sum(Transaction.amount).desc()
        )
    )

    return [
        (
            category or "Другое",
            int(amount),
        )
        for category, amount in result.all()
    ]


async def get_financial_totals(
    session: AsyncSession,
    user_id: int,
) -> tuple[int, int, int]:

    income = int(
        await session.scalar(
            select(
                func.coalesce(
                    func.sum(Transaction.amount),
                    0,
                )
            ).where(
                Transaction.user_id == user_id,
                Transaction.operation_type == "income",
            )
        )
        or 0
    )

    expenses = int(
        await session.scalar(
            select(
                func.coalesce(
                    func.sum(Transaction.amount),
                    0,
                )
            ).where(
                Transaction.user_id == user_id,
                Transaction.operation_type == "expense",
            )
        )
        or 0
    )

    balance = income - expenses

    return income, expenses, balance

async def add_credit_card_debt(
    session: AsyncSession,
    user_id: int,
    amount: int,
) -> int:
    credit_card = await session.get(
        CreditCard,
        user_id,
    )

    if credit_card is None:
        credit_card = CreditCard(
            user_id=user_id,
            balance=0,
        )
        session.add(credit_card)

    credit_card.balance += amount

    await session.commit()
    await session.refresh(credit_card)

    return credit_card.balance


async def pay_credit_card_debt(
    session: AsyncSession,
    user_id: int,
    amount: int,
) -> int:
    credit_card = await session.get(
        CreditCard,
        user_id,
    )

    if credit_card is None:
        credit_card = CreditCard(
            user_id=user_id,
            balance=0,
        )
        session.add(credit_card)

    credit_card.balance = max(
        credit_card.balance - amount,
        0,
    )

    await session.commit()
    await session.refresh(credit_card)

    return credit_card.balance

from database.models import SavingGoal


async def create_saving_goal(
    session: AsyncSession,
    user_id: int,
    name: str,
    target_amount: int,
) -> SavingGoal:

    goal = SavingGoal(
        user_id=user_id,
        name=name,
        target_amount=target_amount,
        saved_amount=0,
    )

    session.add(goal)

    await session.commit()
    await session.refresh(goal)

    return goal


async def get_saving_goals(
    session: AsyncSession,
    user_id: int,
) -> list[SavingGoal]:

    result = await session.scalars(
        select(SavingGoal).where(
            SavingGoal.user_id == user_id
        )
        .order_by(SavingGoal.id)
    )

    return list(result.all())


async def find_saving_goal(
    session: AsyncSession,
    user_id: int,
    name: str,
) -> SavingGoal | None:

    goals = await get_saving_goals(
        session,
        user_id,
    )

    name = name.lower()

    for goal in goals:
        if goal.name.lower() in name:
            return goal

    return None


async def add_to_saving_goal(
    session: AsyncSession,
    goal: SavingGoal,
    amount: int,
) -> SavingGoal:

    goal.saved_amount += amount

    if goal.saved_amount > goal.target_amount:
        goal.saved_amount = goal.target_amount

    await session.commit()
    await session.refresh(goal)

    return goal

async def find_category_keyword(
    session: AsyncSession,
    user_id: int,
    keyword: str,
) -> str | None:

    from database.models import CategoryKeyword

    result = await session.scalar(
        select(CategoryKeyword).where(
            CategoryKeyword.user_id == user_id,
            CategoryKeyword.keyword == keyword.lower(),
        )
    )

    if result is None:
        return None

    return result.category


async def save_category_keyword(
    session: AsyncSession,
    user_id: int,
    keyword: str,
    category: str,
) -> None:

    from database.models import CategoryKeyword

    item = CategoryKeyword(
        user_id=user_id,
        keyword=keyword.lower(),
        category=category,
    )

    session.add(item)

    await session.commit()

from sqlalchemy import distinct


async def get_user_categories(
    session: AsyncSession,
    user_id: int,
) -> list[str]:

    from database.models import CategoryKeyword

    result = await session.scalars(
        select(
            distinct(CategoryKeyword.category)
        ).where(
            CategoryKeyword.user_id == user_id
        )
    )

    return list(result.all())

async def clear_user_data(
    session,
    user_id: int,
):
    from database.models import (
        Transaction,
        SavingGoal,
        CategoryKeyword,
        CreditCard,
        MandatoryTemplate,
        MandatoryExpense,
    )

    from sqlalchemy import delete


    await session.execute(
        delete(Transaction).where(
            Transaction.user_id == user_id
        )
    )

    await session.execute(
        delete(SavingGoal).where(
            SavingGoal.user_id == user_id
        )
    )

    await session.execute(
        delete(CategoryKeyword).where(
            CategoryKeyword.user_id == user_id
        )
    )

    await session.execute(
        delete(CreditCard).where(
            CreditCard.user_id == user_id
        )
    )

    await session.execute(
        delete(MandatoryExpense).where(
            MandatoryExpense.user_id == user_id
        )
    )

    await session.execute(
        delete(MandatoryTemplate).where(
            MandatoryTemplate.user_id == user_id
        )
    )

    await session.commit()

async def get_history(
    session: AsyncSession,
    user_id: int,
    limit: int = 20,
) -> list[Transaction]:

    result = await session.scalars(
        select(Transaction)
        .where(
            Transaction.user_id == user_id
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .limit(limit)
    )

    return list(result.all())

async def get_last_transaction(
    session: AsyncSession,
    user_id: int,
) -> Transaction | None:

    result = await session.scalar(
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.operation_type.in_(
                [
                    "income",
                    "expense",
                ]
            ),
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .limit(1)
    )

    return result



async def delete_transaction(
    session: AsyncSession,
    transaction: Transaction,
) -> None:

    await session.delete(
        transaction
    )

    await session.commit()
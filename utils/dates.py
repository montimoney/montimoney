from datetime import date, timedelta


def move_salary_from_weekend(salary_date: date) -> date:
    """Переносит выплату с выходного на пятницу."""
    if salary_date.weekday() == 5:  # суббота
        return salary_date - timedelta(days=1)

    if salary_date.weekday() == 6:  # воскресенье
        return salary_date - timedelta(days=2)

    return salary_date


def get_next_salary_date(today: date | None = None) -> date:
    """Возвращает ближайшую дату зарплаты: 10-е или 25-е."""
    today = today or date.today()

    candidates: list[date] = []

    for month_shift in range(2):
        year = today.year
        month = today.month + month_shift

        if month > 12:
            month -= 12
            year += 1

        for day in (10, 25):
            salary_date = move_salary_from_weekend(
                date(year, month, day)
            )

            if salary_date >= today:
                candidates.append(salary_date)

    return min(candidates)


def get_days_until_salary(today: date | None = None) -> int:
    today = today or date.today()
    next_salary = get_next_salary_date(today)

    return (next_salary - today).days

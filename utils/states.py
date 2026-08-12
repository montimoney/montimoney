from aiogram.fsm.state import State, StatesGroup


class MandatoryAddState(StatesGroup):
    waiting_name = State()
    waiting_amount = State()


class MandatoryEditState(StatesGroup):
    waiting_name = State()
    waiting_amount = State()


class MandatoryDeleteState(StatesGroup):
    waiting_name = State()


class CategoryState(StatesGroup):
    waiting_category = State()


class AdviceState(StatesGroup):
    waiting_exit = State()


class CreditCorrectionState(StatesGroup):
    waiting_spent = State()
    waiting_available = State()


class CategoryDeleteState(StatesGroup):
    waiting_category = State()


class PlannerAddState(StatesGroup):
    waiting_salary_date = State()
    waiting_salary_amount = State()
    waiting_expense_salary = State()
    waiting_expense_name = State()
    waiting_expense_amount = State()


class PlannerEditState(StatesGroup):
    waiting_section = State()
    waiting_salary = State()
    waiting_expense_date = State()
    waiting_expense = State()
    waiting_new_amount = State()
    waiting_move_salary = State()
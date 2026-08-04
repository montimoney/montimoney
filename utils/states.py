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
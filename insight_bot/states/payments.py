from aiogram.fsm.state import StatesGroup, State


class PaymentScenario(StatesGroup):
    waiting_for_payment = State()
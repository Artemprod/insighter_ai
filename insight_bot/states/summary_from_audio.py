from aiogram.fsm.state import StatesGroup, State


class FSMSummaryFromAudioScenario(StatesGroup):
    load_file = State()
    get_result = State()
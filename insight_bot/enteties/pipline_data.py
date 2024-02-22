from dataclasses import dataclass
from typing import Optional

import aiogram
from aiogram.fsm.context import FSMContext


@dataclass
class PipelineData:
    telegram_message: aiogram.types.Message
    telegram_bot: aiogram.Bot
    assistant_id: str
    fsm_bot_state: FSMContext
    file_duration: float
    additional_system_information: Optional[str] = None
    additional_user_information: Optional[str] = None
    file_path: Optional[str] = None
    debase_document_id: Optional[str] = None
    transcribed_text: Optional[str] = None
    preprocessed_text: Optional[str] = None
    summary_text: Optional[str] = None

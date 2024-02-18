from aiogram.filters.callback_data import CallbackData


class AssistantCallbackFactory(CallbackData, prefix='gen_answer'):
    assistant_id: str


class DocumentsCallbackFactory(CallbackData, prefix='show_docs'):
    document_date: str

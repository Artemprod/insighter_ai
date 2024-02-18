from aiogram.filters.callback_data import CallbackData


class AssistantRedactCallbackFactory(CallbackData, prefix='option_redact'):
    assistant_id: str


class AssistantDeleteCallbackFactory(CallbackData, prefix='option_delete'):
    assistant_id: str



class AssistantRedactOptionCallbackFactory(CallbackData, prefix='redact_action'):
    assistant_id: str
    assistant_field: str

class AssistantCallbackFactory(CallbackData, prefix='gen_answer'):
    assistant_id: str

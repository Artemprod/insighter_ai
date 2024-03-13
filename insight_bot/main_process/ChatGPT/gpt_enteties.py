
from dataclasses import dataclass


@dataclass
class AssistantInWork:
    system_prompt: str
    user_prompt_for_chunks: str
    main_user_prompt: str
    additional_system_information: str
    additional_user_information: str

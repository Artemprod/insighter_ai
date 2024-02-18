from enum import Enum
from dataclasses import dataclass


class GPTRole(str, Enum):
    SYSTEM = 'system'
    ASSISTANT = 'assistant'
    USER = 'user'

@dataclass
class GPTMessage:
    role: GPTRole
    content: str
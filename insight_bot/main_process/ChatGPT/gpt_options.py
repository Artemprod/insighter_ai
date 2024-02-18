from dataclasses import dataclass, field
from typing import Union


@dataclass
class GPTOptions:
    api_key: str = field(repr=False)
    model_name: str
    max_message_count: Union[int, None]
    max_token_count: int
    temperature: float
    max_return_tokens:int


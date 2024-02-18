from dataclasses import dataclass, field


@dataclass
class GPTOptions:
    api_key: str = field(repr=False)
    model_name: str
    max_message_count: int | None
    max_token_count: int
    temperature: float
    max_return_tokens:int


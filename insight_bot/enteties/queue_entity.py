import asyncio
from typing import Optional


class PipelineQueues:
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.income_items_queue = asyncio.Queue()
        self.text_invoke_queue = asyncio.Queue()
        self.text_preprocess_queue = asyncio.Queue()
        self.text_gen_answer_queue = asyncio.Queue()
        self.result_dispatching_queue = asyncio.Queue()
        self.transcribed_text_sender_queue = asyncio.Queue()
        self.loop = loop

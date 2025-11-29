from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    topic: str
    payload: Any


class Agent:
    def handle(self, msg: Message) -> Any:
        raise NotImplementedError()

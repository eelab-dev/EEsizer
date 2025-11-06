from dataclasses import dataclass
from typing import Dict

@dataclass
class NetlistDocument:
    text: str
    meta: Dict = None

    def hash(self) -> int:
        return hash(self.text)

    def str(self) -> str:
        return self.text

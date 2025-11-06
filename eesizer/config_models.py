from pydantic import BaseModel
from typing import Optional

class RunConfig(BaseModel):
    ngspice_bin: str = "/usr/bin/ngspice"
    timeout_seconds: int = 300
    output_dir: str = "output"
    max_threads: Optional[int] = None

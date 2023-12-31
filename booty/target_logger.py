from dataclasses import dataclass
import pathlib
import time
from typing import Literal


@dataclass(frozen=True)
class TargetLogger:
    log_dir: str
    current_ms_time: int = int(time.time() * 1000)

    def log(self, target: str, setup_type: Literal["setup", "is_setup"], stdout: str, stderr: str):
        dir = f"{self.log_dir}/{self.current_ms_time}/{setup_type}"
        pathlib.Path(dir).mkdir(parents=True, exist_ok=True)

        with open(f"{dir}/{target}_stdout.log", "w") as f:
            f.write("=== stdout: ===\n")
            f.write(stdout)

        with open(f"{dir}/{target}_stderr.log", "w") as f:
            f.write("=== stderr: ===\n")
            f.write(stderr)

    def log_setup(self, target: str, stdout: str, stderr: str):
        self.log(target, "setup", stdout, stderr)

    def log_is_setup(self, target: str, stdout: str, stderr: str):
        self.log(target, "is_setup", stdout, stderr)

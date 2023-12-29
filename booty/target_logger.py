from dataclasses import dataclass
import pathlib
import time
from typing import Literal


@dataclass(frozen=True)
class TargetLogger:
    log_dir: str

    def log(self, target: str, setup_type: Literal["setup", "is_setup"], stdout: str, stderr: str):
        current_ms_time = int(time.time() * 1000)
        dir = f"{self.log_dir}/{current_ms_time}/{setup_type}"
        pathlib.Path(dir).mkdir(parents=True, exist_ok=True)

        with open(f"{dir}/{target}_stdout.log", "w") as f:
            f.write("=== stdout: ===\n")
            f.write(stdout)
            print(stdout)

        with open(f"{dir}/{target}_stderr.log", "w") as f:
            f.write("=== stderr: ===\n")
            f.write(stderr)
            print(stderr)

    def log_setup(self, target: str, stdout: str, stderr: str):
        self.log(target, "setup", stdout, stderr)

    def log_is_setup(self, target: str, stdout: str, stderr: str):
        self.log(target, "is_setup", stdout, stderr)

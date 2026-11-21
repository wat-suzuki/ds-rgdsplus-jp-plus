#!/usr/bin/env python3
"""Exercise launcher logging using a fake emulator inside a temporary SD card."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[3]


def main():
    subprocess.run(["sh", "-n", str(REPO / "skeleton/main.sh")], check=True)
    subprocess.run(["sh", "-n", str(REPO / "skeleton/system/run.sh")], check=True)
    with tempfile.TemporaryDirectory(prefix="dsplus-launcher-") as directory:
        root = Path(directory) / "SD card 日本語"
        emulator = root / "system/drastic"
        emulator.mkdir(parents=True)
        (root / "system/bin").mkdir()
        (root / "system/lib").mkdir()
        (emulator / "drastic").write_text("#!/bin/sh\nprintf 'emulator stdout\\n'\nprintf 'emulator stderr\\n' >&2\n")
        (emulator / "drastic").chmod(0o755)
        (root / "system/loop.sh").write_text(
            '#!/bin/sh\nprintf "%s\\n%s\\n" "$SDCARD_PATH" "$DRASTIC_PROFILE" > "$SDCARD_PATH/main-env"\n')
        (root / "system/loop.sh").chmod(0o755)
        (root / "main.sh").write_text((REPO / "skeleton/main.sh").read_text())
        environment = os.environ.copy()
        environment.pop("DRASTIC_PROFILE", None)
        subprocess.run(["sh", str(root / "main.sh")], env=environment, check=True)
        assert (root / "main-env").read_text().splitlines() == [str(root), "2"]
        environment["DRASTIC_PROFILE"] = "0"
        subprocess.run(["sh", str(root / "main.sh")], env=environment, check=True)
        assert (root / "main-env").read_text().splitlines()[1] == "0"

        # Redirect only the legacy /tmp destinations in the TEST copy.
        pointer, fallback = Path(directory) / "log-pointer", Path(directory) / "fallback.log"
        runner = root / "run-test.sh"
        text = (REPO / "skeleton/system/run.sh").read_text()
        text = text.replace("LOG_FILE=/tmp/drastic.txt", "LOG_FILE=" + shlex.quote(str(fallback)))
        text = text.replace("/tmp/drastic-log-path", shlex.quote(str(pointer)))
        runner.write_text(text)
        environment.update(SDCARD_PATH=str(root), DRASTIC_PROFILE="2")
        environment.pop("DRASTIC_PRESENT_ORDER", None)
        for order in ("batched", "grouped"):
            if order == "grouped":
                environment["DRASTIC_PRESENT_ORDER"] = order
            subprocess.run(["sh", str(runner)], env=environment, check=True, capture_output=True)
            assert f"DRASTIC_PRESENT_ORDER={order}" in Path(pointer.read_text().strip()).read_text()
        logs = list((root / "userdata/logs").glob("drastic-*.log"))
        assert len(logs) == 2
        for log in logs:
            content = log.read_text()
            assert "DRASTIC_PROFILE=2" in content and "emulator stdout" in content and "emulator stderr" in content
        assert Path(pointer.read_text().strip()).is_file()

        # Force an existing timestamp/PID path while keeping the same shell PID.
        date = root / "system/bin/date"
        date.write_text("#!/bin/sh\nprintf 'fixed\\n'\n")
        date.chmod(0o755)
        environment["PATH"] = str(date.parent) + os.pathsep + environment["PATH"]
        environment["RUN_SCRIPT"] = str(runner)
        subprocess.run(["sh", "-c", 'printf keep > "$SDCARD_PATH/userdata/logs/drastic-fixed-$$.log"\n. "$RUN_SCRIPT"'],
                       env=environment, check=True, capture_output=True)
        selected = Path(pointer.read_text().strip())
        assert selected.name.endswith("-1.log")
        assert selected.with_name(selected.name.replace("-1.log", ".log")).read_text() == "keep"

        log_dir = root / "userdata/logs"
        log_dir.rename(root / "userdata/saved-logs")
        log_dir.write_text("block mkdir")
        subprocess.run(["sh", str(runner)], env=environment, check=True, capture_output=True)
        assert pointer.read_text().strip() == str(fallback)
        assert "emulator stdout" in fallback.read_text() and "emulator stderr" in fallback.read_text()
    print("launcher: profile defaults/override, spaced UTF-8 paths, preserved logs, collision suffix and /tmp fallback passed")


if __name__ == "__main__":
    main()

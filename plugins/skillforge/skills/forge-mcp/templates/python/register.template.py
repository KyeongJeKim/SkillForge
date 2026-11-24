"""Register {{SF: server-name}} with Claude Code in one step.

Run it yourself in a terminal, in this folder:
    python3 register.py        (Windows: py -3 register.py)

It prepares this folder (a private Python environment with the packages server.py needs), checks
that the server starts, asks for each value below without showing what you type, and registers the
server for all your Claude Code projects. Running it again replaces the old values.

    python3 register.py --check    only prepare and check; asks nothing, registers nothing

Standard library only. Values you type go to `claude mcp add`, which keeps them in Claude Code's own
user settings, the same place a hand-typed `claude mcp add -e` puts them. This script never writes
them to a file of its own, prints them or leaves them in the shell history. While `claude mcp add`
runs (about a second) they are its command-line arguments, which other programs on this computer
can see; on a shared computer, register from your own account.
"""

from __future__ import annotations

import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

SERVER_NAME = "{{SF: server-name}}"
# One entry per environment variable server.py reads:
# (name, what it is and who has it, secret?, default or "" if it must be typed)
SETTINGS = [
    ("{{SF: ENV_PREFIX}}_TOKEN", "{{SF: what it is - who gives it, e.g. 재고 시스템 조회용 토큰 - 개발팀}}", True, ""),
]
# Two or three things to ask Claude once it is registered (the README's examples).
EXAMPLES = ["{{SF: example question 1}}", "{{SF: example question 2}}"]

HERE = Path(__file__).resolve().parent
VENV_PY = HERE / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
LIST_TOOLS = ("import runpy, asyncio; ns = runpy.run_path('server.py', run_name='check'); "
              "print(', '.join(t.name for t in asyncio.run(ns['mcp'].list_tools())))")


def say(text: str) -> None:
    print(text, flush=True)


def stop(text: str, code: int = 1) -> None:
    say(text)
    sys.exit(code)


def prepare() -> None:
    """Create .venv and install requirements.txt the first time; then list the tools."""
    if sys.version_info < (3, 10):
        stop(f"Python 3.10 이상이 필요합니다(지금 {sys.version.split()[0]}). 새 Python 을 설치한 뒤 다시 실행해 주세요.")
    if not VENV_PY.exists():
        say("1/3 이 폴더에 필요한 프로그램을 설치합니다(처음 한 번, 1~2분)...")
        for cmd in ([sys.executable, "-m", "venv", str(HERE / ".venv")],
                    [str(VENV_PY), "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", str(HERE / "requirements.txt")]):
            if subprocess.run(cmd, cwd=HERE).returncode != 0:
                stop("설치에 실패했습니다. 위 메시지를 개발 담당에게 보여 주세요(인터넷 연결, 회사 프록시를 확인).")
    else:
        say("1/3 필요한 프로그램은 이미 설치돼 있습니다.")
    done = subprocess.run([str(VENV_PY), "-c", LIST_TOOLS], cwd=HERE, capture_output=True, text=True)
    if done.returncode != 0:
        stop("서버가 시작되지 않았습니다. 아래 내용을 개발 담당에게 보여 주세요.\n" + done.stderr[-1500:])
    say(f"2/3 서버 확인: 도구 {done.stdout.strip()} (실제 시스템에는 아직 연결하지 않았습니다)")


def ask_values() -> list[str]:
    pairs = []
    for name, label, secret, default in SETTINGS:
        for _ in range(3):
            if secret:
                value = getpass.getpass(f"- {label} ({name}). 붙여 넣어도 화면에 보이지 않습니다: ")
            else:
                shown = f" [Enter = {default}]" if default else ""
                value = input(f"- {label} ({name}){shown}: ") or default
            value = value.strip()
            if value:
                pairs.append(f"{name}={value}")
                break
            say("  비어 있습니다. 다시 입력해 주세요.")
        else:
            stop("값을 받지 못해 등록하지 않았습니다. 값을 받은 뒤 다시 실행해 주세요.")
    return pairs


def register(claude: str, pairs: list[str]) -> None:
    if subprocess.run([claude, "mcp", "get", SERVER_NAME], capture_output=True).returncode == 0:
        subprocess.run([claude, "mcp", "remove", SERVER_NAME, "-s", "user"], capture_output=True)
        say("  이전에 등록한 것을 새 값으로 바꿉니다.")
    cmd = [claude, "mcp", "add", SERVER_NAME, "-s", "user"]
    for pair in pairs:
        cmd += ["-e", pair]
    cmd += ["--", str(VENV_PY), str(HERE / "server.py")]
    # Output is captured so a value can never be echoed back on screen.
    if subprocess.run(cmd, capture_output=True, text=True).returncode != 0:
        stop("Claude Code 에 등록하지 못했습니다. 'claude mcp list' 가 되는지 개발 담당과 확인해 주세요.")


def main(argv: list[str]) -> int:
    prepare()
    if "--check" in argv:
        say("확인만 했습니다(--check). 등록하려면 터미널에서 --check 없이 실행해 주세요.")
        return 0
    if not sys.stdin.isatty():
        stop("값을 화면에 보이지 않게 받으려면 터미널에서 직접 실행해 주세요: python3 register.py", 2)
    claude = shutil.which("claude")
    if not claude:
        stop("Claude Code(claude 명령)를 찾지 못했습니다. Claude Code 를 설치한 뒤 다시 실행해 주세요.")
    say("3/3 연결에 필요한 값을 받습니다.")
    register(claude, ask_values())
    say(f"\n완료: '{SERVER_NAME}' 를 등록했습니다. Claude Code 를 새로 열고 이렇게 물어보세요:")
    for example in EXAMPLES:
        say(f"  - {example}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

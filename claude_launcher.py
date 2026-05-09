"""Launch an interactive Claude Code session with a prompt from a temp file."""

import os
import shutil
import subprocess
import sys


def _resolve_claude_command() -> list[str]:
    """Return the argv prefix needed to invoke the Claude CLI.

    On Windows the npm-installed CLI is typically a ``claude.cmd`` shim,
    which CreateProcess cannot execute directly -- it must be routed
    through ``cmd.exe /c``. ``shutil.which`` honours ``PATHEXT`` and finds
    the shim regardless of extension.
    """
    claude = shutil.which("claude")
    if claude is None:
        raise FileNotFoundError("claude")
    if sys.platform == "win32" and claude.lower().endswith((".cmd", ".bat")):
        return ["cmd.exe", "/c", claude]
    return [claude]


def run_claude(prompt: str) -> subprocess.CompletedProcess:
    """Open an interactive Claude Code session pre-seeded with ``prompt``.

    The prompt is passed as a positional argv so Claude starts an
    interactive REPL with it as the first user message. Piping via stdin
    would make Claude run in non-interactive print mode and exit
    immediately, which closes the host terminal window before the user
    can read anything.
    """
    cmd = _resolve_claude_command() + ["--model", "sonnet", prompt]
    return subprocess.run(cmd, text=True)


def _pause_for_user_if_windows() -> None:
    """Block on a keypress so error output stays visible in wt.exe."""
    if sys.platform != "win32":
        return
    try:
        if not sys.stdin.isatty():
            return
    except (AttributeError, ValueError):
        return
    try:
        input("\nPress Enter to close this window...")
    except (EOFError, KeyboardInterrupt):
        pass


def main(argv: list[str] | None = None):
    """Entry point: read a prompt file and launch an interactive Claude session.

    Args:
        argv: Argument list (defaults to ``sys.argv``).  Expected:
            ``[script, prompt_file_path]``.  The prompt file is deleted on
            success and preserved (with its path printed to stderr) on failure.
    """
    argv = sys.argv if argv is None else argv
    if len(argv) != 2:
        print("Usage: claude_launcher.py <prompt_file>", file=sys.stderr)
        _pause_for_user_if_windows()
        sys.exit(1)

    prompt_file = argv[1]
    try:
        with open(prompt_file, encoding="utf-8") as f:
            prompt = f.read().strip()
    except FileNotFoundError:
        print(f"Prompt file not found: {prompt_file}", file=sys.stderr)
        _pause_for_user_if_windows()
        sys.exit(1)

    try:
        result = run_claude(prompt)
    except FileNotFoundError:
        print(
            "Claude CLI not found on PATH. "
            "Install Claude Code: https://docs.claude.com/en/docs/claude-code\n"
            f"Prompt preserved at: {prompt_file}",
            file=sys.stderr,
        )
        _pause_for_user_if_windows()
        sys.exit(1)
    except OSError as e:
        print(
            f"Failed to start Claude. Prompt preserved at: {prompt_file}. Error: {e}",
            file=sys.stderr,
        )
        _pause_for_user_if_windows()
        sys.exit(1)

    if result.returncode == 0:
        try:
            os.remove(prompt_file)
        except OSError as e:
            print(
                f"Warning: Claude session ended but prompt file could not be removed: {prompt_file} ({e})",
                file=sys.stderr,
            )
    else:
        print(
            f"Claude exited with code {result.returncode}. Prompt preserved at: {prompt_file}",
            file=sys.stderr,
        )
        _pause_for_user_if_windows()

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

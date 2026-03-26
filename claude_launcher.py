"""Launch an interactive Claude Code session with a prompt from a temp file."""
import os
import subprocess
import sys


def run_claude(prompt: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["claude", "--model", "sonnet", prompt],
    )


def main(argv: list[str] | None = None):
    argv = sys.argv if argv is None else argv
    if len(argv) != 2:
        print("Usage: claude_launcher.py <prompt_file>", file=sys.stderr)
        sys.exit(1)

    prompt_file = argv[1]
    try:
        with open(prompt_file, encoding="utf-8") as f:
            prompt = f.read().strip()
    except FileNotFoundError:
        print(f"Prompt file not found: {prompt_file}", file=sys.stderr)
        sys.exit(1)

    try:
        result = run_claude(prompt)
    except FileNotFoundError:
        print(f"Claude CLI not found. Prompt preserved at: {prompt_file}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Failed to start Claude. Prompt preserved at: {prompt_file}. Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        os.remove(prompt_file)
    except OSError as e:
        print(
            f"Warning: Claude session ended but prompt file could not be removed: {prompt_file} ({e})",
            file=sys.stderr,
        )

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

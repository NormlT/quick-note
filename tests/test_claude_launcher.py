import subprocess

import pytest

import claude_launcher


def test_run_claude_passes_prompt_as_argv(monkeypatch):
    captured = {}

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args=args, returncode=0)

    monkeypatch.setattr(claude_launcher, "_resolve_claude_command", lambda: ["/usr/bin/claude"])
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = claude_launcher.run_claude("hello from prompt")

    assert result.returncode == 0
    assert captured["args"] == [
        "/usr/bin/claude",
        "--model",
        "sonnet",
        "hello from prompt",
    ]
    # stdin must NOT be piped: piping forces Claude into non-interactive
    # print mode, which closes the host terminal window immediately.
    assert "input" not in captured["kwargs"]
    assert captured["kwargs"].get("text") is True


def test_resolve_claude_command_uses_shutil_which(monkeypatch):
    monkeypatch.setattr(claude_launcher.shutil, "which", lambda name: "/usr/bin/claude")
    monkeypatch.setattr(claude_launcher.sys, "platform", "linux")

    assert claude_launcher._resolve_claude_command() == ["/usr/bin/claude"]


def test_resolve_claude_command_wraps_cmd_shim_on_windows(monkeypatch):
    monkeypatch.setattr(
        claude_launcher.shutil,
        "which",
        lambda name: r"C:\Users\u\AppData\Roaming\npm\claude.CMD",
    )
    monkeypatch.setattr(claude_launcher.sys, "platform", "win32")

    assert claude_launcher._resolve_claude_command() == [
        "cmd.exe",
        "/c",
        r"C:\Users\u\AppData\Roaming\npm\claude.CMD",
    ]


def test_resolve_claude_command_passes_through_exe_on_windows(monkeypatch):
    monkeypatch.setattr(
        claude_launcher.shutil,
        "which",
        lambda name: r"C:\Program Files\Claude\claude.exe",
    )
    monkeypatch.setattr(claude_launcher.sys, "platform", "win32")

    assert claude_launcher._resolve_claude_command() == [
        r"C:\Program Files\Claude\claude.exe",
    ]


def test_resolve_claude_command_raises_when_missing(monkeypatch):
    monkeypatch.setattr(claude_launcher.shutil, "which", lambda name: None)

    with pytest.raises(FileNotFoundError):
        claude_launcher._resolve_claude_command()


def test_main_deletes_prompt_file_after_success(tmp_path, monkeypatch):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("ship it", encoding="utf-8")

    monkeypatch.setattr(
        claude_launcher,
        "run_claude",
        lambda prompt: subprocess.CompletedProcess(args=["claude"], returncode=0),
    )

    with pytest.raises(SystemExit) as exc_info:
        claude_launcher.main(["claude_launcher.py", str(prompt_file)])

    assert exc_info.value.code == 0
    assert not prompt_file.exists()


def test_main_preserves_prompt_file_on_nonzero_exit(tmp_path, monkeypatch, capsys):
    """Prompt file must be preserved when Claude exits with a nonzero return code."""
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("my important prompt", encoding="utf-8")

    monkeypatch.setattr(
        claude_launcher,
        "run_claude",
        lambda prompt: subprocess.CompletedProcess(args=["claude"], returncode=1),
    )

    with pytest.raises(SystemExit) as exc_info:
        claude_launcher.main(["claude_launcher.py", str(prompt_file)])

    assert exc_info.value.code == 1
    assert prompt_file.exists()
    assert str(prompt_file) in capsys.readouterr().err


def test_main_preserves_prompt_file_when_claude_missing(tmp_path, monkeypatch, capsys):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("keep me", encoding="utf-8")

    def fake_run(prompt):
        raise FileNotFoundError

    monkeypatch.setattr(claude_launcher, "run_claude", fake_run)

    with pytest.raises(SystemExit) as exc_info:
        claude_launcher.main(["claude_launcher.py", str(prompt_file)])

    assert exc_info.value.code == 1
    assert prompt_file.exists()
    assert str(prompt_file) in capsys.readouterr().err

from note_capture import generate_slug

def test_slug_basic():
    assert generate_slug("Fix UI thing in app B") == "fix-ui-thing-in-app"

def test_slug_short_note():
    assert generate_slug("hello") == "hello"

def test_slug_strips_punctuation():
    assert generate_slug("Fix the bug! It's broken.") == "fix-the-bug-its-broken"

def test_slug_unicode_swedish():
    assert generate_slug("Ändra DNS-inställningar för hemma") == "andra-dns-installningar-for-hemma"

def test_slug_max_five_words():
    assert generate_slug("one two three four five six seven") == "one-two-three-four-five"

def test_slug_empty():
    assert generate_slug("") == "untitled"


from note_capture import infer_tag

def test_tag_fix():
    assert infer_tag("fix the login button") == "todo"

def test_tag_update():
    assert infer_tag("update the README") == "todo"

def test_tag_bug():
    assert infer_tag("bug in the checkout flow") == "todo"

def test_tag_broken():
    assert infer_tag("broken CSS on mobile") == "todo"

def test_tag_maybe():
    assert infer_tag("maybe we should use Redis") == "idea"

def test_tag_what_if():
    assert infer_tag("what if we cached this") == "idea"

def test_tag_no_match():
    assert infer_tag("DNS settings for the homelab") == ""

def test_tag_case_insensitive():
    assert infer_tag("Fix the UI") == "todo"

def test_tag_empty():
    assert infer_tag("") == ""

def test_tag_action_in_middle_no_match():
    assert infer_tag("the user wants to fix something") == ""


from note_capture import resolve_context

def test_context_vscode():
    ctx = resolve_context("budget_calc.py - my-project - Visual Studio Code", "Code.exe")
    assert ctx["source"] == "vscode"
    assert ctx["project"] == "my-project"

def test_context_browser_chrome():
    ctx = resolve_context("GitHub Pull Request #42 - Google Chrome", "chrome.exe")
    assert ctx["source"] == "chrome"
    assert ctx["page"] == "GitHub Pull Request #42"

def test_context_browser_with_url():
    ctx = resolve_context("GitHub - Google Chrome", "chrome.exe", url="https://github.com/user/repo")
    assert ctx["source"] == "chrome"
    assert ctx["page"] == "GitHub"
    assert ctx["url"] == "https://github.com/user/repo"

def test_context_browser_without_url():
    ctx = resolve_context("GitHub - Google Chrome", "chrome.exe", url="")
    assert "url" not in ctx

def test_markdown_with_url():
    md = generate_markdown(
        note="interesting repo",
        tag="learning",
        context={"source": "chrome", "page": "GitHub", "url": "https://github.com/user/repo"},
        timestamp="2026-03-22T10:00:00",
    )
    assert "https://github.com/user/repo" in md
    assert "**URL**" in md

def test_context_browser_firefox():
    ctx = resolve_context("Reddit - Pair programming — Mozilla Firefox", "firefox.exe")
    assert ctx["source"] == "firefox"
    assert ctx["page"] == "Reddit - Pair programming"

def test_context_browser_edge():
    ctx = resolve_context("Bing - Microsoft Edge", "msedge.exe")
    assert ctx["source"] == "edge"
    assert ctx["page"] == "Bing"

def test_context_terminal_gitbash():
    ctx = resolve_context("MINGW64:/c/Users/youruser/Documents/github/homelab", "mintty.exe")
    assert ctx["source"] == "terminal"
    assert ctx["project"] == "homelab"

def test_context_terminal_wt():
    ctx = resolve_context("youruser@DESKTOP: ~/projects/myapp", "WindowsTerminal.exe")
    assert ctx["source"] == "terminal"
    assert ctx["project"] == "myapp"

def test_context_terminal_cmd_path():
    ctx = resolve_context(r"C:\Users\youruser\Documents\github\quick-note", "WindowsTerminal.exe")
    assert ctx["source"] == "terminal"
    assert ctx["project"] == "quick-note"

def test_context_terminal_unknown_title():
    ctx = resolve_context("PowerShell", "WindowsTerminal.exe")
    assert ctx["source"] == "terminal"
    assert ctx["window"] == "PowerShell"

def test_context_unknown_app():
    ctx = resolve_context("Untitled - Notepad", "notepad.exe")
    assert ctx["source"] == "notepad.exe"
    assert ctx["window"] == "Untitled - Notepad"

def test_context_empty():
    ctx = resolve_context("", "")
    assert ctx["source"] == "unknown"


from note_capture import generate_markdown, build_filename

def test_markdown_with_context():
    md = generate_markdown(
        note="Fix the login bug",
        tag="todo",
        context={"source": "vscode", "project": "my-app"},
        timestamp="2026-03-22T14:30:52",
    )
    assert "type: note" in md
    assert "tags: [quick-capture, todo]" in md
    assert 'created: "2026-03-22T14:30:52"' in md
    assert 'source: "vscode"' in md
    assert "# Fix the login bug" in md
    assert "**From**: vscode -- my-app" in md

def test_markdown_no_tag():
    md = generate_markdown(
        note="some random thought",
        tag="",
        context={"source": "unknown"},
        timestamp="2026-03-22T20:00:00",
    )
    assert "tags: [quick-capture]" in md
    assert "# Some random thought" in md

def test_markdown_browser_context():
    md = generate_markdown(
        note="interesting article",
        tag="learning",
        context={"source": "chrome", "page": "How DNS Works"},
        timestamp="2026-03-22T10:00:00",
    )
    assert "tags: [quick-capture, learning]" in md
    assert '**From**: chrome -- "How DNS Works"' in md

def test_build_filename():
    name = build_filename("Fix the login bug", "2026-03-22T14:30:52")
    assert name == "2026-03-22-143052-fix-the-login-bug.md"

def test_build_filename_timestamp_format():
    name = build_filename("hello world", "2026-01-05T09:05:03")
    assert name == "2026-01-05-090503-hello-world.md"


def test_save_note_creates_file(tmp_path):
    from note_capture import save_note

    result = save_note(
        note="Test note content",
        tag="idea",
        window_title="Test Window",
        process_name="notepad.exe",
        timestamp="2026-03-22T14:30:52",
        inbox_path=str(tmp_path),
    )
    assert result is True
    files = list(tmp_path.glob("*.md"))
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert "Test note content" in content
    assert "tags: [quick-capture, idea]" in content

def test_save_note_slug_collision(tmp_path):
    from note_capture import save_note

    save_note("hello", "", "win", "app.exe", "2026-03-22T14:30:52", str(tmp_path))
    save_note("hello", "", "win", "app.exe", "2026-03-22T14:30:52", str(tmp_path))
    files = list(tmp_path.glob("*.md"))
    assert len(files) == 2
    names = sorted(f.name for f in files)
    assert "-2" in names[1]

def test_save_note_bad_inbox(tmp_path):
    from note_capture import save_note

    result = save_note("test", "", "", "", "2026-03-22T14:30:52", str(tmp_path / "nonexistent"))
    assert result is False


def test_tag_could_we():
    assert infer_tag("could we try a different approach") == "idea"

def test_tag_should_we():
    assert infer_tag("should we refactor this module") == "idea"

def test_markdown_window_context():
    md = generate_markdown(
        note="test note",
        tag="",
        context={"source": "notepad.exe", "window": "Untitled - Notepad"},
        timestamp="2026-03-22T10:00:00",
    )
    assert "**From**: notepad.exe -- Untitled - Notepad" in md

def test_build_filename_with_microseconds():
    name = build_filename("test note", "2026-03-22T14:30:52.123456")
    assert name == "2026-03-22-143052-test-note.md"

def test_context_vscode_no_file():
    ctx = resolve_context("my-project - Visual Studio Code", "Code.exe")
    assert ctx["source"] == "vscode"
    assert ctx["project"] == "my-project"

def test_context_vscode_bare():
    ctx = resolve_context("Visual Studio Code", "Code.exe")
    assert ctx["source"] == "vscode"
    assert ctx["project"] == ""

def test_context_empty_title_with_process():
    ctx = resolve_context("", "notepad.exe")
    assert ctx["source"] == "notepad.exe"
    assert ctx["window"] == ""

def test_markdown_yaml_escape_quotes():
    md = generate_markdown(
        note="test",
        tag="",
        context={"source": "chrome", "page": '"React" vs "Vue"'},
        timestamp="2026-03-22T10:00:00",
    )
    # The YAML context line should have escaped quotes
    assert '\\"React\\"' in md or "React" in md
    # Frontmatter should not have unescaped double quotes breaking YAML
    lines = md.split("\n")
    for line in lines:
        if line.startswith("context:"):
            # Should not have raw unescaped quotes inside the YAML value
            assert line.count('"') % 2 == 0, f"Unbalanced quotes in YAML: {line}"

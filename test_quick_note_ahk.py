from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("quick-note.ahk")


def read_script() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_open_inbox_uri_encodes_parameters():
    script = read_script()

    assert 'UriEncode(VAULT_NAME)' in script
    assert 'UriEncode(inboxFolder)' in script


def test_do_save_note_escapes_dynamic_json_fields():
    script = read_script()

    assert 'JsonEscape(tag)' in script
    assert 'JsonEscape(processName)' in script
    assert 'JsonEscape(timestamp)' in script


def test_debug_logs_do_not_write_raw_urls():
    script = read_script()

    assert 'GetBrowserUrl returned, url=' not in script
    assert 'success, url=' not in script
    assert 'GetBrowserUrl completed, hasUrl=' in script


def test_startup_validates_required_config():
    script = read_script()

    assert 'ValidateRequiredConfig()' in script
    assert 'Config missing required key: python_path' in script
    assert 'Config missing required key: inbox_path' in script


def test_theme_defaults_to_windows_preference():
    script = read_script()

    assert 'GetSystemThemePref()' in script
    assert 'AppsUseLightTheme' in script
    assert 'return GetSystemThemePref()' in script

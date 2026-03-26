# Quick Note Copilot Instructions

## Common commands

- Install runtime dependencies: `pip install -r requirements.txt`
- Install the test runner used in the repo docs: `pip install pytest`
- Launch the app on Windows: `"%LocalAppData%\Programs\AutoHotkey\v2\AutoHotkey64.exe" "quick-note.ahk"`
- Run the full Python test suite: `python -m pytest -q`
- Run one test file: `python -m pytest test_note_capture.py -v`
- Run one test by name pattern: `python -m pytest test_note_capture.py -k test_context_browser_with_url -v`

## High-level architecture

- `quick-note.ahk` is the entrypoint and orchestrator. It loads config, registers the global hotkey, builds the tray menu, starts `note_watcher.py`, captures the active window/process/URL context, and shells out to the Python helpers.
- `popup.html` is not served by a web app. It is loaded into AutoHotkey's `Shell.Explorer` ActiveX control, so the popup behaves like an embedded IE11 document rather than a modern browser page.
- The save flow is file-based: `quick-note.ahk` writes a temp JSON payload, then runs `note_capture.py`. `note_capture.py` resolves the source context, infers a tag when the UI left it blank, formats the Obsidian markdown, and writes the final `.md` file into the configured inbox.
- The Claude flow is also file-based: `quick-note.ahk` writes a temp prompt file and launches `claude_launcher.py` inside Windows Terminal. `claude_launcher.py` reads and deletes the temp file, then runs `claude --model sonnet`.
- The Notepad++ watcher is a separate Python process. `note_watcher.py` snapshots existing `.txt` files on startup, debounces filesystem events, splits multi-note files, and reuses `note_capture.save_note()` so watcher-created notes follow the same markdown and filename rules as popup-created notes.

## Key conventions

- This is a Windows-first project. AutoHotkey v2, Windows Terminal, tray behavior, and UI Automation are part of the normal runtime path.
- User-specific state belongs in `local\`. Both Python and AHK look for `local\quick-note-config.json` first and fall back to a root `quick-note-config.json` only if needed. Logs, theme preference, and other runtime files also live under `local\` or `%TEMP%`.
- Keep the config schema flat unless you also update `quick-note.ahk`. AHK parses config values with regexes in `LoadConfig()` rather than a JSON parser, so renamed keys or nested structures require coordinated changes.
- Preserve the AHK/HTML contract when editing the popup. The embedded page signals actions by setting `document.title` to `SAVE`, `CLAUDE`, or `CANCEL`, and passes values back through the hidden `resultNote` and `resultTag` fields.
- Keep `popup.html` compatible with the embedded IE-style environment. The current code intentionally uses conservative DOM/CSS/clipboard patterns because the UI runs inside `Shell.Explorer`, not Chromium.
- `note_capture.py` is the source of truth for note output. It owns context resolution, tag inference, markdown/frontmatter layout, and filename generation. Filenames use `YYYY-MM-DD-HHMMSS-slug.md`, where the slug is ASCII-normalized and limited to the first five words.
- Explicit UI tags win; auto-tagging only runs when the popup did not select a tag. The built-in inference is intentionally narrow: action-oriented starts map to `todo`, and speculative starts map to `idea`.
- The first note line becomes the note title and the remaining text becomes the body. The generated note always appends a `## Captured Context` section sourced from the resolved window/browser/terminal metadata.
- Watcher deduplication and pause/resume behavior depend on `%TEMP%\quick-note-processed.json` and `%TEMP%\quick-note-watcher-paused`. If you change watcher behavior, keep those semantics aligned with the tray menu in `quick-note.ahk`.
- Automated tests only cover the Python modules. Changes to hotkeys, the embedded popup, browser URL capture, Windows UI Automation, or Claude launching need manual verification on Windows in addition to `pytest`.
- If `requirements.txt` changes, keep `.github\workflows\license-check.yml` in mind. CI installs `pip-licenses` and fails on GPL/AGPL/LGPL/SSPL-style licenses.

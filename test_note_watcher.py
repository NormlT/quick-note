from note_watcher import split_notes

def test_split_double_blank_lines():
    text = "First note here\n\n\nSecond note here"
    chunks = split_notes(text)
    assert len(chunks) == 2
    assert chunks[0] == "First note here"
    assert chunks[1] == "Second note here"

def test_split_separator_dashes():
    text = "First note\n---\nSecond note"
    chunks = split_notes(text)
    assert len(chunks) == 2
    assert chunks[0] == "First note"
    assert chunks[1] == "Second note"

def test_split_single_note():
    text = "Just one note"
    chunks = split_notes(text)
    assert len(chunks) == 1
    assert chunks[0] == "Just one note"

def test_split_empty_chunks_removed():
    text = "Note one\n\n\n\n\n\nNote two"
    chunks = split_notes(text)
    assert len(chunks) == 2

def test_split_whitespace_only_chunks_removed():
    text = "Note one\n---\n   \n---\nNote two"
    chunks = split_notes(text)
    assert len(chunks) == 2


import logging

def test_process_file_creates_inbox_notes(tmp_path, monkeypatch):
    from note_watcher import process_file
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("First note\n\n\nSecond note", encoding="utf-8")

    inbox = tmp_path / "inbox"
    inbox.mkdir()
    config = {"inbox_path": str(inbox), "log_path": str(tmp_path / "test.log")}

    monkeypatch.setattr("note_watcher.PROCESSED_DB", str(tmp_path / "processed.json"))

    logger = logging.getLogger("test-watcher")
    process_file(str(txt_file), config, logger)

    md_files = list(inbox.glob("*.md"))
    assert len(md_files) == 2

def test_process_file_skips_already_processed(tmp_path, monkeypatch):
    from note_watcher import process_file
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Only one note", encoding="utf-8")

    inbox = tmp_path / "inbox"
    inbox.mkdir()
    config = {"inbox_path": str(inbox), "log_path": str(tmp_path / "test.log")}
    monkeypatch.setattr("note_watcher.PROCESSED_DB", str(tmp_path / "processed.json"))

    logger = logging.getLogger("test-watcher")
    process_file(str(txt_file), config, logger)
    process_file(str(txt_file), config, logger)

    md_files = list(inbox.glob("*.md"))
    assert len(md_files) == 1

def test_process_file_paused(tmp_path, monkeypatch):
    from note_watcher import process_file
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("A note", encoding="utf-8")

    inbox = tmp_path / "inbox"
    inbox.mkdir()
    config = {"inbox_path": str(inbox), "log_path": str(tmp_path / "test.log")}
    monkeypatch.setattr("note_watcher.PROCESSED_DB", str(tmp_path / "processed.json"))

    # Create pause flag
    pause_file = tmp_path / "paused"
    pause_file.touch()
    monkeypatch.setattr("note_watcher.PAUSE_FLAG", str(pause_file))

    logger = logging.getLogger("test-watcher")
    process_file(str(txt_file), config, logger)

    md_files = list(inbox.glob("*.md"))
    assert len(md_files) == 0  # paused, nothing created

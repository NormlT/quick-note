"""Notepad++ file watcher -- monitors a folder and creates Obsidian Inbox notes."""

import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from note_capture import save_note, load_config, setup_logging


PROCESSED_DB = os.path.join(os.environ.get("TEMP", "/tmp"), "quick-note-processed.json")
PAUSE_FLAG = os.path.join(os.environ.get("TEMP", "/tmp"), "quick-note-watcher-paused")


_SPLIT_RE = re.compile(r"\n{3,}|(?:^|\n)---(?:\n|$)")


def split_notes(text: str) -> list[str]:
    """Split text into separate notes on triple newlines or --- separators."""
    chunks = _SPLIT_RE.split(text)
    return [c.strip() for c in chunks if c.strip()]


def _load_processed_db() -> dict[str, str]:
    if os.path.exists(PROCESSED_DB):
        try:
            with open(PROCESSED_DB, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_processed_db(db: dict[str, str]) -> None:
    with open(PROCESSED_DB, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)


def _content_hash(filepath: str) -> str:
    with open(filepath, encoding="utf-8", errors="replace") as f:
        return hashlib.sha256(f.read().encode()).hexdigest()


def process_file(filepath: str, config: dict, logger: logging.Logger):
    """Process a single Notepad++ file into Inbox notes."""
    if os.path.exists(PAUSE_FLAG):
        logger.info("Watcher paused, skipping: %s", filepath)
        return

    db = _load_processed_db()

    with open(filepath, encoding="utf-8", errors="replace") as f:
        content = f.read()
    current_hash = hashlib.sha256(content.encode()).hexdigest()

    if db.get(filepath) == current_hash:
        logger.info("Already processed (unchanged): %s", filepath)
        return

    chunks = split_notes(content)
    timestamp = datetime.now().isoformat(timespec="seconds")
    source_name = Path(filepath).stem
    all_saved = True

    for i, chunk in enumerate(chunks):
        # Use a fresh timestamp per chunk; build_filename handles filename collisions via counter
        chunk_ts = datetime.now().isoformat(timespec="seconds") if i > 0 else timestamp
        if not save_note(
            note=chunk,
            tag="",
            window_title=f"Notepad++ -- {source_name}",
            process_name="notepad++.exe",
            timestamp=chunk_ts,
            inbox_path=config["inbox_path"],
            log_path=config.get("log_path", ""),
        ):
            logger.error("Failed to create inbox note from: %s", filepath)
            all_saved = False
            break
        logger.info("Created inbox note from: %s", filepath)

    if not all_saved:
        logger.warning("Leaving file unmarked for retry: %s", filepath)
        return

    db[filepath] = current_hash
    _save_processed_db(db)


class NoteHandler(FileSystemEventHandler):
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self._pending = {}

    def on_modified(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".txt"):
            return
        self._pending[event.src_path] = time.time()

    def on_created(self, event):
        self.on_modified(event)

    def check_pending(self):
        """Call periodically to process debounced files."""
        now = time.time()
        ready = [p for p, t in self._pending.items() if now - t >= 2.0]
        for filepath in ready:
            del self._pending[filepath]
            try:
                process_file(filepath, self.config, self.logger)
            except Exception as e:
                self.logger.error("Error processing %s: %s", filepath, e)


def snapshot_existing(watch_path: str) -> dict[str, str]:
    """Take a content hash snapshot of existing files at startup."""
    db = _load_processed_db()
    # Prune entries for files that no longer exist
    db = {k: v for k, v in db.items() if os.path.exists(k)}
    for f in Path(watch_path).glob("*.txt"):
        filepath = str(f)
        if filepath not in db:
            db[filepath] = _content_hash(filepath)
    _save_processed_db(db)
    return db


def main():
    config = load_config()
    logger = setup_logging(config.get("log_path", "quick-note.log"))

    watch_path = config.get("watch_path")
    if not watch_path:
        logger.error("'watch_path' missing from config")
        return
    if not config.get("inbox_path"):
        logger.error("'inbox_path' missing from config")
        return

    max_retries = 10
    retries = 0
    while not os.path.isdir(watch_path):
        retries += 1
        if retries > max_retries:
            logger.error("Watch path not found after %d retries, exiting: %s", max_retries, watch_path)
            return
        logger.warning("Watch path not found, retrying in 30s (%d/%d): %s", retries, max_retries, watch_path)
        time.sleep(30)

    snapshot_existing(watch_path)
    logger.info("Watcher started, monitoring: %s", watch_path)

    handler = NoteHandler(config, logger)
    observer = Observer()
    observer.schedule(handler, watch_path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
            handler.check_pending()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()

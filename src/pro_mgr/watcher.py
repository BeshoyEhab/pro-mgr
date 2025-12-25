"""
Watcher module for {{name}}.
Handles file monitoring and automatic task re-execution.
"""

import time
import fnmatch
from pathlib import Path
from typing import List, Callable, Optional, Set
from threading import Timer

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class DebouncedHandler(FileSystemEventHandler):
    """
    File system event handler with debouncing.
    
    Collects events and only triggers callback after a quiet period.
    """
    
    def __init__(
        self,
        callback: Callable[[], None],
        debounce_ms: int = 500,
        ignore_patterns: Optional[List[str]] = None
    ):
        """
        Initialize the debounced handler.
        
        Args:
            callback: Function to call when files change
            debounce_ms: Milliseconds to wait after last event before triggering
            ignore_patterns: Glob patterns to ignore (e.g., ['*.pyc', '__pycache__/*'])
        """
        super().__init__()
        self.callback = callback
        self.debounce_seconds = debounce_ms / 1000.0
        self.ignore_patterns = ignore_patterns or []
        self._timer: Optional[Timer] = None
        self._pending_events: Set[str] = set()
    
    def _should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored based on patterns."""
        path_str = str(path)
        name = Path(path).name
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
            if fnmatch.fnmatch(path_str, pattern):
                return True
        
        # Always ignore common temporary/cache files
        always_ignore = [
            '__pycache__',
            '.git',
            '.venv',
            'venv',
            '*.pyc',
            '*.pyo',
            '.DS_Store',
            '*.swp',
            '*.swo',
            '*~',
        ]
        
        for pattern in always_ignore:
            if fnmatch.fnmatch(name, pattern):
                return True
            if pattern in path_str:
                return True
        
        return False
    
    def _schedule_callback(self) -> None:
        """Schedule the callback with debouncing."""
        if self._timer:
            self._timer.cancel()
        
        self._timer = Timer(self.debounce_seconds, self._trigger_callback)
        self._timer.start()
    
    def _trigger_callback(self) -> None:
        """Trigger the callback and clear pending events."""
        if self._pending_events:
            changed_files = list(self._pending_events)
            self._pending_events.clear()
            
            print(f"\n📁 Files changed: {len(changed_files)}")
            for f in changed_files[:5]:  # Show first 5 files
                print(f"   - {Path(f).name}")
            if len(changed_files) > 5:
                print(f"   ... and {len(changed_files) - 5} more")
            print()
            
            self.callback()
    
    def on_any_event(self, event: FileSystemEvent) -> None:
        """Handle any file system event."""
        if event.is_directory:
            return
        
        path = event.src_path
        
        if self._should_ignore(path):
            return
        
        self._pending_events.add(path)
        self._schedule_callback()
    
    def stop(self) -> None:
        """Stop any pending timer."""
        if self._timer:
            self._timer.cancel()
            self._timer = None


def load_gitignore_patterns(project_path: str) -> List[str]:
    """
    Load ignore patterns from .gitignore file.
    
    Args:
        project_path: Path to project root
    
    Returns:
        List of gitignore patterns
    """
    gitignore_path = Path(project_path) / ".gitignore"
    patterns = []
    
    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception:
            pass
    
    return patterns


def watch_and_execute(
    dirs: List[str],
    callback: Callable[[], None],
    debounce_ms: int = 500,
    project_path: Optional[str] = None
) -> None:
    """
    Watch directories for changes and execute callback.
    
    This function blocks until interrupted with Ctrl+C.
    
    Args:
        dirs: List of directories to watch
        callback: Function to call when files change
        debounce_ms: Milliseconds to wait after last change
        project_path: Project root for loading .gitignore
    """
    # Load ignore patterns
    ignore_patterns = []
    if project_path:
        ignore_patterns = load_gitignore_patterns(project_path)
    
    # Create handler
    handler = DebouncedHandler(
        callback=callback,
        debounce_ms=debounce_ms,
        ignore_patterns=ignore_patterns
    )
    
    # Create observer
    observer = Observer()
    
    # Schedule watches for all directories
    for dir_path in dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            observer.schedule(handler, str(path), recursive=True)
            print(f"👁 Watching: {path}")
    
    # Run initial execution
    print("\n▶ Running initial execution...")
    callback()
    
    print("\n⏳ Watching for changes... (Press Ctrl+C to stop)")
    
    # Start observer
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping watcher...")
        handler.stop()
        observer.stop()
    
    observer.join()


def resolve_watch_dirs(project_path: str, task_dirs: Optional[List[str]] = None) -> List[str]:
    """
    Resolve watch directories to absolute paths.
    
    Args:
        project_path: Project root path
        task_dirs: Directories specified in task config
    
    Returns:
        List of absolute directory paths
    """
    base = Path(project_path)
    
    if task_dirs:
        # Use specified directories
        dirs = []
        for d in task_dirs:
            full_path = base / d
            if full_path.exists():
                dirs.append(str(full_path))
        return dirs if dirs else [str(base)]
    else:
        # Default: watch src/ and tests/ if they exist, otherwise project root
        candidates = [base / "src", base / "tests"]
        dirs = [str(d) for d in candidates if d.exists()]
        return dirs if dirs else [str(base)]

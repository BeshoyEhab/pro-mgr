# pro-mgr Developer Documentation

This document contains technical details for contributors.

## Project Status: ✅ Complete

All modules implemented and tested.

---

## Architecture

```
src/pro_mgr/
├── cli.py       # Click commands - main entry point
├── db.py        # SQLite database (projects, snippets)
├── config.py    # TOML parser, dependency resolution
├── scaffold.py  # Project templates, venv, git init
├── runner.py    # Task execution, venv activation
├── watcher.py   # File monitoring with debounce
└── tui.py       # Textual interactive dashboard
```

---

## Database Schema

**Location**: `~/.pro-mgr/pro-mgr.db`

### Projects Table

```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    root_path TEXT NOT NULL,
    venv_path TEXT,
    description TEXT,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP
);
```

### Snippets Table

```sql
CREATE TABLE snippets (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## Key Interfaces

### cli.py

- `new` - Create project from template with `--author`, `--license`, `--description`
- `init` - Initialize pro-mgr.toml in existing project (auto-detects type)
- `run` - Execute task for a project with optional `--watch`
- `shell` - Print shell activation command (Fish-compatible)
- `project` - Subcommands: list, info, add, rm, update
- `snip` - Subcommands: add, ls, search, show, edit, rm

### db.py

- `add_project(name, root_path, venv_path, description, tags)`
- `get_project(name)` → dict or None
- `get_all_projects()` → list
- `add_snippet(name, content, tags)`
- `search_snippets(query)` → list

### config.py

- `load_config(project_path)` → dict
- `resolve_dependencies(config, task_name)` → list (topological order)
- `expand_snippets(command)` → str (replaces `{snip:name}`)

### scaffold.py

- `create_project(name, template, path, init_git, create_venv, variables)` → dict
- `get_available_templates()` → list
- `get_default_variables()` → dict (author, email, license from config/env)

### runner.py

- `run_task(project_name, task_name, force)` → exit_code
- `run_single_task(task_config, project_path, env)` → exit_code (supports timeout)
- `activate_virtualenv(venv_path)` → env dict
- `detect_shell()` → str (fish, bash, zsh, sh)

### watcher.py

- `watch_and_execute(dirs, callback, gitignore_patterns)`

### tui.py

- `run_tui()` → tuple or None

---

## Template Variables

Templates support these variables (substituted with `{{variable}}`):

| Variable          | Source                                                  |
| ----------------- | ------------------------------------------------------- |
| `name`            | Project name                                            |
| `name_underscore` | Project name with `-` → `_`                             |
| `author`          | `~/.pro-mgr/config.toml`, `PRO_MGR_AUTHOR` env, or CLI  |
| `email`           | `~/.pro-mgr/config.toml`, `PRO_MGR_EMAIL` env           |
| `license`         | `~/.pro-mgr/config.toml`, `PRO_MGR_LICENSE` env, or CLI |
| `description`     | CLI `--description` option                              |

### User Config Example

```toml
# ~/.pro-mgr/config.toml
[defaults]
author = "Your Name"
email = "you@example.com"
license = "MIT"
```

---

## Task Timeout

Tasks can specify a timeout in seconds:

```toml
[tasks.test]
command = "pytest"
timeout = 300  # 5 minutes
```

---

## Package Caching

**Location**: `~/.pro-mgr/pip-cache/`

All project venvs share this cache to avoid re-downloading packages.
Configured via `PIP_CACHE_DIR` env var and per-venv `pip.conf`.

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/test_config.py -v
pytest tests/test_scaffold.py -v
```

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Submit a pull request

---

## License

MIT License

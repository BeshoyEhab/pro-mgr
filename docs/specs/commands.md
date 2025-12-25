# Command Specifications

This document details the implementation specifications for the `pro-mgr` CLI commands. It is intended for developers working on `cli.py`, `runner.py`, `scaffold.py`, and `db.py`.

## Command Hierarchy

```
pro-mgr
├── (default) -> TUI Dashboard
├── new
├── run
├── project
│   ├── list
│   ├── info
│   ├── add
│   ├── rm
│   └── update
├── shell
└── snip
    ├── add
    ├── ls
    ├── search
    ├── show
    ├── edit
    └── rm
```

---

## 1. `pro-mgr` (Root/TUI)

**Module**: `cli.py` -> `tui.py`

### Signature
```python
@click.command()
def cli():
    """Opens the interactive dashboard."""
```

### Internal Logic
1.  Check if any subcommand is passed. If yes, delegate to that command.
2.  If no subcommand, initialize `tui.ProMgrApp`.
3.  `ProMgrApp` loads projects from `db.get_all_projects()`.
4.  Render the Textual UI.

### Dependencies
- `tui.py`: The Textual application class.
- `db.py`: To fetch project list.

---

## 2. `pro-mgr new`

**Module**: `cli.py` -> `scaffold.py`

### Signature
```python
@cli.command()
@click.argument("name")
@click.option("--template", default="python-cli", help="Project template to use")
@click.option("--path", default=".", help="Target directory")
@click.option("--no-git", is_flag=True, help="Skip git init")
@click.option("--no-venv", is_flag=True, help="Skip venv creation")
def new(name, template, path, no_git, no_venv):
```

### Internal Logic
1.  **Validation**: Check if `path/name` already exists. If so, abort.
2.  **Scaffolding**:
    - Call `scaffold.create_project_structure(name, template, path)`.
    - Copy template files from `templates/<template>/` to target.
3.  **Git Init** (unless `--no-git`):
    - Run `git init` in the new directory.
    - Create `.gitignore`.
4.  **Venv Creation** (unless `--no-venv`):
    - Run `python -m venv .venv`.
5.  **Registration**:
    - Call `db.add_project(name, full_path, venv_path)`.
6.  **Output**: Print success message with "cd" instructions.

### Error Handling
- `FileExistsError`: If directory exists.
- `TemplateNotFoundError`: If template name is invalid.

---

## 3. `pro-mgr run`

**Module**: `cli.py` -> `runner.py`

### Signature
```python
@cli.command()
@click.argument("project_name")
@click.argument("task_name")
@click.option("--watch", "-w", is_flag=True, help="Watch mode")
@click.option("--force", "-f", is_flag=True, help="Ignore git dirty check")
def run(project_name, task_name, watch, force):
```

### Internal Logic
1.  **Lookup**: Call `db.get_project(project_name)`. If None, error.
2.  **Config**: Load `pro-mgr.toml` from project root using `config.load_config()`.
3.  **Task Resolution**:
    - Get task definition via `config.get_task(task_name)`.
    - Check `fail_on_dirty_branch`. If true and not `force`, check `git status`. Abort if dirty.
    - Resolve dependencies (DAG check for cycles).
4.  **Execution**:
    - If `--watch`:
        - Call `watcher.watch_and_execute(dirs, callback=runner.run_task)`.
    - Else:
        - Call `runner.run_task(project, task)`.
        - `runner.run_task` must activate venv environment variables before subprocess call.

### Dependencies
- `runner.py`: For execution.
- `watcher.py`: For watch mode.
- `config.py`: For parsing TOML.

---

## 4. `pro-mgr project`

**Module**: `cli.py` -> `db.py`

### Subcommands

#### `list`
- **Signature**: `list(format: str)`
- **Logic**: Fetch all from DB. Print table (using `rich.table`) or JSON.

#### `info`
- **Signature**: `info(project_name: str)`
- **Logic**: Fetch details. Parse `pro-mgr.toml` to show available tasks.

#### `add`
- **Signature**: `add(path: str, name: str)`
- **Logic**:
    - Verify path exists and has `pro-mgr.toml` (optional warning if missing).
    - Detect venv path automatically if possible.
    - Insert into DB.

#### `rm`
- **Signature**: `rm(project_name: str, confirm: bool)`
- **Logic**: Delete row from `projects` table. **Do not** delete files.

#### `update`
- **Signature**: `update(name: str, description: str, tags: str)`
- **Logic**: Update fields in DB.

---

## 5. `pro-mgr shell`

**Module**: `cli.py`

### Signature
```python
@cli.command()
@click.argument("project_name")
def shell(project_name):
```

### Internal Logic
1.  **Lookup**: Get project from DB.
2.  **Output**: Print the shell command to be evaluated by the user's shell.
    - Format: `export VIRTUAL_ENV=...; export PATH=...; cd ...`
    - **Note**: This command prints text. The user must run `eval $(pro-mgr shell name)` for it to take effect.

---

## 6. `pro-mgr snip`

**Module**: `cli.py` -> `db.py`

### Subcommands

#### `add`
- **Signature**: `add(name: str, tags: str)`
- **Logic**:
    - Open `click.edit()` to let user type the script.
    - Save to `snippets` table.

#### `ls`
- **Signature**: `ls(tag: str, format: str)`
- **Logic**: `SELECT * FROM snippets WHERE tags LIKE %tag%`.

#### `search`
- **Signature**: `search(query: str)`
- **Logic**:
    - `SELECT * FROM snippets WHERE name LIKE %q% OR content LIKE %q% OR tags LIKE %q%`.
    - Highlight matches in output.

#### `show`
- **Signature**: `show(name: str)`
- **Logic**: Print content of snippet.

#### `edit`
- **Signature**: `edit(name: str)`
- **Logic**:
    - Fetch content.
    - `click.edit(content)`.
    - Update DB with new content.

#### `rm`
- **Signature**: `rm(name: str, confirm: bool)`
- **Logic**: Delete from DB.

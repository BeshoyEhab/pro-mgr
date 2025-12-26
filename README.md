# 🚀 Pro-Mgr

**A command-line tool to manage multiple projects from anywhere.**

Stop juggling folders, virtual environments, and commands. Run tasks for any project from any directory.

```bash
# From anywhere on your system:
pro-mgr run my-api test --watch
pro-mgr shell blog-app
pro-mgr  # Opens interactive dashboard
```

---

## ✨ Features

- **🌍 Work from anywhere** - Run tasks without navigating to project directories
- **📦 Package caching** - Shared pip cache across projects (no re-downloading)
- **🖥️ Interactive TUI** - Navigate projects and tasks with keyboard
- **👁️ Watch mode** - Auto-rerun tasks on file changes
- **🔗 Task dependencies** - Define task chains with cycle detection
- **📝 Code snippets** - Save and reuse common commands
- **🐍 Venv support** - Automatic virtual environment activation

---

## 📥 Installation

```bash
git clone https://github.com/username/pro-mgr.git
cd pro-mgr
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

---

## 🎯 Quick Start

### Create a new project

```bash
pro-mgr new my-app                          # Python CLI template
pro-mgr new my-api --template flask-api     # Flask API template
pro-mgr new my-site --template django-app   # Django template
pro-mgr new my-app --author "John Doe"      # With custom author
```

### Initialize in existing project

```bash
cd my-existing-project
pro-mgr init                                # Auto-detects project type
pro-mgr init --name my-app                  # With custom name
```

### Run tasks

```bash
pro-mgr run my-app test           # Run tests
pro-mgr run my-app test --watch   # Auto-rerun on file changes
pro-mgr run my-api serve          # Start server
```

### Interactive dashboard

```bash
pro-mgr                           # Opens TUI
```

- `↑/↓` Navigate projects
- `Enter` Select project → view tasks
- `r` Run task | `w` Watch mode
- `Backspace` Go back | `q` Quit

### Manage projects

```bash
pro-mgr project list              # Show all projects
pro-mgr project add ~/code/app    # Register existing project
pro-mgr project rm my-app         # Unregister (files preserved)
```

### Code snippets

```bash
pro-mgr snip add --name deploy --tags "docker,prod"
pro-mgr snip search docker
pro-mgr snip show deploy
```

---

## 📄 Configuration

Create `pro-mgr.toml` in your project root:

```toml
[project]
name = "my-app"
version = "1.0.0"

[tasks.test]
command = "pytest tests/ -v"
description = "Run tests"
watch_dirs = ["src/", "tests/"]

[tasks.serve]
command = "flask run --debug"
description = "Start dev server"

[tasks.deploy]
command = "docker-compose up -d"
description = "Deploy to production"
fail_on_dirty_branch = true  # Requires clean git
depends_on = ["test"]        # Run tests first

[tasks.lint]
command = "npm run lint"     # Works with any language!

[dotfiles]
branch = "work"              # Switch dot-man branch
auto_switch = true           # Auto-switch on shell activation
```

### 🔌 Dot-Man Integration

Integrate with [dot-man](https://github.com/BeshoyEhab/dot-man) to automatically switch dotfiles when working on a project:

```bash
# Activation switches dotfiles to "work" branch if configured
eval $(pro-mgr shell my-work-project)
```

---

## 🗂️ Project Structure

```
pro-mgr/
├── src/pro_mgr/
│   ├── cli.py       # Click commands
│   ├── db.py        # SQLite database
│   ├── config.py    # TOML parsing
│   ├── scaffold.py  # Project templates
│   ├── runner.py    # Task execution
│   ├── watcher.py   # File monitoring
│   └── tui.py       # Interactive dashboard
├── templates/       # Project templates
│   ├── python-cli/
│   ├── flask-api/
│   └── django-app/
└── tests/           # Unit tests
```

---

## 🔧 Data Locations

- **Database**: `~/.pro-mgr/pro-mgr.db`
- **Pip cache**: `~/.pro-mgr/pip-cache/` (shared across projects)

---

## 📚 Resources

- [Click](https://click.palletsprojects.com/) - CLI framework
- [Textual](https://textual.textualize.io/) - TUI framework
- [Watchdog](https://python-watchdog.readthedocs.io/) - File monitoring

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

# Pro-Mgr TODO

## ✅ Completed

- [x] Core CLI with Click
- [x] SQLite database for projects and snippets
- [x] TOML configuration parser
- [x] Task execution with dependencies
- [x] Virtual environment activation
- [x] Git dirty branch check
- [x] File watcher with debouncing
- [x] Interactive TUI dashboard
- [x] Project templates (python-cli, flask-api, django-app, node-app, dotfiles)
- [x] Shared pip cache across projects
- [x] Package installation
- [x] `pro-mgr init` command for existing projects
- [x] Template variables ({{author}}, {{license}}, etc.)
- [x] Task timeout configuration
- [x] Fish shell activation fix
- [x] Shell completions (bash, zsh, fish)
- [x] `pro-mgr config` command for global settings
- [x] Enhanced TUI (new/add project, config, snippets screens)

---

## v0.4.0 - Parallel Execution & Templates

### Parallel Task Execution

**Why**: Running independent tasks sequentially wastes time. Build + lint + typecheck could run in parallel.

**What**:

- Add `parallel: true` option to task groups
- Thread pool for concurrent task execution
- Aggregate output display (interleaved or per-task)
- Shared exit code (fail if any task fails)

**Success Criteria**: `pro-mgr run my-app all --parallel` runs build, test, lint concurrently

**Complexity**: Medium

---

### Rust Template (rust-cli)

**Why**: Rust is increasingly popular for CLI tools. Template reduces boilerplate setup.

**What**:

- `Cargo.toml` with clap for CLI parsing
- src/main.rs with argument handling
- Basic test structure
- GitHub Actions CI for Rust

**Success Criteria**: `pro-mgr new my-tool --template rust-cli` creates working Rust project

**Complexity**: Low

---

### Go Template (go-api)

**Why**: Go is popular for microservices. Provide opinionated starter.

**What**:

- `go.mod` and main.go
- Basic HTTP server with chi/echo
- Dockerfile included
- Makefile for common tasks

**Success Criteria**: `pro-mgr new my-service --template go-api` creates working Go API

**Complexity**: Low

---

#### Template Inheritance

**Why**: DRY principle for templates. Python projects share common config; inherit from base.

**What**:

- `extends: python-cli` in template.toml
- Merge file trees (child overrides parent)
- Variable inheritance with override capability
- Multi-level inheritance (python-cli → flask-api)

**Success Criteria**: `pro-mgr new my-api --template my-custom-flask` inherits from flask-api

**Complexity**: Medium

---

### Task Output Logging

**Why**: Debug failures by reviewing historical logs. Essential for CI/CD.

**What**:

- `~/.pro-mgr/logs/{project}/{task}/{timestamp}.log`
- Configurable retention (default: 7 days, 50 runs)
- `pro-mgr logs my-app test` to view recent runs
- Log rotation

**Success Criteria**: Task output persists and can be reviewed later

**Complexity**: Low

---

## v0.5.0 - Environment & Configuration

### Environment Variable Management

**Why**: Secrets and environment-specific config need secure, convenient handling.

**What**:

- `pro-mgr env` command group
- Support `.env`, `.env.local`, `.env.{stage}` files
- Environment variable interpolation in tasks
- Secret masking in output

**Success Criteria**: `pro-mgr run my-app deploy --env production` loads correct .env file

**Complexity**: Medium

---

### Config Validation Command

**Why**: Catch typos and misconfigurations before runtime failures.

**What**:

- `pro-mgr validate` command
- Check pro-mgr.toml syntax
- Verify task dependencies exist
- Warn about unused/orphan tasks
- Check template variables

**Success Criteria**: `pro-mgr validate` reports all config issues with clear messages

**Complexity**: Low

---

### Export/Import Configurations

**Why**: Share configurations across machines, backup settings, team onboarding.

**What**:

- `pro-mgr export` → JSON/YAML bundle
- `pro-mgr import` → restore from bundle
- Include global config, projects, snippets
- Migration handling for version differences

**Success Criteria**: Full state can round-trip through export/import

**Complexity**: Medium

---

## v0.6.0 - Project Organization

### Project Groups/Workspaces

**Why**: Large codebases have related projects. Group operations save time.

**What**:

- `pro-mgr group create frontend`
- Add/remove projects from groups
- Run tasks across groups: `pro-mgr run @frontend test`
- Group-level configuration

**Success Criteria**: Can execute same task across all projects in a group

**Complexity**: Medium

---

### Project Tagging and Filtering

**Why**: Find projects quickly by type, status, or custom criteria.

**What**:

- Extend existing tags support
- `pro-mgr project list --tag=python`
- Multiple tag support with AND/OR logic
- Auto-tags based on detected project type

**Success Criteria**: `pro-mgr project list --tag=api --tag=python` filters correctly

**Complexity**: Low

---

### Task History and Statistics

**Why**: Track performance trends, identify flaky tests, measure improvements.

**What**:

- Store task run times and exit codes
- `pro-mgr stats my-app test` shows history
- Average/median/p95 run times
- Success rate trends

**Success Criteria**: Can see that "test suite now runs 20% faster"

**Complexity**: Medium

---

## v0.7.0 - Remote & Advanced Features

### Remote Project Support (SSH)

**Why**: Manage projects on remote servers without local checkout.

**What**:

- `pro-mgr project add ssh://user@host:/path`
- SSH key authentication
- Remote task execution
- Output streaming

**Success Criteria**: Run tasks on remote server from local CLI

**Complexity**: High

---

### Project Health Checks

**Why**: Quick overview of project status - outdated deps, failing tests, etc.

**What**:

- `pro-mgr health my-app`
- Check: git dirty, outdated deps, last test run, disk usage
- Configurable health rules per project
- Dashboard integration

**Success Criteria**: See all project issues at a glance

**Complexity**: Medium

---

### Dependency Graph Visualization

**Why**: Understand task dependencies at a glance, debug circular dependencies.

**What**:

- `pro-mgr graph my-app` → ASCII/SVG output
- Show task dependencies
- Highlight circular dependencies
- Optional: Open in browser with interactive SVG

**Success Criteria**: Generate visual graph of task dependencies

**Complexity**: Medium

---

## v0.8.0 - Plugin System

### Plugin Architecture

**Why**: Users want custom commands without forking. Ecosystem growth.

**What**:

- Plugin discovery in `~/.pro-mgr/plugins/`
- Python-based plugins with decorator API
- Plugin manifest (plugin.toml)
- `pro-mgr plugin install/list/rm`

**Success Criteria**: Third-party plugin adds new command that works seamlessly

**Complexity**: High

---

### Hook System (Pre/Post Task Hooks)

**Why**: Run setup/teardown automatically. Notifications, cleanup, etc.

**What**:

- `[hooks.pre_task]` and `[hooks.post_task]` in config
- Hook types: shell, notify, webhook
- Per-task and global hooks
- Hook failure handling (continue/abort)

**Success Criteria**: Slack notification sent after every deploy task

**Complexity**: Medium

---

### Custom Template Registry

**Why**: Share templates within team/organization. Avoid template duplication.

**What**:

- `pro-mgr template add <url>`
- Template sources: local path, git repo, HTTP
- Template versioning
- Template updates: `pro-mgr template update`

**Success Criteria**: Can use templates from private git repo

**Complexity**: Medium

---

## v0.9.0 - Polish & Documentation

### Documentation Site

**Why**: Users need reference docs, tutorials, examples. Reduce support burden.

**What**:

- MkDocs or similar static site generator
- Getting started guide
- Command reference
- Plugin development guide
- Deploy to GitHub Pages

**Success Criteria**: Complete docs at pro-mgr.readthedocs.io or similar

**Complexity**: Medium (writing takes time)

---

### CI/CD Platform Integration

**Why**: Reuse pro-mgr tasks in CI without duplicating shell scripts.

**What**:

- `pro-mgr ci github` → Generate .github/workflows
- `pro-mgr ci gitlab` → Generate .gitlab-ci.yml
- Map pro-mgr tasks to CI jobs
- Matrix support for multiple Python versions

**Success Criteria**: Generate working CI config from pro-mgr.toml

**Complexity**: Medium

---

### Dockerfile Generation

**Why**: Containerize projects with consistent best practices.

**What**:

- `pro-mgr docker init`
- Multi-stage builds for Python
- .dockerignore generation
- Compose file for multi-project setups

**Success Criteria**: Generated Dockerfile builds and runs correctly

**Complexity**: Medium

---

### Install Script Modularization

**Why**: install.sh is monolithic and hard to maintain. Separate concerns.

**What**:

- `install/` directory structure:
  - `install.sh` (main orchestrator)
  - `completions/bash.sh`
  - `completions/zsh.sh`
  - `completions/fish.sh`
  - `utils.sh` (colors, helpers)
- Source files as needed
- Easier testing and maintenance

**Success Criteria**: `./install.sh` works same as before, code is modular

**Complexity**: Low

---

### Performance Optimizations

**Why**: CLI should feel instant. Sub-100ms response times.

**What**:

- Lazy imports
- Database query optimization
- Caching for expensive operations
- Profiling and benchmarks

**Success Criteria**: `pro-mgr project list` < 100ms for 100 projects

**Complexity**: Medium

---

## v1.0.0 - Stable Release

### Full Test Coverage

**Why**: Stability for production use. Confidence in releases.

**What**:

- 90%+ line coverage
- Integration tests for all commands
- Edge case coverage
- CI enforcement

**Success Criteria**: All tests pass, coverage gate in CI

**Complexity**: Medium

---

### API Stability Guarantees

**Why**: Users and plugins need stable interfaces.

**What**:

- Semantic versioning policy
- Deprecation warnings (2 minor versions)
- Breaking change documentation
- Migration guides

**Success Criteria**: Clear upgrade path between versions

**Complexity**: Low

---

### Web Dashboard (Optional)

**Why**: Visual project management for those who prefer GUIs.

**What**:

- Local Flask/FastAPI server
- Project list and status
- Task execution with live output
- Configuration editing

**Success Criteria**: `pro-mgr web` opens browser with working dashboard

**Complexity**: High

---

## 🐛 Known Issues

- [ ] **Database locking in high concurrency**: SQLite struggles with many parallel writes. Consider WAL mode or connection pooling.

---

## 💡 Future Ideas (Post v1.0)

- **Cloud sync**: Sync projects/config across machines via pro-mgr cloud account
- **Team collaboration**: Shared snippets, project templates within organization
- **IDE extensions**: VS Code and JetBrains plugins for in-editor task running
- **Mobile companion**: iOS/Android app for monitoring long-running tasks
- **AI integration**: Natural language task creation, smart suggestions

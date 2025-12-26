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
- [x] Project templates (python-cli, flask-api, django-app)
- [x] Shared pip cache across projects
- [x] Package installation
- [x] `pro-mgr init` command for existing projects
- [x] Template variables ({{author}}, {{license}}, etc.)
- [x] Task timeout configuration
- [x] Fish shell activation fix
- [x] Shell completions (bash, zsh, fish)
- [x] `pro-mgr config` command for global settings
- [x] Node.js template (node-app)
- [x] Enhanced TUI (new/add project, config, snippets screens)

---

## 🚧 Roadmap to v1.0.0

### v0.4.0 - Parallel Execution & Templates

- [ ] Parallel task execution
- [ ] Add Rust template (rust-cli)
- [ ] Add Go template (go-api)
- [ ] Task output logging to file

### v0.5.0 - Environment & Configuration

- [ ] Environment variable management (.env files)
- [ ] Config validation command
- [ ] Export/import project configurations

### v0.6.0 - Project Organization

- [ ] Project groups/workspaces
- [ ] Project tagging and filtering
- [ ] Task history and statistics

### v0.7.0 - Remote & Advanced Features

- [ ] Remote project support (SSH)
- [ ] Project health checks
- [ ] Dependency graph visualization

### v0.8.0 - Plugin System

- [ ] Plugin system for custom commands
- [ ] Hook system (pre/post task hooks)
- [ ] Custom template registry

### v0.9.0 - Polish & Documentation

- [ ] Comprehensive documentation site
- [ ] Integration with CI/CD platforms
- [ ] Dockerfile generation for projects
- [ ] Performance optimizations

### v1.0.0 - Stable Release

- [ ] Full test coverage
- [ ] API stability guarantees
- [ ] Web dashboard (optional)
- [ ] Final bug fixes and polish

---

## 🐛 Known Issues

- [ ] Database locking possible in very high concurrency scenarios

---

## 💡 Future Ideas (Post v1.0)

- Cloud sync for project configurations
- Team collaboration features
- IDE extensions (VS Code, JetBrains)
- Mobile companion app for project monitoring

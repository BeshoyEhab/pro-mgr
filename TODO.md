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

---

## 🚧 Future Improvements

### High Priority

- [ ] Add more templates (node-app, rust-cli, go-api)
- [ ] Template variables for customization
- [ ] `pro-mgr init` to create pro-mgr.toml in existing projects
- [ ] Parallel task execution
- [ ] Task timeout configuration

### Medium Priority

- [ ] Project groups/workspaces
- [ ] Environment variable management (.env files)
- [ ] Remote project support (SSH)
- [ ] Task output logging to file
- [ ] Task history and statistics

### Low Priority

- [ ] Plugin system for custom commands
- [ ] Shell completion scripts (bash, zsh, fish)
- [ ] Config validation command
- [ ] Export/import project configurations
- [ ] Web dashboard (optional)

---

## 🐛 Known Issues

- [ ] Database locking in parallel test runs (use separate test db)
- [ ] Fish shell activation script differs from bash

---

## 💡 Ideas

- Integration with CI/CD platforms
- Dockerfile generation for projects
- Dependency graph visualization
- Project health checks

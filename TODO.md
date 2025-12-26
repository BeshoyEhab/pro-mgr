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

---

## 🚧 Future Improvements

### High Priority

- [ ] Add more templates (node-app, rust-cli, go-api)
- [ ] Parallel task execution
- [ ] `pro-mgr config` command to set defaults

### Medium Priority

- [ ] Project groups/workspaces
- [ ] Environment variable management (.env files)
- [ ] Remote project support (SSH)
- [ ] Task output logging to file
- [ ] Task history and statistics

### Low Priority

- [ ] Plugin system for custom commands
- [ ] Config validation command
- [ ] Export/import project configurations
- [ ] Web dashboard (optional)

---

## 🐛 Known Issues

- [ ] Database locking possible in very high concurrency scenarios

---

## 💡 Ideas

- Integration with CI/CD platforms
- Dockerfile generation for projects
- Dependency graph visualization
- Project health checks

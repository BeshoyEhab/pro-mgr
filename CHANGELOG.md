# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-12-26

### Added

- **`pro-mgr config` command** - Manage default settings (author, license, template)
- **Node.js template** - New `node-app` template for Express.js projects
- **Enhanced TUI** - Full feature support in the interactive dashboard:
  - `n` - Create new project with template selection
  - `a` - Add existing project directory
  - `c` - View and edit configuration
  - `Ctrl+S` - Browse and manage code snippets
  - `F5` - Refresh project list

### Changed

- TUI now supports all CLI features

### Fixed

- README GitHub URL now points to correct repository

## [0.2.0] - 2025-12-25

### Added

- `pro-mgr init` command for existing projects
- Template variable support (`{{author}}`, `{{license}}`, etc.)
- Task timeout configuration
- Fish shell activation script
- Shell completions for bash, zsh, and fish

## [0.1.0] - 2025-12-24

### Added

- Core CLI with Click
- SQLite database for projects and snippets
- TOML configuration parser
- Task execution with dependency resolution
- Virtual environment activation
- Git dirty branch check
- File watcher with debouncing
- Interactive TUI dashboard
- Project templates: `python-cli`, `flask-api`, `django-app`
- Shared pip cache across projects
- Package installation

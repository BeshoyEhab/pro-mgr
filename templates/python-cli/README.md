# {{name}}

A Python CLI application.

## Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
python -m {{name_underscore}}.main

# Or use pro-mgr
pro-mgr run {{name}} run
```

## Development

```bash
# Run tests
pro-mgr run {{name}} test

# Run linter
pro-mgr run {{name}} lint
```

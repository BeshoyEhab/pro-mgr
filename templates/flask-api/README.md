# {{name}}

A Flask API application.

## Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Start the development server
pro-mgr run {{name}} serve

# Or use Flask directly
flask --app {{name_underscore}}.app run --debug
```

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check

## Development

```bash
# Run tests
pro-mgr run {{name}} test

# Run linter
pro-mgr run {{name}} lint
```

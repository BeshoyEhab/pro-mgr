# {{name}}

A Django web application.

## Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate
```

## Usage

```bash
# Start the development server
pro-mgr run {{name}} runserver

# Or use Django directly
python manage.py runserver
```

## Development

```bash
# Create migrations
pro-mgr run {{name}} makemigrations

# Apply migrations
pro-mgr run {{name}} migrate

# Run tests
pro-mgr run {{name}} test

# Open Django shell
pro-mgr run {{name}} shell
```

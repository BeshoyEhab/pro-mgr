"""
ASGI config for {{name}} project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{{name_underscore}}.settings')

application = get_asgi_application()

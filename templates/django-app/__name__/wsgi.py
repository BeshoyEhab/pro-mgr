"""
WSGI config for {{name}} project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{{name_underscore}}.settings')

application = get_wsgi_application()

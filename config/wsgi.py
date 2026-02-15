"""
WSGI config for config project.
"""

import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
application = WhiteNoise(application, root=settings.MEDIA_ROOT, prefix="media/")

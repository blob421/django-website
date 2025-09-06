"""
WSGI config for portal project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""
#from whitenoise import WhiteNoise


import	os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",	"portal.settings")


from configurations.wsgi import	get_wsgi_application
application	= get_wsgi_application()
#application = WhiteNoise(application, root='static')
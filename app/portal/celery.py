import	os
from celery	import Celery
from django.conf import	settings
import configurations

os.environ.setdefault("DJANGO_SETTINGS_MODULE",	"portal.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", os.getenv("DJANGO_CONFIGURATION", "Dev"))

configurations.setup()

app	= Celery("portal")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
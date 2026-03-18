
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from home.views import api_get_dashboard_data
from django.test import RequestFactory

factory = RequestFactory()
url = '/api/dashboard-data/?regiao=todos&uf=todos&rm=todos&porte=todos&classification=quintil&display_format=numero&calculation_mode=total&include_2000_data=false'
request = factory.get(url)

try:
    response = api_get_dashboard_data(request)
    print(f"Status Code: {response.status_code}")
    print(f"Content: {response.content[:500]}")
except Exception as e:
    import traceback
    traceback.print_exc()

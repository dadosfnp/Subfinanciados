
import os
import django
from django.db.models import Avg, StdDev

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from home.models import Municipio

q = Municipio.objects.all()
count = q.count()
avg_rc24 = q.aggregate(Avg('rc_24_pc'))['rc_24_pc__avg']
null_rc24 = q.filter(rc_24_pc__isnull=True).count()

print(f"Total Municipios: {count}")
print(f"Average RC24: {avg_rc24}")
print(f"Null RC24: {null_rc24}")

if avg_rc24 == 0 or avg_rc24 is None:
    print("WARNING: Average RC24 is 0 or None. This will cause a division by zero error in the view.")

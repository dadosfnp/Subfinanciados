from django.conf import settings

def public_settings(request):
    return {"MAPBOX_PUBLIC_TOKEN": settings.MAPBOX_PUBLIC_TOKEN}
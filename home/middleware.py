from django.http import JsonResponse
from django.urls import resolve
from .models import APIKey # Ou de onde seu modelo APIKey estiver

class APIKeyAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Define as URLs que requerem autenticação por chave de API
        # Adapte conforme as suas URLs de API
        self.api_paths = ['/api/get_dependent_filters/', '/api/get_dashboard_data/']

    def __call__(self, request):
        # Verifica se o caminho da requisição está entre os que requerem chave de API
        if request.path in self.api_paths:
            api_key = request.headers.get('X-API-KEY') # Tenta pegar a chave do cabeçalho X-API-KEY

            if not api_key:
                return JsonResponse({'error': 'API Key is missing'}, status=401)
            
            try:
                # Tenta encontrar a chave no banco de dados e verifica se está ativa
                APIKey.objects.get(key=api_key, is_active=True)
            except APIKey.DoesNotExist:
                return JsonResponse({'error': 'Invalid or inactive API Key'}, status=403)
        
        response = self.get_response(request)
        return response
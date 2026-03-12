import os
import django

# Setup do Django para rodar script isolado
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # Ajuste o nome do módulo de settings se necessário
django.setup()

from detail.views import conjunto_detalhe_view
from django.test import RequestFactory
import time

def testar_performance_atual():
    factory = RequestFactory()
    # Cria uma requisição simulada com parâmetros comuns
    request = factory.get('/detail/conjunto/', {'uf': 'SP', 'porte': 'todos'})
    
    start_time = time.time()
    response = conjunto_detalhe_view(request)
    end_time = time.time()
    
    print(f"Tempo de execução (Atual): {end_time - start_time:.4f} segundos")

if __name__ == '__main__':
    testar_performance_atual()

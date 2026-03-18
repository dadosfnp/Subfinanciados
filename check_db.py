import psycopg2
from urllib.parse import quote_plus

# Testa conexão com URL raw (caracteres especiais podem ser problema)
host = "aws-0-us-west-2.pooler.supabase.com"
port = 6543
dbname = "postgres"
user = "postgres.wytsfxkusrziuqorvrzf"
password = "D9e_-M!cEhEw3,j"  # Senha com chars especiais

try:
    conn = psycopg2.connect(
        host=host, port=port, dbname=dbname,
        user=user, password=password, sslmode='require'
    )
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM home_municipio')
    print('Municipios:', cur.fetchone()[0])
    cur.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s', ('public',))
    print('Tabelas no banco:', cur.fetchone()[0])
    conn.close()
except Exception as e:
    print('Erro de conexao:', e)

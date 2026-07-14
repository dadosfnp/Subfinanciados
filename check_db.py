import os
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("Erro: variável DATABASE_URL não definida. Configure o arquivo .env.")
    exit(1)

parsed = urlparse(database_url)

try:
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        dbname=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
        sslmode="require",
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM home_municipio")
    print("Municipios:", cur.fetchone()[0])
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s",
        ("public",),
    )
    print("Tabelas no banco:", cur.fetchone()[0])
    conn.close()
except Exception as e:
    print("Erro de conexao:", e)

"""
Configurações do projeto Biblioteca.

As credenciais do banco ficam no arquivo .env (na raiz do repositório),
na variável DATABASE_URL. Veja o .env.example.
"""
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# src/
BASE_DIR = Path(__file__).resolve().parent.parent
# raiz do repositório (onde fica o .env)
RAIZ_PROJETO = BASE_DIR.parent

load_dotenv(RAIZ_PROJETO / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "chave-so-para-desenvolvimento-troque-em-producao")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "biblioteca",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # mostra uma página amigável quando o banco está fora do ar
    "biblioteca.middleware.ErroConexaoMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------------
# Banco de dados (PostgreSQL local)
# ---------------------------------------------------------------------
def ler_database_url():
    """Lê a DATABASE_URL do .env e falha com mensagem clara se estiver errada."""
    url = os.getenv("DATABASE_URL", "").strip()

    if not url:
        raise ImproperlyConfigured(
            "\n\nDATABASE_URL não encontrada!\n"
            "1) Copie o arquivo .env.example para .env (na raiz do projeto)\n"
            "2) Coloque a senha do seu PostgreSQL em DATABASE_URL\n"
        )
    if "SUA_SENHA" in url:
        raise ImproperlyConfigured(
            "\n\nA DATABASE_URL no .env ainda está com o valor de exemplo!\n"
            "Troque SUA_SENHA pela senha do usuário postgres (a que você definiu ao instalar o PostgreSQL).\n"
        )
    return url


DATABASES = {
    "default": dj_database_url.parse(
        ler_database_url(),
        conn_max_age=0,      # abre e fecha a conexão a cada requisição
    )
}

# ---------------------------------------------------------------------
# Idioma e data
# ---------------------------------------------------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
# Com USE_TZ = False o Django configura a conexão no fuso de São Paulo,
# então o CURRENT_DATE do Postgres (usado na view, function e procedures)
# é a data do Brasil, e não a de Londres (UTC). Evita "pular o dia" à noite.
USE_TZ = False

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Mensagens (sucesso/erro) guardadas em cookie: não dependem do banco
MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

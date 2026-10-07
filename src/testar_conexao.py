"""
Confere se o banco está pronto: conecta no PostgreSQL e verifica se as
tabelas, a view, a function e as procedures existem.

Uso (dentro da pasta src/, com o venv ativado):
    python testar_conexao.py
"""
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# o .env fica na raiz do repositório (uma pasta acima de src/)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TABELAS = ["livros", "membros", "emprestimos"]
VIEWS = ["vw_emprestimos_detalhados"]
FUNCOES = ["fn_calcular_multa"]
PROCEDURES = ["sp_registrar_emprestimo", "sp_registrar_devolucao"]


def existe(cursor, sql, nome):
    cursor.execute(sql, [nome])
    return cursor.fetchone()[0]


def main():
    url = os.getenv("DATABASE_URL", "").strip()
    if not url or "SUA_SENHA" in url:
        print("ERRO: configure a DATABASE_URL no arquivo .env (veja o .env.example).")
        sys.exit(1)

    try:
        conexao = psycopg2.connect(url, connect_timeout=10)
    except psycopg2.OperationalError as erro:
        print("ERRO: não consegui conectar no banco.")
        print("Detalhe:", str(erro).strip().splitlines()[0])
        sys.exit(1)

    print("Conectado ao banco com sucesso!\n")
    faltando = 0

    with conexao, conexao.cursor() as cursor:
        sql_tabela = """SELECT EXISTS (SELECT 1 FROM information_schema.tables
                         WHERE table_schema = 'public' AND table_name = %s
                           AND table_type = 'BASE TABLE')"""
        sql_view = """SELECT EXISTS (SELECT 1 FROM information_schema.views
                       WHERE table_schema = 'public' AND table_name = %s)"""
        # prokind: 'f' = function, 'p' = procedure
        sql_rotina = """SELECT EXISTS (SELECT 1 FROM pg_proc p
                         JOIN pg_namespace n ON n.oid = p.pronamespace
                         WHERE n.nspname = 'public' AND p.proname = %s AND p.prokind = '{}')"""

        itens = (
            [("TABELA", nome, sql_tabela) for nome in TABELAS]
            + [("VIEW", nome, sql_view) for nome in VIEWS]
            + [("FUNCTION", nome, sql_rotina.format("f")) for nome in FUNCOES]
            + [("PROCEDURE", nome, sql_rotina.format("p")) for nome in PROCEDURES]
        )

        for tipo, nome, sql in itens:
            ok = existe(cursor, sql, nome)
            situacao = "OK" if ok else "FALTANDO"
            extra = ""
            if ok and tipo in ("TABELA", "VIEW"):
                # nome vem da lista fixa acima, não do usuário
                cursor.execute(f"SELECT COUNT(*) FROM {nome}")
                extra = f"  ({cursor.fetchone()[0]} registro(s))"
            if not ok:
                faltando += 1
            print(f"[{situacao:^8}] {tipo:<10} {nome}{extra}")

    conexao.close()
    print()
    if faltando:
        print(f"{faltando} item(ns) FALTANDO. Rode os scripts de database/ em ordem no banco biblioteca.")
        sys.exit(1)
    print("Tudo certo! Pode rodar: python manage.py runserver")


if __name__ == "__main__":
    main()

"""
Telas da biblioteca.

Onde cada recurso do banco é usado:
  - VIEW      vw_emprestimos_detalhados -> emprestimos_lista e emprestimo_detalhe
  - FUNCTION  fn_calcular_multa         -> emprestimo_detalhe (e dentro da procedure de devolução)
  - PROCEDURE sp_registrar_emprestimo   -> emprestimo_novo
  - PROCEDURE sp_registrar_devolucao    -> emprestimo_devolver (botão "Devolver" da lista)
"""
from django.contrib import messages
from django.db import DatabaseError, IntegrityError, OperationalError, connection, transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import EmprestimoForm, LivroForm, MembroForm
from .models import Emprestimo, Livro, Membro


# ---------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------
def mensagem_do_banco(erro):
    """
    Pega só o texto do RAISE EXCEPTION (sem 'ERROR:', CONTEXT, traceback...).
    O Django embrulha o erro do psycopg2; o original fica em erro.__cause__.
    """
    original = erro.__cause__ or erro
    diag = getattr(original, "diag", None)
    if diag is not None and diag.message_primary:
        return diag.message_primary
    # plano B: primeira linha da mensagem
    return str(erro).strip().splitlines()[0].replace("ERROR:", "").strip()


def dictfetchall(cursor):
    """Transforma o resultado do cursor em lista de dicionários {coluna: valor}."""
    colunas = [col[0] for col in cursor.description]
    return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]


def inicio(request):
    """Tela inicial: a estante com os livros + resumo vindo da VIEW."""
    livros = list(Livro.objects.all())

    with connection.cursor() as cursor:
        # quantos empréstimos em cada situação (a regra da situação está na VIEW)
        cursor.execute("SELECT situacao, COUNT(*) FROM vw_emprestimos_detalhados GROUP BY situacao")
        contagem = dict(cursor.fetchall())

        cursor.execute("""
            SELECT id_emprestimo, titulo, nome_membro, dias_atraso
              FROM vw_emprestimos_detalhados
             WHERE situacao = %s
             ORDER BY dias_atraso DESC
        """, ["Em atraso"])
        atrasados = dictfetchall(cursor)

    em_atraso = contagem.get("Em atraso", 0)
    return render(request, "biblioteca/inicio.html", {
        "livros": livros,
        "ativos": em_atraso + contagem.get("No prazo", 0),
        "em_atraso": em_atraso,
        "atrasados": atrasados,
    })


# ---------------------------------------------------------------------
# LIVROS
# ---------------------------------------------------------------------
def livros_lista(request):
    busca = request.GET.get("q", "").strip()
    livros = Livro.objects.all()
    if busca:
        # o ORM gera SQL parametrizado (ILIKE %s), sem risco de SQL injection
        livros = livros.filter(Q(titulo__icontains=busca) | Q(autor__icontains=busca))
    return render(request, "biblioteca/livros_lista.html", {"livros": livros, "busca": busca})


def livro_criar(request):
    form = LivroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        livro = form.save(commit=False)
        # livro novo: todos os exemplares estão disponíveis
        livro.exemplares_disponiveis = livro.exemplares_total
        livro.save()
        messages.success(request, f'Livro "{livro.titulo}" cadastrado!')
        return redirect("livros_lista")
    return render(request, "biblioteca/form_generico.html", {
        "form": form, "titulo_pagina": "Novo livro", "url_voltar": "livros_lista",
    })


def livro_editar(request, pk):
    livro = get_object_or_404(Livro, pk=pk)
    # quantos exemplares estão emprestados agora (antes de mexer no total)
    emprestados = livro.exemplares_total - livro.exemplares_disponiveis

    form = LivroForm(request.POST or None, instance=livro)
    if request.method == "POST" and form.is_valid():
        novo_total = form.cleaned_data["exemplares_total"]
        if novo_total < emprestados:
            form.add_error("exemplares_total",
                           f"Há {emprestados} exemplar(es) emprestado(s); o total não pode ser menor que isso.")
        else:
            livro = form.save(commit=False)
            livro.exemplares_disponiveis = novo_total - emprestados
            livro.save()
            messages.success(request, f'Livro "{livro.titulo}" atualizado!')
            return redirect("livros_lista")
    return render(request, "biblioteca/form_generico.html", {
        "form": form, "titulo_pagina": f"Editar livro: {livro.titulo}", "url_voltar": "livros_lista",
    })


def livro_excluir(request, pk):
    livro = get_object_or_404(Livro, pk=pk)
    if request.method == "POST":
        try:
            with transaction.atomic():
                livro.delete()
            messages.success(request, f'Livro "{livro.titulo}" excluído.')
        except IntegrityError:
            # a FK de emprestimos impede apagar livro que já foi emprestado
            messages.error(request, "Não dá para excluir: este livro tem empréstimos registrados.")
        return redirect("livros_lista")
    return render(request, "biblioteca/confirmar_exclusao.html", {
        "objeto": f'o livro "{livro.titulo}"', "url_voltar": "livros_lista",
    })


# ---------------------------------------------------------------------
# MEMBROS
# ---------------------------------------------------------------------
def membros_lista(request):
    return render(request, "biblioteca/membros_lista.html", {"membros": Membro.objects.all()})


def membro_criar(request):
    form = MembroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        membro = form.save()
        messages.success(request, f"Membro {membro.nome} cadastrado!")
        return redirect("membros_lista")
    return render(request, "biblioteca/form_generico.html", {
        "form": form, "titulo_pagina": "Novo membro", "url_voltar": "membros_lista",
    })


def membro_editar(request, pk):
    membro = get_object_or_404(Membro, pk=pk)
    form = MembroForm(request.POST or None, instance=membro)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Membro {membro.nome} atualizado!")
        return redirect("membros_lista")
    return render(request, "biblioteca/form_generico.html", {
        "form": form, "titulo_pagina": f"Editar membro: {membro.nome}", "url_voltar": "membros_lista",
    })


def membro_excluir(request, pk):
    membro = get_object_or_404(Membro, pk=pk)
    if request.method == "POST":
        try:
            with transaction.atomic():
                membro.delete()
            messages.success(request, f"Membro {membro.nome} excluído.")
        except IntegrityError:
            messages.error(request, "Não dá para excluir: este membro tem empréstimos registrados.")
        return redirect("membros_lista")
    return render(request, "biblioteca/confirmar_exclusao.html", {
        "objeto": f"o membro {membro.nome}", "url_voltar": "membros_lista",
    })


# ---------------------------------------------------------------------
# NOVO EMPRÉSTIMO -> PROCEDURE sp_registrar_emprestimo
# ---------------------------------------------------------------------
def emprestimo_novo(request):
    form = EmprestimoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        id_livro = form.cleaned_data["livro"].pk
        id_membro = form.cleaned_data["membro"].pk
        dias = form.cleaned_data["dias"]
        try:
            # tudo numa transação: se a procedure der RAISE EXCEPTION, nada é gravado
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("CALL sp_registrar_emprestimo(%s, %s, %s)",
                                   [id_livro, id_membro, dias])
            messages.success(request, "Empréstimo registrado com sucesso!")
            return redirect("emprestimos_lista")
        except OperationalError:
            raise  # problema de conexão: o middleware mostra a página amigável
        except DatabaseError as erro:
            # erro de regra de negócio vindo do RAISE EXCEPTION da procedure
            messages.error(request, mensagem_do_banco(erro))
    return render(request, "biblioteca/emprestimo_novo.html", {"form": form})


# ---------------------------------------------------------------------
# LISTA DE EMPRÉSTIMOS -> VIEW vw_emprestimos_detalhados
# ---------------------------------------------------------------------
FILTROS_SITUACAO = [
    ("", "Todas"),
    ("Ativos", "Ativos (no prazo + em atraso)"),
    ("No prazo", "No prazo"),
    ("Em atraso", "Em atraso"),
    ("Devolvido", "Devolvido"),
]


def emprestimos_lista(request):
    situacao = request.GET.get("situacao", "")

    sql = """
        SELECT id_emprestimo, titulo, nome_membro, data_emprestimo,
               data_prevista, data_devolucao, situacao, dias_atraso
          FROM vw_emprestimos_detalhados
    """
    parametros = []
    if situacao == "Ativos":
        sql += " WHERE situacao <> 'Devolvido'"
    elif situacao in ("No prazo", "Em atraso", "Devolvido"):
        sql += " WHERE situacao = %s"
        parametros.append(situacao)
    sql += " ORDER BY id_emprestimo DESC"

    with connection.cursor() as cursor:
        cursor.execute(sql, parametros)
        emprestimos = dictfetchall(cursor)

    return render(request, "biblioteca/emprestimos_lista.html", {
        "emprestimos": emprestimos,
        "situacao": situacao,
        "filtros": FILTROS_SITUACAO,
    })


# ---------------------------------------------------------------------
# DEVOLUÇÃO -> PROCEDURE sp_registrar_devolucao
# ---------------------------------------------------------------------
@require_POST
def emprestimo_devolver(request, pk):
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("CALL sp_registrar_devolucao(%s)", [pk])
        # lê a multa que a procedure gravou (calculada pela function)
        multa = Emprestimo.objects.get(pk=pk).multa
        if multa > 0:
            valor = f"{multa:.2f}".replace(".", ",")  # formato brasileiro: 20,00
            messages.warning(request, f"Devolução registrada. Multa por atraso: R$ {valor}")
        else:
            messages.success(request, "Devolução registrada, sem multa!")
        return redirect("emprestimo_detalhe", pk=pk)
    except OperationalError:
        raise
    except DatabaseError as erro:
        messages.error(request, mensagem_do_banco(erro))
        return redirect("emprestimos_lista")


# ---------------------------------------------------------------------
# DETALHE -> FUNCTION fn_calcular_multa (+ VIEW para a situação)
# ---------------------------------------------------------------------
def emprestimo_detalhe(request, pk):
    with connection.cursor() as cursor:
        # dados principais e situação vêm da VIEW
        cursor.execute("""
            SELECT id_emprestimo, titulo, nome_membro, data_emprestimo,
                   data_prevista, data_devolucao, situacao, dias_atraso
              FROM vw_emprestimos_detalhados
             WHERE id_emprestimo = %s
        """, [pk])
        resultado = dictfetchall(cursor)
        if not resultado:
            raise Http404("Empréstimo não encontrado")
        dados = resultado[0]

        # multa calculada AGORA pelo banco, usando a FUNCTION
        cursor.execute("SELECT fn_calcular_multa(%s)", [pk])
        multa_calculada = cursor.fetchone()[0]

    # informações extras (autor, e-mail, multa gravada) pelo ORM
    emprestimo = Emprestimo.objects.select_related("livro", "membro").get(pk=pk)

    return render(request, "biblioteca/emprestimo_detalhe.html", {
        "dados": dados,
        "emprestimo": emprestimo,
        "multa_calculada": multa_calculada,
    })

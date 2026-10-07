"""
Models da biblioteca.

IMPORTANTE: todas as tabelas são criadas pelos scripts em database/.
Por isso os models usam managed = False: o Django só LÊ e GRAVA nelas,
nunca cria, altera ou apaga a estrutura.
"""
from django.db import models


class Livro(models.Model):
    titulo = models.CharField("Título", max_length=200)
    autor = models.CharField("Autor", max_length=150)
    isbn = models.CharField("ISBN", max_length=20, unique=True)
    exemplares_total = models.IntegerField("Total de exemplares")
    exemplares_disponiveis = models.IntegerField("Exemplares disponíveis")

    class Meta:
        managed = False
        db_table = "livros"
        ordering = ["titulo"]

    def __str__(self):
        return self.titulo


class Membro(models.Model):
    nome = models.CharField("Nome", max_length=150)
    email = models.EmailField("E-mail", max_length=150, unique=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True, null=True)
    criado_em = models.DateTimeField("Cadastrado em", auto_now_add=True)

    class Meta:
        managed = False
        db_table = "membros"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Emprestimo(models.Model):
    # db_column aponta para o nome real da coluna no banco
    livro = models.ForeignKey(Livro, on_delete=models.DO_NOTHING, db_column="id_livro")
    membro = models.ForeignKey(Membro, on_delete=models.DO_NOTHING, db_column="id_membro")
    data_emprestimo = models.DateField()
    data_prevista = models.DateField()
    data_devolucao = models.DateField(null=True, blank=True)
    multa = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        managed = False
        db_table = "emprestimos"

    def __str__(self):
        return f"Empréstimo {self.pk}"

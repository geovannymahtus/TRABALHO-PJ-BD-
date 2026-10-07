from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),

    # Livros (CRUD)
    path("livros/", views.livros_lista, name="livros_lista"),
    path("livros/novo/", views.livro_criar, name="livro_criar"),
    path("livros/<int:pk>/editar/", views.livro_editar, name="livro_editar"),
    path("livros/<int:pk>/excluir/", views.livro_excluir, name="livro_excluir"),

    # Membros (CRUD)
    path("membros/", views.membros_lista, name="membros_lista"),
    path("membros/novo/", views.membro_criar, name="membro_criar"),
    path("membros/<int:pk>/editar/", views.membro_editar, name="membro_editar"),
    path("membros/<int:pk>/excluir/", views.membro_excluir, name="membro_excluir"),

    # Empréstimos (usam VIEW, FUNCTION e PROCEDURES)
    path("emprestimos/", views.emprestimos_lista, name="emprestimos_lista"),
    path("emprestimos/novo/", views.emprestimo_novo, name="emprestimo_novo"),
    path("emprestimos/<int:pk>/", views.emprestimo_detalhe, name="emprestimo_detalhe"),
    path("emprestimos/<int:pk>/devolver/", views.emprestimo_devolver, name="emprestimo_devolver"),
]

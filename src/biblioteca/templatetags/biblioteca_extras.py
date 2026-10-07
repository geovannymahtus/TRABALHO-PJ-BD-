"""Filtros de template usados só para o visual (cores das lombadas, iniciais...)."""
from django import template

register = template.Library()

# cores de capa de livro (encadernação)
CORES_LOMBADA = ["#1F4D3A", "#7A2E2E", "#2D4F9E", "#9A7424", "#4B3F6B", "#2F6B6B", "#8A5A2B", "#3E4A3D"]


@register.filter
def cor(objeto):
    """Cor fixa para cada livro/membro, baseada no id."""
    return CORES_LOMBADA[objeto.pk % len(CORES_LOMBADA)]


@register.filter
def estilo_lombada(livro):
    """Altura e largura variam um pouco para a estante parecer de verdade."""
    altura = 175 + (livro.pk * 37) % 60
    largura = 52 + min(len(livro.titulo), 32) // 2
    return f"--cor:{cor(livro)};--altura:{altura}px;--largura:{largura}px"


@register.filter
def exemplares(livro):
    """Lista com um item por exemplar: True = disponível, False = emprestado."""
    total = min(livro.exemplares_total, 12)
    disponiveis = min(livro.exemplares_disponiveis, total)
    return [True] * disponiveis + [False] * (total - disponiveis)


@register.filter
def iniciais(nome):
    """'Ana Souza' -> 'AS'"""
    partes = nome.split()
    if not partes:
        return "?"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[-1][0]).upper()

from django import forms

from .models import Livro, Membro


class SemDoisPontos:
    """Tira o ':' que o Django coloca depois de cada rótulo."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)


class LivroForm(SemDoisPontos, forms.ModelForm):
    # exemplares_disponiveis não aparece no formulário: é calculado na view
    exemplares_total = forms.IntegerField(label="Total de exemplares", min_value=1, max_value=1000)

    class Meta:
        model = Livro
        fields = ["titulo", "autor", "isbn", "exemplares_total"]


class MembroForm(SemDoisPontos, forms.ModelForm):
    class Meta:
        model = Membro
        fields = ["nome", "email", "telefone"]


class EmprestimoForm(SemDoisPontos, forms.Form):
    livro = forms.ModelChoiceField(queryset=Livro.objects.all(), label="Livro")
    membro = forms.ModelChoiceField(queryset=Membro.objects.all(), label="Membro",
                                    empty_label="Selecione um membro")
    dias = forms.IntegerField(label="Prazo (dias)", min_value=1, max_value=60, initial=7)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A lista só MOSTRA livros com exemplar disponível.
        # A validação de verdade (estoque, limite de 3 empréstimos) fica com a
        # PROCEDURE sp_registrar_emprestimo no banco.
        disponiveis = Livro.objects.filter(exemplares_disponiveis__gt=0).order_by("titulo")
        self.fields["livro"].widget.choices = [("", "Selecione um livro")] + [
            (l.pk, f"{l.titulo} — {l.autor} ({l.exemplares_disponiveis} disponível(is))")
            for l in disponiveis
        ]

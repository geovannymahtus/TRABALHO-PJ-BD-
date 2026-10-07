"""Mostra uma página amigável quando não dá para conectar no banco."""
from django.db import InterfaceError, OperationalError
from django.shortcuts import render


class ErroConexaoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # OperationalError/InterfaceError = problema de conexão (senha, host, internet...)
        if isinstance(exception, (OperationalError, InterfaceError)):
            detalhe = str(exception).strip().splitlines()[0] if str(exception).strip() else ""
            return render(request, "biblioteca/erro_conexao.html", {"detalhe": detalhe}, status=503)
        return None

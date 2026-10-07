# Roteiro do vídeo (8 a 10 minutos)

> **Antes de gravar:** rode de novo o `database/inserts/06_dados_exemplo.sql` no banco `biblioteca` para os dados ficarem "limpos", e deixe abertos: o navegador com o sistema (`runserver` rodando), o VS Code com a pasta `database/` e o pgAdmin (Query Tool no banco `biblioteca`) ou o `psql`.

| Parte | Tempo sugerido | Acumulado |
|---|---|---|
| 1. Apresentação | 0:45 | 0:45 |
| 2. Telas | 1:45 | 2:30 |
| 3. View | 1:30 | 4:00 |
| 4. Function | 1:30 | 5:30 |
| 5. Procedures | 2:00 | 7:30 |
| 6. Fluxo integrado | 1:45 | 9:15 |
| Encerramento | 0:15 | 9:30 |

---

## 1) Apresentação (0:00 – 0:45)

- "Oi, eu sou **[seu nome]**, esse é meu trabalho de Banco de Dados: um sistema de biblioteca."
- Tecnologias: Python + Django, PostgreSQL.
- Ideia central: "as regras importantes ficam **no banco**: uma View para consulta, uma Function para cálculo e Procedures para as operações de escrita. O Django só chama."
- Mostrar rapidinho a estrutura do repositório (pasta `database/` com os scripts numerados).

## 2) Telas (0:45 – 2:30)

- **Estante (início):** cada lombada é um livro do banco; o espaço tracejado é o "Grande Sertão", com todos os exemplares emprestados. Mostrar a lista de atrasados (vem da View).
- **Livros:** mostrar a lista, fazer uma busca (ex.: "Machado"), mostrar a coluna disponíveis/total ("Grande Sertão" está 0/1).
- **Membros:** mostrar a lista.
- **Novo empréstimo:** mostrar o formulário (só aparecem livros com exemplar disponível).
- **Empréstimos:** mostrar a lista com as situações coloridas e o filtro.
- **Detalhe:** abrir um empréstimo em atraso e mostrar a multa.
- Apontar o **aviso azul no rodapé** de cada tela que usa recurso do banco.

## 3) View — `vw_emprestimos_detalhados` (2:30 – 4:00)

- Abrir `database/views/02_vw_emprestimos_detalhados.sql`.
- **Motivo:** a lista de empréstimos precisa de dados de 3 tabelas e de uma regra (situação/atraso). Em vez de repetir JOIN e CASE no Python, o banco entrega pronto.
- **Tabelas:** `emprestimos` JOIN `livros` JOIN `membros`.
- **Retorno:** id do empréstimo, título, nome do membro, datas, `situacao` (CASE: Devolvido / Em atraso / No prazo) e `dias_atraso` (`CURRENT_DATE - data_prevista`, ou 0).
- No pgAdmin (Query Tool): `SELECT * FROM vw_emprestimos_detalhados WHERE situacao = 'Em atraso';`
- **Tela:** Empréstimos → filtrar "Em atraso" → mesmo resultado. Mostrar no `views.py` a função `emprestimos_lista` com o `SELECT ... FROM vw_emprestimos_detalhados WHERE situacao = %s` (parametrizado).

## 4) Function — `fn_calcular_multa` (4:00 – 5:30)

- Abrir `database/functions/03_fn_calcular_multa.sql`.
- **O que faz:** calcula multa de R$ 2,00 por dia de atraso. Só calcula, não altera nada (`STABLE`).
- **Parâmetro:** `p_id_emprestimo integer`. **Retorno:** `numeric`.
- **Lógica:** se já devolveu, conta até `data_devolucao`; senão, até `CURRENT_DATE`. `GREATEST(..., 0)` garante que nunca fica negativa.
- No pgAdmin (Query Tool): `SELECT id, fn_calcular_multa(id) FROM emprestimos;` (empréstimo 3 → R$ 20,00; 4 → R$ 16,00).
- **Onde é usada:** tela Detalhe (`SELECT fn_calcular_multa(%s)` na view `emprestimo_detalhe`) e **dentro** da procedure de devolução.

## 5) Procedures (5:30 – 7:30)

### `sp_registrar_emprestimo(p_id_livro, p_id_membro, p_dias)`
- Abrir `04_sp_registrar_emprestimo.sql`.
- **Operações:** valida prazo → livro existe (com `FOR UPDATE`) → membro existe → tem exemplar → membro tem menos de 3 ativos → `INSERT` em emprestimos → `UPDATE` baixando o estoque.
- Erros com `RAISE EXCEPTION` em português. Sem `COMMIT`: quem controla a transação é o Django (`transaction.atomic()`), então se der erro **nada** é gravado.
- **Tela que chama:** Novo empréstimo → `CALL sp_registrar_emprestimo(%s, %s, %s)` no `views.py`.

### `sp_registrar_devolucao(p_id_emprestimo)`
- Abrir `05_sp_registrar_devolucao.sql`.
- **Operações:** valida se existe e se não foi devolvido → grava `data_devolucao = CURRENT_DATE` → grava `multa = fn_calcular_multa(id)` → devolve o exemplar ao estoque.
- **Tela que chama:** botão Devolver em Empréstimos → `CALL sp_registrar_devolucao(%s)`.

## 6) Fluxo integrado: tela → banco → recurso → resultado (7:30 – 9:15)

1. **Erro de estoque:** abrir "Novo empréstimo" em duas abas, escolher um livro com 1 exemplar (ex.: "Engenharia de Software") e confirmar nas duas. A segunda mostra a mensagem da procedure: *"O livro ... não tem exemplares disponíveis"*.
2. **Erro de limite:** tentar emprestar qualquer livro para a **Ana Souza** (já tem 3 ativos) → mensagem *"O membro Ana Souza já tem 3 empréstimos ativos..."*.
3. **Sucesso:** emprestar um livro para o Bruno → aparece na lista como "No prazo" (via View) → em Livros o disponível baixou 1.
4. **Devolução com multa:** em Empréstimos, filtrar "Em atraso", clicar **Devolver** no empréstimo 3 → mensagem com a multa de R$ 20,00 → no detalhe, situação "Devolvido" e multa gravada (calculada pela Function dentro da Procedure) → em Livros, "Grande Sertão" voltou para 1/1.
5. **Erro de devolver duas vezes:** no pgAdmin `CALL sp_registrar_devolucao(3);` → *"O empréstimo 3 já foi devolvido em ..."*.

Resumo falado: "tela → Django chama o banco → View/Function/Procedure processam → resultado volta para a tela".

## Encerramento (9:15 – 9:30)

- "Os scripts estão em `database/`, o passo a passo no README. Obrigado!"

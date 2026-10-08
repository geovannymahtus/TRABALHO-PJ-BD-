# 📚 Sistema de Biblioteca

Trabalho individual de Banco de Dados: um sistema web de biblioteca em que as regras de negócio ficam **dentro do PostgreSQL**, em uma View, uma Function e duas Procedures, e a aplicação Django só chama esses recursos.

![Tela inicial: a estante com os livros do banco](docs/img/01_estante.png)

## Identificação

| | |
|---|---|
| **Nome** | [Geovanny Mahtus Aguiar Silva] |
| **Disciplina** | Banco de Dados |
| **Professor** | [Anderson Soares] |

## Sumário

1. [Sobre o projeto](#sobre-o-projeto)
2. [Tecnologias](#tecnologias)
3. [Banco de dados](#banco-de-dados)
4. [Telas](#telas)
5. [Como executar](#como-executar)
6. [Como testar](#como-testar)
7. [Estrutura do repositório](#estrutura-do-repositório)
8. [Vídeo](#vídeo)

## Sobre o projeto

O sistema permite:

- cadastrar, buscar, editar e excluir **livros** e **membros**;
- registrar **empréstimos**, respeitando o estoque e o limite de 3 empréstimos ativos por membro;
- registrar **devoluções**, calculando multa de **R$ 2,00 por dia de atraso**;
- acompanhar a **situação** de cada empréstimo: *No prazo*, *Em atraso* ou *Devolvido*.

O objetivo é mostrar que **o banco processa os dados**: o cálculo da situação, o cálculo da multa e as validações de empréstimo e devolução são feitos pelo PostgreSQL, não pelo Python.

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Framework web | Django 5 (templates do Django) |
| Visual | Pico.css (via CDN) + CSS próprio, fontes Literata e Courier Prime |
| Banco de dados | PostgreSQL |
| Driver | psycopg2-binary |
| Configuração | python-dotenv + dj-database-url |

## Banco de dados

**SGBD:** PostgreSQL, rodando localmente (banco `biblioteca`).

Os scripts da pasta `database/` são a **fonte da verdade**: são eles que criam as tabelas, a view, a function e as procedures. Os models do Django usam `managed = False` e apontam para as tabelas existentes (`db_table`), então o Django **não cria nem altera** nada disso.

### Tabelas

| Tabela | Colunas | Restrições |
|---|---|---|
| `livros` | id, titulo, autor, isbn, exemplares_total, exemplares_disponiveis | PK; `isbn` UNIQUE; CHECK `exemplares_disponiveis` entre 0 e `exemplares_total` |
| `membros` | id, nome, email, telefone, criado_em | PK; `email` UNIQUE |
| `emprestimos` | id, id_livro, id_membro, data_emprestimo, data_prevista, data_devolucao, multa | PK; FK para `livros` e `membros`; CHECK `multa >= 0`; CHECK `data_prevista >= data_emprestimo` |

```
livros 1 ──── N emprestimos N ──── 1 membros
```

### Recursos programados no banco

Cada recurso tem uma finalidade diferente:

| Recurso | Finalidade | O que faz | Onde é usado |
|---|---|---|---|
| **VIEW** `vw_emprestimos_detalhados` | Consulta | Junta `emprestimos`, `livros` e `membros` e calcula a `situacao` (Devolvido / Em atraso / No prazo) e os `dias_atraso` | Telas **Empréstimos**, **Detalhe** e **Estante** |
| **FUNCTION** `fn_calcular_multa(p_id_emprestimo)` → `numeric` | Cálculo | Multa de R$ 2,00 por dia de atraso. Se já foi devolvido, conta até a data de devolução; se não, até hoje. Nunca é negativa | Tela **Detalhe** (`SELECT fn_calcular_multa(id)`) e dentro da procedure de devolução |
| **PROCEDURE** `sp_registrar_emprestimo(p_id_livro, p_id_membro, p_dias)` | Operação (escrita) | Valida livro, membro, estoque e limite de 3 empréstimos ativos; insere o empréstimo e baixa o estoque | Tela **Novo empréstimo** (`CALL`) |
| **PROCEDURE** `sp_registrar_devolucao(p_id_emprestimo)` | Operação (escrita) | Valida se o empréstimo existe e ainda não foi devolvido; grava a data de devolução e a multa (usando a function) e devolve o exemplar ao estoque | Botão **Devolver** nas telas Empréstimos e Detalhe (`CALL`) |

**Transações:** as procedures não fazem `COMMIT`. O Django chama cada uma dentro de `transaction.atomic()`; se a procedure der `RAISE EXCEPTION`, **tudo é desfeito** e a mensagem do banco aparece na tela, em português.

**Mensagens de erro das procedures:**

| Situação | Mensagem |
|---|---|
| Livro sem exemplar | O livro "…" não tem exemplares disponíveis no momento. |
| Membro no limite | O membro … já tem 3 empréstimos ativos (limite máximo). Devolva um livro antes. |
| Devolver duas vezes | O empréstimo … já foi devolvido em dd/mm/aaaa. |
| Prazo inválido | O prazo do empréstimo deve ser de pelo menos 1 dia. |

### Scripts (rodar nesta ordem)

| Ordem | Arquivo | O que cria |
|---|---|---|
| 1 | `database/tables/01_criar_tabelas.sql` | Tabelas, PKs, FKs, CHECKs e índices |
| 2 | `database/views/02_vw_emprestimos_detalhados.sql` | View |
| 3 | `database/functions/03_fn_calcular_multa.sql` | Function |
| 4 | `database/procedures/04_sp_registrar_emprestimo.sql` | Procedure de empréstimo |
| 5 | `database/procedures/05_sp_registrar_devolucao.sql` | Procedure de devolução |
| 6 | `database/inserts/06_dados_exemplo.sql` | Dados de exemplo (**apaga e recria** os dados) |

Todos podem ser executados mais de uma vez. O script 6 cria 10 livros, 5 membros e 5 empréstimos (2 devolvidos, 2 em atraso e 1 no prazo), com datas relativas ao dia de hoje para sempre existir atraso para mostrar.

## Telas

As telas que usam recursos do banco mostram um aviso azul no rodapé dizendo qual recurso está sendo usado.

| Tela | URL | Recurso do banco |
|---|---|---|
| Estante (início) | `/` | VIEW (resumo e lista de atrasados) |
| Livros | `/livros/` | tabela `livros` |
| Membros | `/membros/` | tabela `membros` |
| Novo empréstimo | `/emprestimos/novo/` | PROCEDURE `sp_registrar_emprestimo` |
| Empréstimos | `/emprestimos/` | VIEW + PROCEDURE `sp_registrar_devolucao` |
| Detalhe do empréstimo | `/emprestimos/<id>/` | FUNCTION `fn_calcular_multa` + VIEW |

**Estante:** cada lombada é um livro do banco. Um espaço tracejado indica que todos os exemplares daquele livro estão emprestados.

**Livros:** busca por título ou autor; as bolinhas mostram quantos exemplares estão na estante.

![Tela de livros](docs/img/02_livros.png)

**Membros:**

![Tela de membros](docs/img/03_membros.png)

**Novo empréstimo:** só lista livros com exemplar disponível; quem confere as regras é a procedure.

![Tela de novo empréstimo](docs/img/04_novo_emprestimo.png)

**Empréstimos:** lê a VIEW, filtra por situação e tem o botão Devolver em cada empréstimo ativo.

![Tela de empréstimos](docs/img/05_emprestimos.png)

**Detalhe:** ficha do empréstimo com a multa calculada na hora pela FUNCTION.

![Tela de detalhe do empréstimo](docs/img/06_detalhe.png)

## Como executar

### Pré-requisitos

- Python 3.11 ou mais novo
- PostgreSQL instalado e rodando (porta padrão 5432), com a senha do usuário `postgres` em mãos

### 1. Criar o banco e rodar os scripts

**Opção A — pelo terminal (psql)**, na raiz do projeto:

```powershell
$env:PGCLIENTENCODING="UTF8"
psql -U postgres -c "CREATE DATABASE biblioteca"
psql -U postgres -d biblioteca -f database/tables/01_criar_tabelas.sql
psql -U postgres -d biblioteca -f database/views/02_vw_emprestimos_detalhados.sql
psql -U postgres -d biblioteca -f database/functions/03_fn_calcular_multa.sql
psql -U postgres -d biblioteca -f database/procedures/04_sp_registrar_emprestimo.sql
psql -U postgres -d biblioteca -f database/procedures/05_sp_registrar_devolucao.sql
psql -U postgres -d biblioteca -f database/inserts/06_dados_exemplo.sql
```

**Opção B — pelo pgAdmin:** clique com o botão direito em *Databases* → *Create* → *Database...* e crie o banco `biblioteca`. Depois, nesse banco, abra o **Query Tool**, cole cada script **na ordem** (1 a 6) e execute com F5.

### 2. Configurar o `.env`

1. Na raiz do projeto, copie `.env.example` para `.env`.
2. Troque `SUA_SENHA` pela senha do usuário `postgres`:

   ```
   DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost:5432/biblioteca
   ```

3. Se a senha tiver caracteres especiais, codifique: `@` vira `%40`, `#` vira `%23`.

O arquivo `.env` está no `.gitignore` e não vai para o GitHub.

### 3. Instalar e rodar (Windows / PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

cd src
python testar_conexao.py      # confere se tabelas, view, function e procedures existem
python manage.py migrate      # cria só as tabelas internas do Django
python manage.py runserver
```

Acesse <http://127.0.0.1:8000>. No Linux/macOS, ative o venv com `source venv/bin/activate`.

> **Sobre o `migrate`:** ele cria apenas as tabelas internas do Django (`django_session`, `django_content_type`, `django_migrations`). As tabelas da biblioteca, a view, a function e as procedures são criadas **somente** pelos scripts SQL, porque os models têm `managed = False`.

Saída esperada do `testar_conexao.py`:

```
Conectado ao banco com sucesso!

[   OK   ] TABELA     livros  (10 registro(s))
[   OK   ] TABELA     membros  (5 registro(s))
[   OK   ] TABELA     emprestimos  (5 registro(s))
[   OK   ] VIEW       vw_emprestimos_detalhados  (5 registro(s))
[   OK   ] FUNCTION   fn_calcular_multa
[   OK   ] PROCEDURE  sp_registrar_emprestimo
[   OK   ] PROCEDURE  sp_registrar_devolucao

Tudo certo! Pode rodar: python manage.py runserver
```

## Como testar

Com os dados de exemplo recém-carregados:

| Teste | Como fazer | Resultado esperado |
|---|---|---|
| View | Empréstimos → filtro **Em atraso** | Empréstimos 3 e 4, com 10 e 8 dias de atraso |
| Function | Abrir a ficha do empréstimo 3 | Multa de R$ 20,00 |
| Empréstimo OK | Novo empréstimo para **Bruno Lima** | Aparece como "No prazo" e o estoque do livro baixa 1 |
| Limite de 3 | Novo empréstimo para **Ana Souza** | Mensagem de limite de 3 empréstimos ativos |
| Sem exemplar | Abrir Novo empréstimo em 2 abas com "Engenharia de Software" (1 exemplar) e confirmar nas duas | A segunda mostra que não há exemplares disponíveis |
| Devolução | Devolver o empréstimo 3 | Multa de R$ 20,00 gravada; "Grande Sertão" volta para a estante |
| Devolver 2 vezes | No pgAdmin/psql: `CALL sp_registrar_devolucao(3);` | Mensagem de que já foi devolvido |
| Exclusão protegida | Excluir "Dom Casmurro" | Bloqueado, pois o livro tem empréstimo registrado |

Para voltar os dados ao estado inicial, rode de novo o `06_dados_exemplo.sql`.

## Estrutura do repositório

```
biblioteca-bd/
├── database/                      scripts SQL (fonte da verdade do banco)
│   ├── tables/  views/  functions/  procedures/  inserts/
├── docs/
│   ├── roteiro_video.md           roteiro do vídeo de apresentação
│   └── img/                       prints das telas
├── src/
│   ├── manage.py
│   ├── testar_conexao.py          confere se tudo existe no banco
│   ├── config/                    settings e urls do Django
│   └── biblioteca/
│       ├── models.py              models com managed = False
│       ├── views.py               chama a VIEW, a FUNCTION e as PROCEDURES
│       ├── forms.py  urls.py  middleware.py
│       ├── templatetags/          filtros visuais (cores das lombadas, iniciais)
│       ├── templates/biblioteca/  telas e ilustrações SVG
│       └── static/biblioteca/     estilo.css
├── requirements.txt
├── .env.example
└── README.md
```

## Vídeo

- Roteiro: [`docs/roteiro_video.md`](docs/roteiro_video.md)
- Link do vídeo: [COLOCAR LINK DO VÍDEO]

-- =====================================================================
-- 01 - Criação das tabelas do sistema de biblioteca
-- Rodar no banco "biblioteca" (psql ou pgAdmin). Pode rodar mais de uma vez.
-- =====================================================================

-- Livros do acervo
CREATE TABLE IF NOT EXISTS livros (
    id                      SERIAL PRIMARY KEY,
    titulo                  VARCHAR(200) NOT NULL,
    autor                   VARCHAR(150) NOT NULL,
    isbn                    VARCHAR(20)  NOT NULL UNIQUE,
    exemplares_total        INTEGER      NOT NULL CHECK (exemplares_total >= 0),
    exemplares_disponiveis  INTEGER      NOT NULL,
    -- disponíveis nunca pode ser negativo nem passar do total
    CONSTRAINT ck_livros_disponiveis
        CHECK (exemplares_disponiveis BETWEEN 0 AND exemplares_total)
);

-- Membros (leitores) da biblioteca
CREATE TABLE IF NOT EXISTS membros (
    id         SERIAL PRIMARY KEY,
    nome       VARCHAR(150) NOT NULL,
    email      VARCHAR(150) NOT NULL UNIQUE,
    telefone   VARCHAR(20),
    criado_em  TIMESTAMP    NOT NULL DEFAULT now()
);

-- Empréstimos: liga um livro a um membro
CREATE TABLE IF NOT EXISTS emprestimos (
    id               SERIAL PRIMARY KEY,
    id_livro         INTEGER       NOT NULL REFERENCES livros (id),
    id_membro        INTEGER       NOT NULL REFERENCES membros (id),
    data_emprestimo  DATE          NOT NULL DEFAULT CURRENT_DATE,
    data_prevista    DATE          NOT NULL,
    data_devolucao   DATE,                       -- NULL = ainda não devolvido
    multa            NUMERIC(10,2) NOT NULL DEFAULT 0,
    CONSTRAINT ck_emprestimos_multa  CHECK (multa >= 0),
    CONSTRAINT ck_emprestimos_datas  CHECK (data_prevista >= data_emprestimo)
);

-- Índices nas chaves estrangeiras (deixam os JOINs da view mais rápidos)
CREATE INDEX IF NOT EXISTS idx_emprestimos_livro  ON emprestimos (id_livro);
CREATE INDEX IF NOT EXISTS idx_emprestimos_membro ON emprestimos (id_membro);

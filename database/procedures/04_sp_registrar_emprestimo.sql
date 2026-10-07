-- =====================================================================
-- 04 - PROCEDURE sp_registrar_emprestimo
-- Finalidade: OPERAÇÃO (escrita). Registra um empréstimo validando
-- as regras de negócio e baixando o estoque.
-- Roda dentro da transação de quem chamou (o Django usa
-- transaction.atomic). Se der RAISE EXCEPTION, tudo é desfeito.
-- Por isso NÃO tem COMMIT aqui dentro.
-- =====================================================================

CREATE OR REPLACE PROCEDURE sp_registrar_emprestimo(
    p_id_livro  INTEGER,
    p_id_membro INTEGER,
    p_dias      INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_titulo       VARCHAR(200);
    v_disponiveis  INTEGER;
    v_nome_membro  VARCHAR(150);
    v_ativos       INTEGER;
BEGIN
    -- 1) prazo válido
    IF p_dias IS NULL OR p_dias < 1 THEN
        RAISE EXCEPTION 'O prazo do empréstimo deve ser de pelo menos 1 dia.';
    END IF;

    -- 2) livro existe? (FOR UPDATE trava a linha para dois empréstimos
    --    simultâneos não pegarem o último exemplar ao mesmo tempo)
    SELECT titulo, exemplares_disponiveis
      INTO v_titulo, v_disponiveis
      FROM livros
     WHERE id = p_id_livro
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Livro com id % não encontrado.', p_id_livro;
    END IF;

    -- 3) membro existe?
    SELECT nome INTO v_nome_membro
      FROM membros
     WHERE id = p_id_membro;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Membro com id % não encontrado.', p_id_membro;
    END IF;

    -- 4) tem exemplar disponível?
    IF v_disponiveis <= 0 THEN
        RAISE EXCEPTION 'O livro "%" não tem exemplares disponíveis no momento.', v_titulo;
    END IF;

    -- 5) membro já está no limite de 3 empréstimos ativos?
    SELECT COUNT(*) INTO v_ativos
      FROM emprestimos
     WHERE id_membro = p_id_membro
       AND data_devolucao IS NULL;

    IF v_ativos >= 3 THEN
        RAISE EXCEPTION 'O membro % já tem 3 empréstimos ativos (limite máximo). Devolva um livro antes.', v_nome_membro;
    END IF;

    -- 6) registra o empréstimo
    INSERT INTO emprestimos (id_livro, id_membro, data_emprestimo, data_prevista)
    VALUES (p_id_livro, p_id_membro, CURRENT_DATE, CURRENT_DATE + p_dias);

    -- 7) baixa um exemplar do estoque
    UPDATE livros
       SET exemplares_disponiveis = exemplares_disponiveis - 1
     WHERE id = p_id_livro;
END;
$$;

-- Teste rápido:
-- CALL sp_registrar_emprestimo(1, 2, 7);

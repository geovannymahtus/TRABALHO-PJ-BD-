-- =====================================================================
-- 05 - PROCEDURE sp_registrar_devolucao
-- Finalidade: OPERAÇÃO (escrita). Registra a devolução, grava a multa
-- (usando a FUNCTION fn_calcular_multa) e devolve o exemplar ao estoque.
-- Sem COMMIT: a transação é controlada pelo Django (transaction.atomic).
-- =====================================================================

CREATE OR REPLACE PROCEDURE sp_registrar_devolucao(p_id_emprestimo INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_livro       INTEGER;
    v_data_devolucao DATE;
BEGIN
    -- 1) empréstimo existe? (FOR UPDATE evita devolver duas vezes ao mesmo tempo)
    SELECT id_livro, data_devolucao
      INTO v_id_livro, v_data_devolucao
      FROM emprestimos
     WHERE id = p_id_emprestimo
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Empréstimo % não encontrado.', p_id_emprestimo;
    END IF;

    -- 2) já foi devolvido?
    IF v_data_devolucao IS NOT NULL THEN
        RAISE EXCEPTION 'O empréstimo % já foi devolvido em %.',
            p_id_emprestimo, to_char(v_data_devolucao, 'DD/MM/YYYY');
    END IF;

    -- 3) marca a devolução com a data de hoje
    UPDATE emprestimos
       SET data_devolucao = CURRENT_DATE
     WHERE id = p_id_emprestimo;

    -- 4) grava a multa usando a FUNCTION (ela já enxerga a data_devolucao acima)
    UPDATE emprestimos
       SET multa = fn_calcular_multa(p_id_emprestimo)
     WHERE id = p_id_emprestimo;

    -- 5) devolve o exemplar ao estoque
    UPDATE livros
       SET exemplares_disponiveis = exemplares_disponiveis + 1
     WHERE id = v_id_livro;
END;
$$;

-- Teste rápido:
-- CALL sp_registrar_devolucao(3);

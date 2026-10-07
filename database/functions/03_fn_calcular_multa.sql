-- =====================================================================
-- 03 - FUNCTION fn_calcular_multa
-- Finalidade: CÁLCULO. Recebe o id do empréstimo e devolve a multa
-- (R$ 2,00 por dia de atraso). Não altera nada no banco.
--   - Já devolvido: conta o atraso até a data_devolucao
--   - Ainda aberto: conta o atraso até hoje (CURRENT_DATE)
--   - Nunca retorna valor negativo
-- =====================================================================

CREATE OR REPLACE FUNCTION fn_calcular_multa(p_id_emprestimo INTEGER)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE   -- só lê dados, não modifica
AS $$
DECLARE
    c_valor_por_dia CONSTANT NUMERIC := 2.00;
    v_data_prevista  DATE;
    v_data_devolucao DATE;
    v_data_referencia DATE;
    v_dias_atraso    INTEGER;
BEGIN
    SELECT data_prevista, data_devolucao
      INTO v_data_prevista, v_data_devolucao
      FROM emprestimos
     WHERE id = p_id_emprestimo;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Empréstimo % não encontrado.', p_id_emprestimo;
    END IF;

    -- se já devolveu usa a data da devolução, senão usa hoje
    v_data_referencia := COALESCE(v_data_devolucao, CURRENT_DATE);

    -- GREATEST garante que nunca fica negativo
    v_dias_atraso := GREATEST(v_data_referencia - v_data_prevista, 0);

    RETURN ROUND(v_dias_atraso * c_valor_por_dia, 2);
END;
$$;

-- Teste rápido:
-- SELECT id, fn_calcular_multa(id) FROM emprestimos;

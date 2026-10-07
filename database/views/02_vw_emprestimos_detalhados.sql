-- =====================================================================
-- 02 - VIEW vw_emprestimos_detalhados
-- Finalidade: CONSULTA. Junta emprestimos + livros + membros e já
-- calcula a situação e os dias de atraso, para a tela "Empréstimos"
-- não precisar repetir JOIN e regra de negócio no Python.
-- =====================================================================

-- DROP + CREATE para poder rodar de novo mesmo se as colunas mudarem
DROP VIEW IF EXISTS vw_emprestimos_detalhados;

CREATE VIEW vw_emprestimos_detalhados AS
SELECT
    e.id               AS id_emprestimo,
    l.titulo,
    m.nome             AS nome_membro,
    e.data_emprestimo,
    e.data_prevista,
    e.data_devolucao,
    -- situação do empréstimo
    CASE
        WHEN e.data_devolucao IS NOT NULL   THEN 'Devolvido'
        WHEN CURRENT_DATE > e.data_prevista THEN 'Em atraso'
        ELSE 'No prazo'
    END AS situacao,
    -- dias de atraso (0 se devolvido ou dentro do prazo)
    CASE
        WHEN e.data_devolucao IS NULL AND CURRENT_DATE > e.data_prevista
            THEN CURRENT_DATE - e.data_prevista
        ELSE 0
    END AS dias_atraso
FROM emprestimos e
JOIN livros  l ON l.id = e.id_livro
JOIN membros m ON m.id = e.id_membro;

-- Teste rápido:
-- SELECT * FROM vw_emprestimos_detalhados WHERE situacao = 'Em atraso';

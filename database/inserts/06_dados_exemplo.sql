-- =====================================================================
-- 06 - Dados de exemplo
-- ATENÇÃO: este script LIMPA as três tabelas e recria os dados.
-- Pode rodar quantas vezes quiser (ótimo para "resetar" antes do vídeo).
-- RESTART IDENTITY faz os ids voltarem a começar do 1.
-- =====================================================================

TRUNCATE TABLE emprestimos, membros, livros RESTART IDENTITY CASCADE;

-- 10 livros (exemplares_disponiveis já descontando os empréstimos ativos abaixo)
INSERT INTO livros (titulo, autor, isbn, exemplares_total, exemplares_disponiveis) VALUES
('Dom Casmurro',                     'Machado de Assis',           '9788535910663', 3, 3),  -- id 1
('O Cortiço',                        'Aluísio Azevedo',            '9788508133029', 2, 2),  -- id 2
('Vidas Secas',                      'Graciliano Ramos',           '9788501046401', 2, 2),  -- id 3
('Grande Sertão: Veredas',           'João Guimarães Rosa',        '9788535908466', 1, 0),  -- id 4 (único exemplar emprestado)
('Memórias Póstumas de Brás Cubas',  'Machado de Assis',           '9788572326972', 2, 2),  -- id 5
('A Hora da Estrela',                'Clarice Lispector',          '9788532508126', 2, 2),  -- id 6
('Capitães da Areia',                'Jorge Amado',                '9788535914061', 3, 2),  -- id 7 (1 emprestado)
('Código Limpo',                     'Robert C. Martin',           '9788576082675', 2, 2),  -- id 8
('Sistemas de Banco de Dados',       'Ramez Elmasri e Shamkant Navathe', '9788579360855', 2, 1),  -- id 9 (1 emprestado)
('Engenharia de Software',           'Ian Sommerville',            '9788543024974', 1, 1);  -- id 10

-- 5 membros
INSERT INTO membros (nome, email, telefone) VALUES
('Ana Souza',    'ana.souza@email.com',    '(11) 91234-5678'),  -- id 1
('Bruno Lima',   'bruno.lima@email.com',   '(21) 99876-5432'),  -- id 2
('Carla Mendes', 'carla.mendes@email.com', '(31) 98765-1234'),  -- id 3
('Diego Santos', 'diego.santos@email.com', '(41) 97654-3210'),  -- id 4
('Elisa Rocha',  'elisa.rocha@email.com',  '(51) 96543-2109');  -- id 5

-- 5 empréstimos com datas relativas a hoje (assim sempre tem atraso, em qualquer dia)
INSERT INTO emprestimos (id_livro, id_membro, data_emprestimo, data_prevista, data_devolucao, multa) VALUES
-- 1) Devolvido dentro do prazo -> multa 0
(1, 2, CURRENT_DATE - 30, CURRENT_DATE - 23, CURRENT_DATE - 25, 0.00),
-- 2) Devolvido com 3 dias de atraso -> multa R$ 6,00
(2, 3, CURRENT_DATE - 25, CURRENT_DATE - 18, CURRENT_DATE - 15, 6.00),
-- 3) Ativo e EM ATRASO há 10 dias (Grande Sertão, único exemplar)
(4, 1, CURRENT_DATE - 20, CURRENT_DATE - 10, NULL, 0.00),
-- 4) Ativo e EM ATRASO há 8 dias
(9, 1, CURRENT_DATE - 15, CURRENT_DATE - 8,  NULL, 0.00),
-- 5) Ativo e NO PRAZO (vence daqui a 5 dias)
(7, 1, CURRENT_DATE - 2,  CURRENT_DATE + 5,  NULL, 0.00);

-- Obs.: a Ana (id 1) ficou com 3 empréstimos ativos -> serve para testar o limite.
-- Obs.: "Grande Sertão: Veredas" (id 4) ficou com 0 disponíveis -> serve para testar falta de estoque.

-- Conferência:
-- SELECT * FROM vw_emprestimos_detalhados ORDER BY id_emprestimo;

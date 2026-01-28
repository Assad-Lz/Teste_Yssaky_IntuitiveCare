-- Project: Intuitive Care Technical Assessment
-- Module: Database Schema & Analytical Queries
-- Author: Yssaky Assad Luz
-- Database Dialect: Standard SQL (Compatible with MySQL 8.0 / PostgreSQL)

-- ============================================================================
-- 1. DDL (Data Definition Language) - Table Structure
-- ============================================================================

-- Trade-off Decision: Normalization (Option B)
-- Justification: We chosen a Normalized approach separating 'operadoras' (registry) 
-- from 'despesas' (transactions). This reduces data redundancy (storing address/name 
-- only once) and ensures better integrity. Given the quarterly update frequency, 
-- this structure is efficient for both writing and reading.

CREATE TABLE IF NOT EXISTS operadoras (
    registro_ans INT PRIMARY KEY,
    cnpj VARCHAR(14) UNIQUE,
    razao_social VARCHAR(255),
    modalidade VARCHAR(100),
    uf CHAR(2)
);

-- Trade-off Decision: Data Types
-- Justification: Used DECIMAL(15,2) for monetary values instead of FLOAT to ensure 
-- accounting precision and avoid floating-point rounding errors.

CREATE TABLE IF NOT EXISTS despesas (
    id SERIAL PRIMARY KEY, -- Use AUTO_INCREMENT if using MySQL
    registro_ans INT,
    data_evento DATE,
    trimestre VARCHAR(10),
    ano INT,
    valor DECIMAL(15,2),
    descricao TEXT,
    FOREIGN KEY (registro_ans) REFERENCES operadoras(registro_ans)
);

-- Performance Indexes
CREATE INDEX idx_despesas_ano_trimestre ON despesas(ano, trimestre);
CREATE INDEX idx_operadoras_uf ON operadoras(uf);

-- ============================================================================
-- 2. Data Import (Conceptual)
-- ============================================================================
-- The ETL pipeline (Python) is responsible for generating the CSVs.
-- In a production DB environment, we would run:
-- COPY operadoras FROM '/data/Relatorio_cadop.csv' DELIMITER ';' CSV HEADER;
-- COPY despesas FROM '/data/consolidado_despesas.csv' DELIMITER ';' CSV HEADER;

-- ============================================================================
-- 3. Analytical Queries (DML)
-- ============================================================================

-- QUERY 1: Top 5 Operators with highest Expense Growth (First vs Last Quarter)
-- Challenge: Operators might miss data in some quarters. 
-- Solution: We explicitly find the Min and Max date for each operator to compare range.

WITH quarterly_expenses AS (
    SELECT 
        d.registro_ans,
        d.ano,
        d.trimestre,
        SUM(d.valor) as total_trimestre,
        -- Create a sortable period string (e.g., "2023-1") for comparison
        CONCAT(d.ano, '-', RIGHT(d.trimestre, 1)) as periodo_sort
    FROM despesas d
    GROUP BY 1, 2, 3, 5
),
boundaries AS (
    SELECT 
        registro_ans,
        MIN(periodo_sort) as start_period,
        MAX(periodo_sort) as end_period
    FROM quarterly_expenses
    GROUP BY registro_ans
)
SELECT 
    o.razao_social,
    q_start.total_trimestre as valor_inicial,
    q_end.total_trimestre as valor_final,
    -- Growth Formula: (Final - Initial) / Initial
    ROUND(((q_end.total_trimestre - q_start.total_trimestre) / q_start.total_trimestre) * 100, 2) as crescimento_pct
FROM boundaries b
JOIN quarterly_expenses q_start 
    ON b.registro_ans = q_start.registro_ans AND b.start_period = q_start.periodo_sort
JOIN quarterly_expenses q_end 
    ON b.registro_ans = q_end.registro_ans AND b.end_period = q_end.periodo_sort
JOIN operadoras o 
    ON b.registro_ans = o.registro_ans
WHERE q_start.total_trimestre > 0 -- Avoid division by zero
ORDER BY 4 DESC -- Order by percentage growth
LIMIT 5;


-- QUERY 2: Expense Distribution by State (UF)
-- Challenge: Calculate average per operator within the UF as well.

SELECT 
    o.uf,
    SUM(d.valor) as despesas_totais,
    COUNT(DISTINCT o.registro_ans) as qtd_operadoras,
    ROUND(AVG(sum_per_op.total_op), 2) as media_por_operadora
FROM operadoras o
JOIN despesas d ON o.registro_ans = d.registro_ans
JOIN (
    -- Subquery to pre-calculate total per operator for the average metric
    SELECT registro_ans, SUM(valor) as total_op 
    FROM despesas 
    GROUP BY registro_ans
) sum_per_op ON o.registro_ans = sum_per_op.registro_ans
GROUP BY o.uf
ORDER BY despesas_totais DESC
LIMIT 5;


-- QUERY 3: Operators with expenses above average in at least 2 quarters
-- Trade-off: Using "HAVING" clause for better readability compared to complex self-joins.

WITH media_geral_trimestral AS (
    -- 1. Calculate the global average expense for each quarter across ALL operators
    SELECT 
        trimestre, 
        ano, 
        AVG(total_trimestre) as media_mercado
    FROM (
        SELECT registro_ans, trimestre, ano, SUM(valor) as total_trimestre
        FROM despesas
        GROUP BY 1, 2, 3
    ) sub
    GROUP BY 1, 2
),
operadora_trimestral AS (
    -- 2. Calculate each individual operator's total per quarter
    SELECT 
        registro_ans, 
        trimestre, 
        ano, 
        SUM(valor) as total_op
    FROM despesas
    GROUP BY 1, 2, 3
)
SELECT 
    o.razao_social,
    COUNT(*) as qtd_trimestres_acima_media
FROM operadora_trimestral ot
JOIN media_geral_trimestral mgt 
    ON ot.trimestre = mgt.trimestre AND ot.ano = mgt.ano
JOIN operadoras o 
    ON ot.registro_ans = o.registro_ans
WHERE ot.total_op > mgt.media_mercado
GROUP BY o.razao_social
HAVING COUNT(*) >= 2; -- "At least 2 of the 3 quarters"
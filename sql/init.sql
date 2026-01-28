-- Clean slate: Drop tables if they exist to avoid conflicts during restart
DROP TABLE IF EXISTS despesas CASCADE;
DROP TABLE IF EXISTS operadoras CASCADE;

-- 1. Operators Table (Parent Table)
-- Stores registration data (Dimension)
CREATE TABLE operadoras (
    registro_ans VARCHAR(20) PRIMARY KEY,
    cnpj VARCHAR(20),
    razao_social TEXT,
    modalidade VARCHAR(100),
    uf VARCHAR(2)
);

-- 2. Expenses Table (Child Table)
-- Stores financial events (Facts). Linked to Operators via Foreign Key.
CREATE TABLE despesas (
    id SERIAL PRIMARY KEY,
    registro_ans VARCHAR(20) REFERENCES operadoras(registro_ans),
    valor_despesa DECIMAL(15,2), -- DECIMAL used for financial precision
    trimestre VARCHAR(10),
    ano VARCHAR(4),
    descricao TEXT
);

-- Indexes to optimize API search and filtering performance
CREATE INDEX idx_op_razao ON operadoras(razao_social);
CREATE INDEX idx_op_cnpj ON operadoras(cnpj);
CREATE INDEX idx_desp_reg ON despesas(registro_ans);
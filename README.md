# Intuitive Care - Teste Técnico (Fullstack Data Engineer)

Este repositório contém a solução completa para o desafio técnico da Intuitive Care. O projeto consiste em um Pipeline de Dados (ETL) automatizado que alimenta uma API RESTful e um Dashboard interativo, tudo encapsulado em containers Docker para fácil reprodução.

## 🚀 Funcionalidades

### 1. Engenharia de Dados (ETL)

- **Extração:** Scripts automáticos (`etl/main.py`) que baixam arquivos do FTP da ANS (Cadastros e Demonstrações Contábeis).
- **Transformação:** Limpeza de dados robusta e padronização de encodings. O script converte arquivos legados (Latin-1) para **UTF-8**, corrigindo problemas de acentuação (ex: "PARTICIPAÇÃO").
- **Enriquecimento:** Cruzamento (Join) de dados financeiros com dados cadastrais usando `RegistroANS` como chave primária.

### 2. Backend (API)

- Desenvolvido em **FastAPI** (Python 3.10).
- Estratégia **In-Memory Data**: Carregamento otimizado dos CSVs processados com Pandas para garantir respostas em milissegundos.
- **Testes Automatizados:** Cobertura de testes unitários (`pytest`) garantindo a integridade dos endpoints.
- Documentação interativa automática via Swagger UI.

### 3. Frontend (Dashboard)

- Aplicação **Vue.js 3** construída com **Vite**.
- **Visualização:** Gráfico de barras (Chart.js) exibindo o Top 5 Despesas por UF.
- **Busca & Filtro:** Pesquisa textual reativa por Operadora ou CNPJ com paginação controlada pelo servidor.
- Design limpo, responsivo e com tratamento correto de caracteres especiais.

### 4. DevOps & Infraestrutura

- **Docker:** Ambientes isolados (Containerização) para Backend (Python 3.10) e Frontend (Node.js 22+).
- **Docker Compose:** Orquestração completa do ambiente com um único comando.

---

## 🛠️ Tecnologias

- **Linguagem:** Python 3.10, JavaScript
- **Frameworks:** FastAPI, Vue.js 3
- **Dados:** Pandas, NumPy
- **Infraestrutura:** Docker, Docker Compose
- **Testes:** Pytest, HTTPX

---

## 🐳 Como Rodar (Via Docker - Recomendado)

A maneira mais simples e robusta de executar o projeto.

1. **Clone o repositório:**

```bash
git clone https://github.com/Assad-Lz/Teste_Yssaky_IntuitiveCare.git
cd Teste_Yssaky_IntuitiveCare
```

2. **Execute o Ambiente:**

```bash
docker compose up --build
```

3. **Acesse a aplicação:**

- **Dashboard (Frontend):** http://localhost:5173
- **Documentação da API:** http://localhost:8000/docs

---

## ⚙️ Como Rodar (Manual / Sem Docker)

Caso prefira executar localmente em sua máquina:

### Backend & ETL

```bash
# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt

# Execute o ETL (Necessário na primeira execução)
python etl/main.py        # Download
python etl/processing.py  # Processamento (Correção UTF-8)
python etl/enrichment.py  # Enriquecimento

# Inicie a API
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Executando Testes

O projeto conta com testes unitários para validar a lógica da API.

```bash
# Na raiz do projeto (com venv ativado)
python -m pytest
```

---

## ⚖️ Trade-offs e Decisões de Arquitetura

### CSV em Memória vs Banco de Dados SQL

**Decisão:** Servir os dados via Pandas (In-Memory).

**Justificativa:** O dataset consolidado é leve o suficiente para caber na RAM. Isso elimina a latência de I/O de disco e a complexidade de configurar um servidor SQL externo, atendendo ao princípio KISS (Keep It Simple, Stupid) solicitado no teste.

**Nota Importante:** Mesmo utilizando CSV em memória na API, os scripts SQL solicitados estão **totalmente disponíveis** na pasta [sql/](sql/) do projeto. O arquivo [sql/queries.sql](sql/queries.sql) contém:

- **DDL Statements:** CREATE TABLE com estrutura normalizada para `operadoras` e `despesas`
- **Performance Indexes:** Índices estratégicos para otimizar consultas
- **3 Analytical Queries:** Implementações SQL completas das análises de negócio (crescimento de despesas, distribuição por UF, operadoras acima da média)

Isso permite que a solução seja facilmente migrada para um banco de dados SQL quando necessário, sem qualquer modificação nas queries.

### Tratamento de Encoding Robusto (ETL)

**Decisão:** Implementar uma lógica de leitura híbrida no ETL.

**Justificativa:** Arquivos da ANS historicamente variam entre Latin-1 e UTF-8. O script tenta ler como UTF-8 primeiro; se falhar, faz fallback para Latin-1 e salva o arquivo final sempre em UTF-8 puro. Isso garante que o Backend e Frontend nunca sofram com caracteres corrompidos ("Mojibake").

### Frontend: Renderização Condicional vs Router

**Decisão:** Utilizar `v-if` para alternar entre a Lista e os Detalhes.

**Justificativa:** Para uma aplicação de escopo fechado (2 telas), configurar um Vue Router completo adicionaria complexidade desnecessária ao código.

---

**Autor:** Yssaky Assad

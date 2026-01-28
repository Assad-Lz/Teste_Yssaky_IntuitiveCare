# Intuitive Care - Teste Técnico (Fullstack Data Engineer)

Este repositório contém a solução completa para o desafio técnico da Intuitive Care. O projeto evoluiu para uma arquitetura robusta baseada em **Banco de Dados SQL**, consistindo em um Pipeline de Dados (ETL) que alimenta um PostgreSQL, uma API RESTful performática e um Dashboard interativo, tudo orquestrado via Docker.

## 🚀 Funcionalidades

### 1. Engenharia de Dados (ETL)

- **Extração & Carga:** Pipeline otimizado (`etl/pipeline_sql.py`) que processa arquivos CSV brutos e os persiste em um banco PostgreSQL.
- **Tratamento de Dados:** Detecção e correção automática de encodings (UTF-8 vs Latin-1) e limpeza de identificadores (remoção de sufixos `.0` e espaços).
- **Performance:** Implementação de **Batch Processing** (inserção em lotes de 50.000 registros), permitindo o processamento de milhões de linhas sem estourar a memória RAM.

### 2. Backend (API)

- Desenvolvido em **FastAPI** (Python 3.10) com **SQLAlchemy**.
- **Arquitetura SQL:** Consultas otimizadas diretamente no banco de dados, utilizando `LIMIT/OFFSET` para paginação real e agregações (`SUM`, `GROUP BY`) via query.
- **Testes Unitários:** Implementação de testes com **Mocks** (`unittest.mock`), garantindo que a lógica da API seja validada isoladamente, sem depender do estado do banco de dados.
- Documentação interativa automática via Swagger UI.

### 3. Frontend (Dashboard)

- Aplicação **Vue.js 3** construída com **Vite**.
- **Integração Real:** Consumo de dados persistidos no PostgreSQL.
- **Visualização:** Gráfico de barras (Chart.js) exibindo o Top 5 Despesas por UF (query analítica).
- **Busca & Detalhes:** Pesquisa textual por Razão Social e visualização detalhada de despesas históricas da operadora.

### 4. DevOps & Infraestrutura

- **Docker:** Ambientes isolados para Backend, Frontend e **Banco de Dados**.
- **PostgreSQL:** Container dedicado para persistência dos dados.
- **Docker Compose:** Orquestração completa (App + DB) com reinício automático e redes internas configuradas.

---

## 🛠️ Tecnologias

- **Linguagem:** Python 3.10, JavaScript
- **Frameworks:** FastAPI, Vue.js 3
- **Banco de Dados:** PostgreSQL 15
- **ORM:** SQLAlchemy
- **Infraestrutura:** Docker, Docker Compose
- **Testes:** Pytest (com Mocks), HTTPX

---

## 🐳 Como Rodar (Via Docker - Recomendado)

A maneira mais simples e robusta de executar o projeto.

1. **Clone o repositório:**

```bash
git clone [https://github.com/Assad-Lz/Teste_Yssaky_IntuitiveCare.git](https://github.com/Assad-Lz/Teste_Yssaky_IntuitiveCare.git)
cd Teste_Yssaky_IntuitiveCare


Suba o Ambiente:

Bash
docker compose up --build -d
Aguarde cerca de 15 segundos para o Banco de Dados inicializar.

Popule o Banco de Dados (ETL): Como o banco inicia vazio, execute o script de carga para processar os CSVs e inseri-los no PostgreSQL:

Bash
docker compose exec backend python etl/pipeline_sql.py
Você verá uma barra de progresso indicando a inserção dos lotes.

Acesse a aplicação:

Painel de controle (interface do usuário): http://localhost:5173

Documentação da API: http: // localhost: 8000 / docs

⚙️ Como rolar (Híbrido / Depuração)
Caso queira rodar os scripts localmente mantendo apenas o banco no Docker:

Backend e ETL
Bash
# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt

# Garanta que o banco está rodando no Docker
docker compose up -d db

# Execute o ETL
python etl/pipeline_sql.py

# Inicie a API
uvicorn backend.main:app --reload
Front-end
Bash
cd frontend
npm install
npm run dev
🧪 Executando Testes
O projeto utiliza Mocks para testar a API sem necessidade de conexão real com o banco de dados.

Bash
# Rodando via Docker (Recomendado)
docker compose exec backend pytest

# Ou localmente (com venv ativado)
pytest
⚖️ Trade-offs e Decisões de Arquitetura
Migração de "CSV em Memória" para SQL (PostgreSQL)
Decisão: Migrar a persistência de dados para um banco relacional.

Justificativa: Embora a solução em memória fosse rápida para testes pequenos, ela não é escalável para o volume real de dados da saúde suplementar. O uso do PostgreSQL garante:

Integridade Referencial: As despesas só são inseridas se a operadora existir.

Eficiência de Memória: O Python não precisa carregar 2GB de dados na RAM; ele busca apenas a página solicitada (10 itens).

Capacidade Analítica: Consultas complexas (como Agrupamento por UF) são delegadas ao motor do banco de dados, que é otimizado para isso.

Estratégia de Testes com Mocks
Decisão: Usar unittest.mockpara simular a conexão com o banco nos testes.

Justificativa: Testes de integração que dependem de um banco real são lentos e frágeis (quebram se o banco estiver vazio ou sujo). Ao usar Mocks, garantimos que a lógica da API (rotas, filtros, formato do JSON) esteja correta em milissegundos, independentemente do estado do Docker.

ETL com Processamento em Lote
Decisão: Inserção no banco em "chunks" (lotes) de 50.000 registros.

Justificativa: Tentar inserir milhões de linhas de uma vez (Bulk Insert total) frequentemente causa timeouts ou estouro de memória. A abordagem em lotes oferece um equilíbrio ideal entre performance de escrita e estabilidade do sistema, além de fornecer feedback visual de progresso.

Autor: Yssaky Assad
```

# Intuitive Care - Teste Técnico (Fullstack Data Engineer)

Este repositório contém a solução completa para o desafio técnico da Intuitive Care. O projeto evoluiu para uma arquitetura robusta baseada em banco de dados relacional (PostgreSQL), consistindo em um pipeline de ETL, uma API backend e um frontend de visualização.

## 🚀 Funcionalidades

### 1. Engenharia de Dados (ETL)

- **Extração & Carga:** Pipeline otimizado (`etl/pipeline_sql.py`) que processa arquivos CSV brutos e os persiste em um banco PostgreSQL.
- **Tratamento de Dados:** Detecção e correção automática de encodings (UTF-8 vs Latin-1) e limpeza de identificadores (remoção de sufixos `.0` e espaços).
- **Performance:** Implementação de _batch processing_ (inserção em lotes de 50.000 registros), permitindo o processamento de milhões de linhas sem estourar a memória RAM.

### 2. Backend (API)

- Desenvolvido em **FastAPI** (Python 3.10) com **SQLAlchemy**.
- **Arquitetura SQL:** Consultas otimizadas diretamente no banco de dados, utilizando `LIMIT/OFFSET` para paginação e agregações (`SUM`, `GROUP BY`) via query.
- **Testes Unitários:** Implementação de testes com **unittest.mock**, garantindo que a lógica da API seja validada isoladamente, sem depender do estado do banco de dados.
- Documentação interativa automática via Swagger UI.

### 3. Frontend (Dashboard)

- Aplicação **Vue.js 3** construída com **Vite**.
- **Integração Real:** Consumo de dados persistidos no PostgreSQL.
- **Visualização:** Gráfico de barras (Chart.js) exibindo o Top 5 de despesas por UF (query analítica).
- **Busca & Detalhes:** Pesquisa textual por Razão Social e visualização detalhada de despesas históricas por operadora.

### 4. DevOps & Infraestrutura

- **Docker:** Ambientes isolados para Backend, Frontend e Banco de Dados.
- **PostgreSQL:** Container dedicado para persistência dos dados.
- **Docker Compose:** Orquestração completa (app + db) com reinício automático e redes internas configuradas.

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

A maneira mais simples e robusta de executar o projeto é via Docker Compose.

> 📁 Clone (comando)
>
> ```bash
> git clone https://github.com/Assad-Lz/Teste_Yssaky_IntuitiveCare.git
> cd Teste_Yssaky_IntuitiveCare
> ```

> 🐳 Subir ambiente (comando)
>
> ```bash
> docker compose up --build -d
> ```
>
> Aguarde cerca de 15 segundos para o banco de dados inicializar.

> 🔁 Popular o banco (ETL) (comando)
>
> ```bash
> docker compose exec backend python etl/pipeline_sql.py
> ```
>
> Você verá uma barra de progresso indicando a inserção dos lotes.

4. Acesse a aplicação:

- Painel de controle (frontend): http://localhost:5173
- Documentação da API (Swagger): http://localhost:8000/docs

---

## ⚙️ Como Rodar em Híbrido / Para Depuração

Caso queira rodar os scripts localmente mantendo apenas o banco no Docker:

> 🐍 Backend & ETL — setup (comandos)
>
> ```bash
> # Crie e ative o ambiente virtual
> python -m venv venv
> source venv/bin/activate  # Linux/Mac
> # venv\Scripts\activate   # Windows
>
> # Instale as dependências
> pip install -r requirements.txt
>
> # Garanta que o banco está rodando no Docker
> docker compose up -d db
>
> # Execute o ETL
> python etl/pipeline_sql.py
>
> # Inicie a API (no modo de desenvolvimento)
> uvicorn backend.main:app --reload
> ```

> ⚛️ Frontend — desenvolvimento (comandos)
>
> ```bash
> cd frontend
> npm install
> npm run dev
> ```

---

## 🧪 Executando Testes

O projeto utiliza mocks para testar a API sem necessidade de conexão real com o banco de dados.

> ✅ Testes via Docker (recomendado)
>
> ```bash
> docker compose exec backend pytest
> ```

> ✅ Testes localmente (com `venv` ativado)
>
> ```bash
> pytest
> ```

---

## ⚖️ Trade-offs e Decisões de Arquitetura

- Migração de "CSV em memória" para SQL (PostgreSQL)  
  Decisão: migrar a persistência de dados para um banco relacional.

  Justificativa:
  - Integridade referencial: as despesas só são inseridas se a operadora existir.
  - Eficiência de memória: o Python não precisa carregar grandes volumes de dados na RAM; o DB retorna apenas a página solicitada.
  - Capacidade analítica: consultas complexas (como agrupamento por UF) são delegadas ao motor do banco de dados, que é otimizado para isso.

- Estratégia de testes com Mocks  
  Decisão: usar `unittest.mock` para simular a conexão com o banco nos testes.

  Justificativa: testes de integração que dependem de um banco real são mais lentos e frágeis. Com mocks garantimos que a lógica da API (rotas, validações e transformações) seja validada isoladamente.

- ETL com processamento em lote  
  Decisão: inserção no banco em "chunks" (lotes) de 50.000 registros.

  Justificativa: inserir milhões de linhas de uma vez pode causar timeouts ou estouro de memória. A abordagem em lotes é um equilíbrio entre desempenho e estabilidade.

---

## Autor

Yssaky Assad

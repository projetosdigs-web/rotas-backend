# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.


🚚 Sistema de Rotas e Logística

Sistema web para gerenciamento de rotas de entrega, permitindo o cadastro de cidades, bairros, veículos e a visualização geográfica das operações por dia da semana.

🛠 Tecnologias Utilizadas

Backend (API)

Linguagem: Python 3.10+

Framework: FastAPI

Banco de Dados: SQLite (via SQLAlchemy)

Autenticação: JWT (JSON Web Tokens)

Segurança: Passlib + Bcrypt (Hash de senhas)

Servidor: Uvicorn

Frontend (Interface)

Framework: React (Vite)

Estilização: Tailwind CSS

Mapas: Leaflet (React-Leaflet) + OpenStreetMap

HTTP Client: Fetch API nativa

🚀 Guia de Instalação

1. Configurando o Backend (Python)

Abra o terminal na pasta raiz do projeto (onde está o arquivo app.py).

Instale as dependências:
Recomenda-se o uso da versão 4.0.1 do bcrypt para evitar conflitos com o passlib.

pip install fastapi uvicorn sqlalchemy httpx "python-jose[cryptography]" "passlib[bcrypt]" "bcrypt==4.0.1"


Inicie o Servidor:

uvicorn app:app --reload


O servidor rodará em: http://127.0.0.1:8000

2. Configurando o Frontend (React)

Abra um novo terminal na pasta do frontend (onde está o arquivo package.json).

Instale as dependências:

npm install


Inicie a Aplicação:

npm run dev


Acesse pelo navegador no link indicado (geralmente http://localhost:5173)

🔑 Acesso ao Sistema

Ao iniciar o sistema pela primeira vez, um usuário administrador é criado automaticamente.

Usuário: admin

Senha: 123456

⚙️ Configurações Importantes (Troubleshooting)

Se tiver problemas de conexão ou erro "Network Error", verifique as configurações abaixo.

1. Endereço da API (Frontend)

No arquivo App.jsx, certifique-se de que o API_BASE aponta para o IP numérico local para evitar conflitos de DNS no Windows:

// App.jsx
const API_BASE = "[http://127.0.0.1:8000](http://127.0.0.1:8000)";


2. Configuração de CORS (Backend)

No arquivo app.py, a lista de origens permitidas (origins) deve conter todas as portas que o Vite pode usar:

# app.py
origins = [
    "http://localhost:5173",
    "http://localhost:5174", # Caso a porta principal esteja ocupada
    "[http://127.0.0.1:5173](http://127.0.0.1:5173)",
    # ... outros endereços locais
]


📚 Funcionalidades

Painel Administrativo

O acesso é restrito (requer login).

Rotas: Criação de identificadores de rota (ex: Rota Norte, Rota Z1).

Cidades: Cadastro com Latitude/Longitude (busca automática via Nominatim).

Bairros: Subdivisões das cidades.

Veículos: Cadastro da frota (Nome e Placa).

Vínculos (Core): Associação entre Rota + Cidade + Bairro + Dia da Semana + Veículo.

Painel de Consulta (Público)

Busca por Local: Digite o nome de uma cidade ou bairro para ver quais rotas passam lá.

Busca por Dia: Selecione um dia (ex: Segunda-feira) para ver no mapa toda a operação logística daquele dia.

🗺️ API Reference (Endpoints Principais)

Método

Endpoint

Descrição

POST

/auth/login

Realiza login e retorna Token Bearer

GET

/routes/

Lista todas as rotas

POST

/routes/

Cria uma nova rota (Autenticado)

GET

/geocode/?query=...

Busca Lat/Long de um endereço externo

GET

/lookup-city/?query=...

Busca rotas por nome de cidade/bairro

GET

/lookup-day/?weekday=...

Busca rotas por dia da semana (0=Seg, 6=Dom)

📝 Notas de Desenvolvimento

Banco de Dados: O sistema usa SQLite (sql_app.db). Se precisar "resetar" o sistema, basta apagar esse arquivo e reiniciar o backend.

Mapas: O sistema utiliza OpenStreetMap, que é gratuito e não requer chave de API.
@echo off
title INICIADOR DO SISTEMA DE ROTAS
color 0A

echo ======================================================
echo      INICIANDO O SISTEMA DE ROTAS (HIBRIDO)
echo ======================================================
echo.

:: 1. Mostra o IP para o pessoal do faturamento saber qual acessar
echo Enderecos de IP disponiveis nesta maquina:
ipconfig | findstr "IPv4"
echo.
echo ------------------------------------------------------

:: 2. Inicia o Backend (Python)
echo [1/3] Iniciando Servidor Python (Backend)...
:: OBS: Como seus arquivos estao na raiz, nao damos 'cd backend'.
:: Ativamos o venv e rodamos o app.py
start "SISTEMA_BACKEND_NAO_FECHE" cmd /k "call .venv\Scripts\activate && python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000"

:: Pausa de 3 segundos para o Python carregar
timeout /t 3 /nobreak >nul

:: 3. Inicia o Frontend (React)
echo [2/3] Iniciando Interface Web (Frontend)...
:: Entramos na pasta correta 'rotas-frontend'
start "SISTEMA_FRONTEND_NAO_FECHE" cmd /k "cd rotas-frontend && npm run dev -- --host"

:: 4. Abre o navegador automaticamente
echo [3/3] Abrindo o navegador...
timeout /t 2 /nobreak >nul
start http://localhost:5173

cls
echo ======================================================
echo             SISTEMA RODANDO COM SUCESSO!
echo ======================================================
echo.
echo  NAO FECHE AS JANELAS PRETAS QUE ABRIRAM!
echo  Elas sao o servidor rodando.
echo.
echo  PARA ACESSAR DE OUTROS COMPUTADORES:
echo  Use o numero de IPV4 que apareceu acima.
echo  Exemplo: http://192.168.0.15:5173
echo.
pause
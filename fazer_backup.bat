@echo off
title SISTEMA DE BACKUP - ROTAS
color 0B

:: ============================================================
:: CONFIGURAÇÃO DO BACKUP
:: ============================================================

:: 1. Nome EXATO do seu banco de dados
set "ARQUIVO_BANCO=rotas.db"

:: 2. Nome da pasta onde os backups ficarão guardados
set "PASTA_DESTINO=backups_automaticos"

:: ============================================================
:: LÓGICA DE SEGURANÇA
:: ============================================================

echo.
echo  ------------------------------------------------------
echo    INICIANDO ROTINA DE BACKUP...
echo  ------------------------------------------------------
echo.

echo  [1/3] Procurando arquivo %ARQUIVO_BANCO%...
if not exist "%ARQUIVO_BANCO%" (
    color 0C
    echo.
    echo  [ERRO CRITICO] O arquivo "%ARQUIVO_BANCO%" nao foi encontrado nesta pasta!
    echo.
    pause
    exit
)

echo  [2/3] Verificando pasta de destino...
if not exist "%PASTA_DESTINO%" mkdir "%PASTA_DESTINO%"

:: Pega a data e hora (Formato seguro para nome de arquivo)
set "DATA_HORA=%date:~0,2%-%date:~3,2%-%date:~6,4%_%time:~0,2%h%time:~3,2%m"
:: Remove espaços em branco das horas (ex: 9h vira 09h)
set "DATA_HORA=%DATA_HORA: =0%"

echo  [3/3] Criando copia de seguranca...
copy "%ARQUIVO_BANCO%" "%PASTA_DESTINO%\backup_%DATA_HORA%_%ARQUIVO_BANCO%" >nul

if %errorlevel%==0 (
    color 0A
    echo.
    echo  ======================================================
    echo     SUCESSO! BACKUP REALIZADO COM SEGURANCA.
    echo  ======================================================
    echo.
    echo  Arquivo salvo: backup_%DATA_HORA%_%ARQUIVO_BANCO%
    echo  Local: Pasta "%PASTA_DESTINO%"
) else (
    color 0C
    echo.
    echo  [FALHA] Nao foi possivel copiar o arquivo.
    echo  Verifique se o sistema esta aberto (feche o servidor python antes).
)

echo.
pause
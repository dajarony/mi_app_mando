@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%\modules
uvicorn core2.core_dajarony.entradas.api_app:app --reload
.\venv\Scripts\activate
 python -m uvicorn core2.core_dajarony.entradas.api_app:app --reload
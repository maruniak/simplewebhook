@echo off
cd C:\develop\proj\simpleapp2
call .\env\Scripts\activate
uvicorn app:app --host 0.0.0.0 --port 8002

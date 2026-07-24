@echo off
echo ============================================
echo   考研复习平台 - LLM部署环境启动脚本
echo ============================================
echo.
echo 后端端口: 8080
echo 前端端口: 5180
echo LLM服务: 8081
echo.

set ENVIRONMENT=llm

cd backend
echo 启动本地LLM服务...
start cmd /k "python start_llm.py"

echo 等待LLM模型加载（约30-60秒）...
timeout /t 30 /nobreak >nul

echo 启动后端服务...
start cmd /k "uvicorn app.main:app --host 0.0.0.0 --port 8080"

cd ../frontend
echo 启动前端服务...
start cmd /k "npm run dev -- --mode llm"

echo.
echo ============================================
echo   LLM环境启动完成！
echo ============================================
echo.
echo 后端地址: http://localhost:8080
echo 前端地址: http://localhost:5180
echo LLM服务: http://localhost:8081
echo.
pause

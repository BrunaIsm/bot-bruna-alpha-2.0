"""
Script para iniciar Backend e Frontend simultaneamente
Mantém processos rodando até CTRL+C
"""
import subprocess
import sys
import os
import time
import signal

def signal_handler(sig, frame):
    print('\n\n🛑 Encerrando servidores...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    # Diretório do projeto
    project_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.join(project_dir, 'api')
    
    print("=" * 70)
    print("  🚀 BOT BRUNA ALPHA - INICIANDO SERVIDORES")
    print("=" * 70)
    print()
    
    # Iniciar Backend
    print("📡 Iniciando Backend (Flask)...")
    backend_process = subprocess.Popen(
        [sys.executable, 'run_simple.py'],
        cwd=api_dir,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    
    time.sleep(2)
    
    # Iniciar Frontend
    print("🌐 Iniciando Frontend (Vite)...")
    
    if sys.platform == 'win32':
        # No Windows, usar cmd.exe ao invés de PowerShell para evitar crash do Vite
        frontend_process = subprocess.Popen(
            ['cmd.exe', '/c', 'npm run dev'],
            cwd=project_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        frontend_process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=project_dir
        )
    
    print()
    print("=" * 70)
    print("  ✅ SERVIDORES INICIADOS!")
    print("=" * 70)
    print("  🔗 Backend:  http://localhost:5000")
    print("  🔗 Frontend: http://localhost:8080")
    print("=" * 70)
    print()
    print("💡 Duas janelas foram abertas com os servidores")
    print("💡 Feche este script quando quiser parar tudo")
    print("💡 Ou use CTRL+C")
    print()
    
    # Aguardar processos
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Encerrando...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == '__main__':
    main()

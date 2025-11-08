import sys
import os

# Garantir que estamos no diretório correto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Importar e rodar
from index import app

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 SERVIDOR FLASK - BOT BRUNA ALPHA")
    print("=" * 50)
    print(f"Servidor rodando em: http://127.0.0.1:5000")
    print(f"Pressione CTRL+C para parar")
    print("=" * 50)
    
    try:
        app.run(
            debug=True,
            port=5000,
            host='0.0.0.0',
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n✅ Servidor encerrado pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

import sys
import os

# Carregar variáveis de ambiente do .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from index import app

if __name__ == '__main__':
    print("=" * 60)
    print("  BACKEND FLASK - BOT BRUNA ALPHA")
    print("=" * 60)
    print("  Servidor: http://localhost:5000")
    print("  Endpoints: /api/health, /api/metrics, /api/analyze")
    print("=" * 60)
    print()
    
    # IMPORTANTE: use_reloader=False e threaded=True para estabilidade
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # Sem debug para evitar reloader
            use_reloader=False,  # CRÍTICO: sem reloader
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\nServidor encerrado pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERRO: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione ENTER para fechar...")

import sys
import traceback

try:
    from dotenv import load_dotenv
    import os
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    print("1. Variáveis de ambiente carregadas")
    print(f"   SUPABASE_URL: {os.getenv('SUPABASE_URL')[:30]}...")
    print(f"   SUPABASE_KEY: {os.getenv('SUPABASE_KEY')[:30]}...")
    
    # Tentar conectar ao Supabase
    from supabase import create_client, Client
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    print("2. Criando cliente Supabase...")
    supabase: Client = create_client(url, key)
    
    print("3. Cliente criado com sucesso!")
    
    # Tentar buscar dados
    print("4. Buscando dados da tabela vendas_2024...")
    response = supabase.table('vendas_2024').select('*').range(0, 9).execute()
    
    print(f"5. Dados recuperados: {len(response.data)} registros")
    if response.data:
        print(f"   Primeiro registro: {response.data[0]}")
    
    print("\n✓ CONEXÃO COM SUPABASE FUNCIONANDO!")
    
except Exception as e:
    print(f"\n✗ ERRO: {str(e)}")
    print("\nStack trace:")
    traceback.print_exc()

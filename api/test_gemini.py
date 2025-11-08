import requests
import json

# Testar o endpoint de análise
url = "http://127.0.0.1:5000/api/analyze"

questions = [
    "Qual foi o mês com maior faturamento?",
    "Quais os 5 produtos mais vendidos?",
    "Quanto foi vendido no total?",
]

print("=" * 60)
print("TESTANDO ANÁLISE COM GEMINI")
print("=" * 60)
print()

for i, question in enumerate(questions, 1):
    print(f"{i}. Pergunta: {question}")
    print("-" * 60)
    
    try:
        response = requests.post(
            url,
            json={"question": question},
            timeout=30
        )
        
        data = response.json()
        
        if response.status_code == 200:
            print(f"✓ Status: {response.status_code}")
            print(f"Resposta: {data.get('response', 'N/A')[:200]}...")
            print(f"Registros analisados: {data.get('recordsAnalyzed', 'N/A')}")
        else:
            print(f"✗ Status: {response.status_code}")
            print(f"Erro: {data.get('error', 'N/A')}")
            
    except Exception as e:
        print(f"✗ Erro de conexão: {str(e)}")
    
    print()

print("=" * 60)
print("TESTES CONCLUÍDOS")
print("=" * 60)

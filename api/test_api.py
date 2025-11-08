import requests
import json

base_url = "http://127.0.0.1:5000"

print("=" * 60)
print("TESTANDO API DO BOT BRUNA")
print("=" * 60)
print()

# 1. Test Health
print("1. Testando /api/health...")
try:
    response = requests.get(f"{base_url}/api/health")
    print(f"   Status: {response.status_code}")
    print(f"   Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"   ERRO: {str(e)}")
print()

# 2. Test Database Stats
print("2. Testando /api/database-stats...")
try:
    response = requests.get(f"{base_url}/api/database-stats")
    print(f"   Status: {response.status_code}")
    print(f"   Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"   ERRO: {str(e)}")
print()

# 3. Test Metrics
print("3. Testando /api/metrics...")
try:
    response = requests.get(f"{base_url}/api/metrics")
    print(f"   Status: {response.status_code}")
    print(f"   Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"   ERRO: {str(e)}")
print()

print("=" * 60)
print("TESTES CONCLUÍDOS")
print("=" * 60)

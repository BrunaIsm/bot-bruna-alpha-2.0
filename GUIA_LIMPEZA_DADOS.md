# 🗑️ Guia de Limpeza de Dados - API Clear Data

## Endpoint: `POST /api/clear-data`

### ⚠️ IMPORTANTE: Requer Confirmação
Por segurança, todas as operações de exclusão requerem `"confirm": true` no corpo da requisição.

---

## 🎯 Casos de Uso

### 1️⃣ Deletar Arquivo Específico

Remove apenas os dados de um arquivo específico (por nome).

**Exemplo**: Deletar dados do arquivo "teste_janeiro.xlsx"

#### Via PowerShell:
```powershell
$body = @{
    filename = "teste_janeiro.xlsx"
    confirm = $true
} | ConvertTo-Json

Invoke-WebRequest -Method POST -Uri "http://localhost:5000/api/clear-data" `
  -Body $body -ContentType "application/json"
```

#### Via cURL:
```bash
curl -X POST http://localhost:5000/api/clear-data \
  -H "Content-Type: application/json" \
  -d '{"filename": "teste_janeiro.xlsx", "confirm": true}'
```

#### Via JavaScript (Frontend):
```javascript
const response = await fetch('/api/clear-data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    filename: 'teste_janeiro.xlsx',
    confirm: true
  })
});

const result = await response.json();
console.log(result.message);
// "✅ 500 registros do arquivo "teste_janeiro" foram deletados"
```

**Resposta de Sucesso:**
```json
{
  "success": true,
  "message": "✅ 500 registros do arquivo \"teste_janeiro\" foram deletados",
  "rows_deleted": 500,
  "filename": "teste_janeiro"
}
```

---

### 2️⃣ Deletar TODOS os Dados (Limpar Banco Inteiro)

⚠️ **CUIDADO**: Remove TODOS os registros da tabela!

**Omita o campo `filename` para deletar tudo:**

#### Via PowerShell:
```powershell
$body = @{
    confirm = $true
} | ConvertTo-Json

Invoke-WebRequest -Method POST -Uri "http://localhost:5000/api/clear-data" `
  -Body $body -ContentType "application/json"
```

#### Via cURL:
```bash
curl -X POST http://localhost:5000/api/clear-data \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

**Resposta de Sucesso:**
```json
{
  "success": true,
  "message": "⚠️ TODOS os 2.600 registros foram deletados do banco!",
  "rows_deleted": 2600
}
```

---

### 3️⃣ Verificar Antes de Deletar (Sem Confirmar)

Para ver o que seria deletado sem executar a ação:

```powershell
# Sem "confirm": true → apenas retorna erro informativo
$body = @{
    filename = "teste.xlsx"
} | ConvertTo-Json

Invoke-WebRequest -Method POST -Uri "http://localhost:5000/api/clear-data" `
  -Body $body -ContentType "application/json"
```

**Resposta:**
```json
{
  "error": "Operação cancelada. Envie {\"confirm\": true} para confirmar a exclusão."
}
```

---

## 🔍 Verificar o Que Existe no Banco

Antes de deletar, você pode listar os arquivos:

### Via SQL (Supabase Dashboard):
```sql
-- Ver todos os arquivos diferentes no banco
SELECT mes_origem, COUNT(*) as total_registros, MAX(created_at) as ultimo_upload
FROM vendas_2024
GROUP BY mes_origem
ORDER BY ultimo_upload DESC;
```

**Exemplo de Resultado:**
```
mes_origem              | total_registros | ultimo_upload
------------------------|-----------------|------------------
vendas_2024_completo    | 2600            | 2025-11-08 10:00
teste_janeiro           | 500             | 2025-11-08 11:30
teste_fevereiro         | 300             | 2025-11-08 12:15
dados_professor         | 1000            | 2025-11-08 13:45
```

### Via API (endpoint /api/database-stats):
```bash
curl http://localhost:5000/api/database-stats
```

---

## 📋 Exemplos de Fluxo Completo

### Cenário 1: Professor Quer Testar do Zero

```powershell
# 1. Limpar todo o banco
$body = @{ confirm = $true } | ConvertTo-Json
Invoke-WebRequest -Method POST -Uri "http://localhost:5000/api/clear-data" -Body $body -ContentType "application/json"

# 2. Upload nova base
# (Via interface web ou API)

# 3. Testar com a IA
```

### Cenário 2: Remover Upload Errado

```powershell
# Upload acidental de "dados_errados.xlsx"
# Deletar apenas esse arquivo:

$body = @{
    filename = "dados_errados.xlsx"
    confirm = $true
} | ConvertTo-Json

Invoke-WebRequest -Method POST -Uri "http://localhost:5000/api/clear-data" -Body $body -ContentType "application/json"

# Outros arquivos permanecem intactos ✅
```

### Cenário 3: Resetar Para Base Original

```powershell
# 1. Limpar tudo
Invoke-WebRequest -Method POST -Uri "http://localhost:5000/api/clear-data" `
  -Body '{"confirm": true}' -ContentType "application/json"

# 2. Re-upload da base original "vendas_2024_completo.xlsx"
# (mantém apenas os 2.600 registros originais)
```

---

## 🛡️ Proteções de Segurança

1. **Confirmação Obrigatória**: Sem `"confirm": true`, nada é deletado
2. **Validação de Arquivo**: Se especificar arquivo inexistente, retorna erro 404
3. **Logs**: Todas as exclusões são registradas no console do servidor
4. **Sem Recuperação**: ⚠️ Dados deletados **NÃO podem ser recuperados**!

---

## ⚠️ Cuidados Importantes

❌ **Não é possível desfazer** após deletar  
❌ **Não há lixeira ou backup automático**  
✅ **Sempre verifique antes** qual arquivo quer deletar  
✅ **Use o Supabase Dashboard** para fazer backup antes de limpar tudo  

---

## 🔗 URLs dos Ambientes

**Local:**
- `http://localhost:5000/api/clear-data`

**Produção (Vercel):**
- `https://seu-dominio.vercel.app/api/clear-data`

---

## 📞 Respostas de Erro Comuns

### Arquivo Não Encontrado:
```json
{
  "success": false,
  "error": "Nenhum registro encontrado com o arquivo \"arquivo_inexistente\""
}
```

### Banco Já Vazio:
```json
{
  "success": true,
  "message": "Banco já está vazio",
  "rows_deleted": 0
}
```

### Sem Confirmação:
```json
{
  "error": "Operação cancelada. Envie {\"confirm\": true} para confirmar a exclusão."
}
```

---

**Desenvolvido para Alpha Insights - Sistema de Análise de Vendas com IA**

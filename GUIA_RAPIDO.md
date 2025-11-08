# Guia Rápido - Como Usar Após Migração

## ✅ Endpoints Disponíveis

### 1. Health Check
```
GET http://localhost:5000/api/health
```
Verifica se a API está funcionando.

### 2. Métricas
```
GET http://localhost:5000/api/metrics
```
Retorna métricas calculadas dos dados de vendas.

### 3. Estatísticas do Banco
```
GET http://localhost:5000/api/database-stats
```
Retorna estatísticas do banco Supabase (total de registros, meses, datas).

### 4. Análise com IA
```
POST http://localhost:5000/api/analyze
Content-Type: application/json

{
  "question": "Qual foi o produto mais vendido em 2024?"
}
```

### 5. Upload de Dados
```
POST http://localhost:5000/api/upload-data
Content-Type: multipart/form-data

file: [seu_arquivo.xlsx ou .csv]
```

### 6. Sincronizar Dados (Limpar Cache)
```
POST http://localhost:5000/api/sync-data
```

## 🚀 Como Iniciar

### Opção 1: Usar o script
```cmd
start-server.bat
```

### Opção 2: Manual
```cmd
cd api
python index.py
```

O servidor iniciará em: **http://localhost:5000**

## 🧪 Testar a API

### Teste 1: Verificar saúde
```cmd
curl http://localhost:5000/api/health
```

### Teste 2: Ver métricas
```cmd
curl http://localhost:5000/api/metrics
```

### Teste 3: Upload de arquivo (PowerShell)
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:5000/api/upload-data" -Method POST -InFile "caminho\para\arquivo.xlsx" -ContentType "multipart/form-data"
$response.Content
```

## 📋 Checklist Pós-Migração

- [x] Arquivo `.env` renomeado e configurado
- [x] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Schema SQL executado no Supabase
- [ ] Dados migrados/importados para o Supabase
- [ ] API testada localmente
- [ ] Frontend testado

## ⚠️ Troubleshooting

### Erro: "Não foi possível resolver a importação supabase"
**Solução:** Execute `pip install supabase`

### Erro: "Credenciais do Supabase não configuradas"
**Solução:** Verifique se o arquivo `.env` existe na pasta `api/` e contém:
```
SUPABASE_URL=sua_url
SUPABASE_KEY=sua_chave
GEMINI_API_KEY=sua_chave_gemini
```

### Erro 404 nas rotas
**Solução:** 
1. Certifique-se de que está acessando com o prefixo `/api/` (ex: `/api/health`)
2. Verifique se o servidor está rodando na porta 5000

### Erro ao fazer upload
**Solução:** 
1. Verifique se a tabela `vendas` foi criada no Supabase
2. Confirme que o arquivo tem as colunas corretas
3. Verifique o tamanho do arquivo (máx 10MB)

## 📱 Próximo Passo

Após iniciar o servidor, abra o frontend em outra janela:
```cmd
npm run dev
```

O sistema completo estará disponível!

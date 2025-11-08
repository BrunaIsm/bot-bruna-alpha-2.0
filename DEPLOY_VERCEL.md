# 🚀 Deploy no Vercel - Guia Definitivo

## ✅ Pré-requisitos

- Conta no GitHub (já tem ✓)
- Conta no Vercel (criar em vercel.com)
- Repositório no GitHub (já tem ✓)

## 📋 Passos para Deploy

### 1️⃣ Fazer Push do Código Atualizado

```bash
git add .
git commit -m "feat: preparar para deploy Vercel com handler e configs"
git push origin main
```

### 2️⃣ Conectar no Vercel

1. Acesse https://vercel.com
2. Clique em "Add New Project"
3. Selecione seu repositório: `BrunaIsm/bot-bruna-alpha`
4. Clique em "Import"

### 3️⃣ Configurar Variáveis de Ambiente

**IMPORTANTE**: Antes de fazer deploy, configure estas variáveis:

```
SUPABASE_URL=https://zcvobadirlicwysmehjm.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpjdm9iYWRpcmxpY3d5c21laGptIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTkyNTQ3NywiZXhwIjoyMDc3NTAxNDc3fQ.7782zgNgOLjeSjirviBeYUeWHIY082kgjrxj922Yyz8
GEMINI_API_KEY=AIzaSyASK8wjCFjRsZ0RdizpPMNZ_6QIrjOPTUw
SUPABASE_TABLE_NAME=vendas_2024
```

**Como adicionar**:
1. Na tela de import, clique em "Environment Variables"
2. Adicione cada variável com Name e Value
3. Selecione "Production", "Preview" e "Development"

### 4️⃣ Deploy

1. Clique em "Deploy"
2. Aguarde ~2 minutos
3. Acesse a URL gerada (ex: `https://bot-bruna-alpha.vercel.app`)

## 🎯 Verificar Deploy

### Frontend
- Acesse: `https://SEU-PROJETO.vercel.app`
- Deve carregar a interface React

### Backend API
- Teste: `https://SEU-PROJETO.vercel.app/api/health`
- Deve retornar: `{"status": "ok", "message": "API funcionando"}`

### Métricas (Supabase)
- Teste: `https://SEU-PROJETO.vercel.app/api/metrics`
- Deve retornar dados reais dos 2600 registros

## ⚠️ Problemas Comuns e Soluções

### Build Failed
- Verifique se `package.json` tem script `build`
- Certifique-se de que `dist/` está no `.gitignore`

### API 500 Error
- Verifique variáveis de ambiente no dashboard
- Veja logs em "Deployments" → "View Function Logs"

### Frontend em Branco
- Force refresh: Ctrl+Shift+R
- Verifique console do navegador (F12)

## 📊 Diferenças Local vs Produção

| Recurso | Local (Windows) | Produção (Vercel) |
|---------|----------------|-------------------|
| Backend | `python run_simple.py` | Serverless function |
| Frontend | `npm run dev` (port 8080) | Static files (CDN) |
| Banco | Supabase (cloud) | Supabase (cloud) ✓ |
| Logs | Terminal window | Dashboard Vercel |
| Restart | Fechar/abrir janela | Automático |

## 🔄 Atualizações Futuras

Sempre que modificar código:

```bash
git add .
git commit -m "Descrição da mudança"
git push origin main
```

Vercel redesenha **automaticamente** a cada push!

## ✅ Checklist Final

- [ ] Código commitado no GitHub
- [ ] Variáveis de ambiente configuradas no Vercel
- [ ] Build passou sem erros
- [ ] `/api/health` retorna OK
- [ ] `/api/metrics` retorna dados do Supabase
- [ ] Frontend carrega corretamente
- [ ] Chat responde perguntas

---

**Próximo passo**: Fazer commit das alterações e push para GitHub!

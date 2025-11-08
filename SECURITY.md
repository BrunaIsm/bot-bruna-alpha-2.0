# 🔒 Configuração de Segurança

## ⚠️ IMPORTANTE: Variáveis de Ambiente

Este projeto requer variáveis de ambiente que **NÃO DEVEM** ser commitadas no repositório.

### Configuração Local

1. Copie o arquivo de exemplo:
   ```cmd
   copy api\.env.example api\.env
   ```

2. Edite `api/.env` com suas credenciais reais:
   ```
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua-chave-anon-key-aqui
   SUPABASE_TABLE_NAME=vendas_2024
   GEMINI_API_KEY=sua-chave-gemini-aqui
   ```

### Configuração no Vercel

Adicione as mesmas variáveis no painel do Vercel:
- Settings → Environment Variables
- Configure para: Production, Preview, Development

## 🚫 Nunca Commite

- ❌ `api/.env`
- ❌ Arquivos com chaves de API
- ❌ Credenciais do Google Service Account
- ❌ Tokens de autenticação

## ✅ Arquivo .gitignore

O `.gitignore` já está configurado para proteger:
- `.env`
- `api/.env`
- `api/env`
- Arquivos Python compilados
- `node_modules/`

Se você acidentalmente commitou credenciais:
1. **Revogue imediatamente** as chaves comprometidas
2. **Remova do histórico Git** usando `git filter-branch` ou BFG Repo-Cleaner
3. Gere novas credenciais

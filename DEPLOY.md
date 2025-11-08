# 🚀 Guia Rápido de Deploy - Vercel

## Checklist Pré-Deploy

- [ ] Código commitado no GitHub
- [ ] Arquivo `.env` NÃO commitado (já está no .gitignore)
- [ ] Credenciais do Supabase prontas
- [ ] API Key do Gemini pronta
- [ ] Tabela `vendas_2024` criada no Supabase

## Passo a Passo

### 1️⃣ Preparar GitHub

```bash
# Verificar status
git status

# Adicionar todos os arquivos
git add .

# Fazer commit
git commit -m "Preparado para deploy no Vercel"

# Criar branch main (se ainda não existir)
git branch -M main

# Adicionar remote (substitua com seu repositório)
git remote add origin https://github.com/SEU-USUARIO/bot-bruna-alpha.git

# Fazer push
git push -u origin main
```

### 2️⃣ Configurar Vercel

1. Acesse https://vercel.com e faça login com GitHub
2. Clique em **"Add New Project"**
3. Selecione seu repositório `bot-bruna-alpha`
4. Clique em **"Import"**

### 3️⃣ Configurar Variáveis de Ambiente

Na página de configuração do projeto, vá em **Environment Variables** e adicione:

```
Nome: SUPABASE_URL
Valor: https://seu-projeto.supabase.co

Nome: SUPABASE_KEY
Valor: sua-chave-anon-public-aqui

Nome: GEMINI_API_KEY
Valor: sua-chave-gemini-aqui
```

**Importante:** Adicione para todos os ambientes (Production, Preview, Development)

### 4️⃣ Deploy

1. Clique em **"Deploy"**
2. Aguarde ~2-3 minutos
3. ✅ Pronto! Seu app está no ar!

## 🧪 Testar o Deploy

Após o deploy, teste:

1. **Frontend**: Abra a URL fornecida (https://seu-projeto.vercel.app)
2. **API Health**: Acesse `/api/health` e verifique:
   ```json
   {
     "status": "healthy",
     "supabase": "connected",
     "gemini": "configured"
   }
   ```
3. **Upload**: Faça upload de uma planilha de teste
4. **Chat**: Faça uma pergunta sobre os dados

## ⚠️ Problemas Comuns

### Erro 500 na API
- Verifique se as variáveis de ambiente estão configuradas
- Confira os logs: Vercel Dashboard > seu-projeto > Deployments > Logs

### Erro de conexão Supabase
- Verifique se a URL está correta (com https://)
- Confira se a chave é a `anon` (pública)
- Verifique se a tabela `vendas_2024` existe

### Erro Gemini API
- Verifique se a API Key está correta
- Confirme se a API está habilitada no console do Google

## 🔄 Atualizações Futuras

Para atualizar o projeto após mudanças:

```bash
git add .
git commit -m "Descrição das mudanças"
git push
```

O Vercel fará deploy automático! 🎉

## 📊 Monitoramento

- **Logs em tempo real**: Vercel Dashboard > Logs
- **Analytics**: Vercel Dashboard > Analytics
- **Uso de API**: Supabase Dashboard > API Usage

## 🎓 Dicas para Apresentação ao Professor

1. **Demonstre o upload**: Mostre como fazer upload de planilha
2. **Perguntas sugeridas**: Use as 8 perguntas prontas
3. **Análise temporal**: Pergunte sobre meses específicos
4. **Fallback**: Explique o sistema de 3 níveis
5. **Performance**: Mostre que funciona com 2600+ registros

---

**Bom deploy! 🚀**

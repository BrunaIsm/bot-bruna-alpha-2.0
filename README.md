# 🤖 Alpha Insights - Analista de Vendas IA

Sistema inteligente de análise de vendas com IA que integra Supabase e Google Gemini para fornecer insights automatizados sobre dados de vendas.

![Made with React](https://img.shields.io/badge/React-18-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![Supabase](https://img.shields.io/badge/Supabase-Database-green)
![Vercel](https://img.shields.io/badge/Deploy-Vercel-black)

## ✨ Funcionalidades

- 💬 **Chat Inteligente**: Interface conversacional para análise de dados
- 🗄️ **Banco Supabase**: Armazenamento robusto e escalável de dados
- 🤖 **Análise com IA**: Powered by Google Gemini 2.5 Flash API
- 📊 **Dashboard em Tempo Real**: Métricas e visualizações dinâmicas
- 📤 **Upload de Planilhas**: Suporte para Excel (.xlsx, .xls) e CSV
- 🎨 **Interface Moderna**: Design responsivo com Tailwind CSS e animações
- 🔄 **Fallback Inteligente**: Sistema de 3 níveis para garantir respostas sempre

## 🛠️ Tecnologias

### Frontend
- **React 18** + TypeScript
- **Vite** (Build tool ultrarrápido)
- **Tailwind CSS** (Estilização moderna)
- **shadcn/ui** (Componentes acessíveis)
- **Lucide React** (Ícones modernos)
- **Sonner** (Notificações elegantes)

### Backend
- **Python 3.9+** com Flask
- **Supabase** (PostgreSQL database)
- **Google Gemini AI** (2.5 Flash)
- **Pandas** (Análise de dados)
- **python-dotenv** (Variáveis de ambiente)

## 📋 Pré-requisitos

1. **Node.js** (versão 18+)
2. **Python** (versão 3.9+)
3. **Conta Supabase** (gratuita)
4. **Google Gemini API Key** (gratuita)

## ⚙️ Configuração Local

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/bot-bruna-alpha.git
cd bot-bruna-alpha-1
```

### 2. Instale as dependências

**Frontend:**
```bash
npm install
```

**Backend:**
```bash
pip install -r api/requirements.txt
```

### 3. Configure as variáveis de ambiente

Copie o arquivo de exemplo:
```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
# Supabase Configuration
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon-key-aqui

# Gemini API Configuration
GEMINI_API_KEY=sua-chave-gemini-aqui
```

### 4. Configure o Supabase

Execute o SQL do arquivo `api/supabase_schema.sql` no SQL Editor do Supabase:

```sql
-- Cria a tabela vendas_2024
CREATE TABLE vendas_2024 (
  id BIGSERIAL PRIMARY KEY,
  data DATE NOT NULL,
  id_transacao TEXT,
  produto TEXT NOT NULL,
  categoria TEXT NOT NULL,
  regiao TEXT NOT NULL,
  quantidade NUMERIC NOT NULL,
  preco_unitario NUMERIC NOT NULL,
  receita_total NUMERIC NOT NULL,
  mes_origem TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para melhor performance
CREATE INDEX idx_vendas_data ON vendas_2024(data);
CREATE INDEX idx_vendas_produto ON vendas_2024(produto);
CREATE INDEX idx_vendas_regiao ON vendas_2024(regiao);
```

## 🚀 Executando Localmente

### Opção 1: Usar o script batch (Windows)
```bash
.\start-server.bat
```

### Opção 2: Executar separadamente

**Terminal 1 - Backend:**
```bash
cd api
python index.py
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

- Frontend: `http://localhost:8080`
- Backend: `http://127.0.0.1:5000`

## 🌐 Deploy no Vercel

### Passo 1: Push para GitHub

```bash
git add .
git commit -m "Deploy inicial"
git branch -M main
git remote add origin https://github.com/seu-usuario/bot-bruna-alpha.git
git push -u origin main
```

### Passo 2: Importar no Vercel

1. Acesse [vercel.com](https://vercel.com) e faça login
2. Clique em **"Add New Project"**
3. Importe seu repositório do GitHub
4. Configure as variáveis de ambiente:

**Environment Variables:**
```
SUPABASE_URL = https://seu-projeto.supabase.co
SUPABASE_KEY = sua-chave-anon-key-aqui
GEMINI_API_KEY = sua-chave-gemini-aqui
```

5. Clique em **"Deploy"**

### Passo 3: Configuração Adicional (se necessário)

O arquivo `vercel.json` já está configurado para rotear as APIs corretamente:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/index.py"
    }
  ]
}
```

✅ Pronto! Seu projeto estará no ar em poucos minutos!

## 📁 Estrutura do Projeto

```
bot-bruna-alpha-1/
├── api/                      # Backend Flask + Python
│   ├── index.py             # Aplicação principal
│   ├── requirements.txt     # Dependências Python
│   ├── runtime.txt          # Versão Python para Vercel
│   ├── supabase_schema.sql  # Schema do banco de dados
│   └── test_*.py            # Scripts de teste
├── src/                      # Frontend React + TypeScript
│   ├── components/          # Componentes reutilizáveis
│   │   ├── ui/             # Componentes shadcn/ui
│   │   ├── ChatMessage.tsx  # Mensagem do chat
│   │   ├── FileUpload.tsx   # Upload de planilhas
│   │   └── MetricsCard.tsx  # Card de métricas
│   ├── pages/               # Páginas da aplicação
│   │   ├── Index.tsx        # Página principal
│   │   └── NotFound.tsx     # Página 404
│   ├── lib/                 # Utilitários
│   └── hooks/               # React hooks customizados
├── public/                   # Arquivos estáticos
├── .env.example             # Exemplo de variáveis de ambiente
├── vercel.json              # Configuração Vercel
├── vite.config.ts           # Configuração Vite
├── tailwind.config.ts       # Configuração Tailwind
├── package.json             # Dependências Node.js
└── README.md                # Este arquivo
```

## 🔧 Endpoints da API

### GET /api/health
Verifica status da API e conexão com Supabase.

**Response:**
```json
{
  "status": "healthy",
  "supabase": "connected",
  "gemini": "configured"
}
```

### GET /api/metrics
Retorna métricas calculadas dos dados.

**Response:**
```json
{
  "top_product": "Headset HyperX",
  "top_product_quantity": 463,
  "total_sales": 33044725.01,
  "best_month": "Abril/2024",
  "best_month_value": 5119562.68
}
```

### POST /api/analyze
Analisa dados com base em uma pergunta.

**Body:**
```json
{
  "question": "Qual região teve mais vendas em janeiro?"
}
```

**Response:**
```json
{
  "response": "🌍 Em Janeiro/2024, a região com mais vendas foi Norte...",
  "filesProcessed": 12,
  "recordsAnalyzed": 2600
}
```

### POST /api/upload-data
Faz upload de planilha Excel ou CSV.

**Form Data:**
- `file`: Arquivo Excel (.xlsx, .xls) ou CSV

**Response:**
```json
{
  "success": true,
  "rows_imported": 500,
  "message": "Arquivo importado com sucesso!"
}
```

### POST /api/sync-data
Limpa cache e força recarregamento dos dados.

**Response:**
```json
{
  "message": "Sincronização concluída!",
  "recordsAnalyzed": 2600
}
```

## 🎨 Funcionalidades Especiais

### Sistema de Fallback Inteligente (3 Níveis)

1. **Nível 1**: Tenta Gemini com prompt completo + dados agregados
2. **Nível 2**: Se falhar (SAFETY block), tenta prompt simplificado
3. **Nível 3**: Se ainda falhar, usa análise Python direta (sem IA)

Isso garante que o usuário **sempre** recebe uma resposta, mesmo se a Gemini bloquear conteúdo.

### Perguntas Sugeridas

8 perguntas prontas com categorias:
- 📊 Análise Mensal
- 🏆 Top Produtos  
- 💰 Faturamento
- 🌍 Análise Regional
- 📈 Evolução Mensal
- 🎯 Categorias
- 📅 Comparação
- 🛒 Diversidade

### Cache Inteligente

- Dados ficam em cache por 5 minutos
- Cache é limpo automaticamente após uploads
- Otimizado para performance com 2600+ registros

## 🔐 Obtendo as Credenciais

### Supabase

1. Acesse [supabase.com](https://supabase.com)
2. Crie um novo projeto (gratuito)
3. Vá em **Settings > API**
4. Copie:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_KEY`

### Google Gemini API

1. Acesse [aistudio.google.com](https://aistudio.google.com)
2. Clique em **"Get API Key"**
3. Crie ou selecione um projeto
4. Copie a API Key → `GEMINI_API_KEY`

### 1. Criar Service Account:
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione existente
3. Habilite as APIs: Drive API e Sheets API
4. Crie uma Service Account
5. Baixe o arquivo JSON de credenciais
6. Compartilhe a pasta do Google Drive com o email da Service Account

### 2. Obter Gemini API Key:
1. Acesse [Google AI Studio](https://makersuite.google.com/)
2. Crie uma nova API Key
3. Adicione a key no arquivo `.env`

## 🐛 Troubleshooting

### Erro de CORS
Certifique-se de que o Flask está configurado com CORS habilitado.

### Erro de Autenticação Google
Verifique se:
- As credenciais JSON estão corretas
- A Service Account tem acesso à pasta do Drive
- As APIs estão habilitadas no Google Cloud

### Erro de Gemini API
Verifique se:
- A API Key está correta
- Você tem créditos disponíveis na conta

## 📝 Licença

Este projeto está sob a licença MIT.

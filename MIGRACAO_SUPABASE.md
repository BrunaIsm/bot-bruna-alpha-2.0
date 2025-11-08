# Migração de Google Drive para Supabase

## ✅ Migração Concluída

O sistema foi migrado com sucesso do Google Drive para o Supabase como banco de dados.

## 📋 Mudanças Realizadas

### 1. **Dependências Atualizadas**
- ❌ Removido: `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`
- ✅ Adicionado: `supabase==2.3.0`

### 2. **Variáveis de Ambiente (arquivo `env`)**
- ❌ Removido: `GOOGLE_DRIVE_FOLDER_ID`, `GOOGLE_CREDENTIALS_JSON`
- ✅ Adicionado: `SUPABASE_URL`, `SUPABASE_KEY`

### 3. **Estrutura de Dados**
- Schema criado em: `api/supabase_schema.sql`
- Tabela: `vendas`
- Colunas: `id`, `data`, `id_transacao`, `produto`, `categoria`, `regiao`, `quantidade`, `preco_unitario`, `receita_total`, `mes_origem`, `created_at`, `updated_at`

### 4. **Endpoints da API Atualizados**

#### Endpoints Modificados:
- `POST /api/upload-data` (antes: `/api/upload-to-drive`)
  - Agora insere dados diretamente no Supabase
  - Aceita arquivos Excel (.xlsx, .xls) e CSV
  - Processa e valida dados antes de inserir

- `POST /api/sync-data` (antes: `/api/sync-drive`)
  - Limpa o cache e força recarregamento dos dados do Supabase

#### Endpoints Novos:
- `GET /api/database-stats`
  - Retorna estatísticas do banco de dados (total de registros, meses únicos, datas)

#### Endpoints Removidos:
- ❌ `/api/drive-storage` - Não mais necessário
- ❌ `/api/drive-cleanup` - Não mais necessário
- ❌ `/api/drive-info` - Não mais necessário

#### Endpoints Mantidos:
- ✅ `POST /api/analyze` - Análise de vendas com Gemini
- ✅ `GET /api/metrics` - Métricas calculadas
- ✅ `GET /api/health` - Health check

## 🚀 Como Usar

### 1. **Instalar Dependências**
```bash
pip install -r api/requirements.txt
```

### 2. **Configurar Variáveis de Ambiente**
Certifique-se de que o arquivo `api/env` contém:
```env
SUPABASE_URL=https://zcvobadirlicwysmehjm.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
GEMINI_API_KEY=AIzaSyASK8wjCFjRsZ0RdizpPMNZ_6QIrjOPTUw
```

### 3. **Executar o Schema SQL no Supabase**
1. Acesse o painel do Supabase: https://app.supabase.com
2. Vá em "SQL Editor"
3. Execute o conteúdo do arquivo `api/supabase_schema.sql`

### 4. **Iniciar a API**
```bash
cd api
python index.py
```

## 📤 Upload de Dados

Para fazer upload de dados de vendas:

```bash
# Exemplo usando curl
curl -X POST http://localhost:5000/api/upload-data \
  -F "file=@vendas_janeiro.xlsx"
```

Ou através do frontend, enviando o arquivo pelo componente de upload.

## 🔄 Sincronização de Dados

Para limpar o cache e forçar recarregamento dos dados:

```bash
curl -X POST http://localhost:5000/api/sync-data
```

## 📊 Estatísticas do Banco

Para verificar estatísticas do banco de dados:

```bash
curl http://localhost:5000/api/database-stats
```

## 🎯 Benefícios da Migração

1. **Performance**: Consultas SQL mais rápidas que leitura de múltiplas planilhas
2. **Escalabilidade**: Supabase suporta milhões de registros
3. **Simplicidade**: Não precisa gerenciar armazenamento ou limpar arquivos antigos
4. **Confiabilidade**: Banco de dados PostgreSQL robusto e confiável
5. **Recursos**: Row Level Security, triggers, índices automáticos

## 📝 Notas Importantes

- Os dados antigos do Google Drive precisam ser migrados manualmente
- Use o endpoint `/api/upload-data` para importar planilhas existentes
- O sistema mantém cache de 5 minutos para otimizar performance
- Todas as datas são armazenadas no formato ISO (YYYY-MM-DD)

## 🛠️ Troubleshooting

### Erro de conexão com Supabase
- Verifique se as variáveis `SUPABASE_URL` e `SUPABASE_KEY` estão corretas
- Confirme que a tabela `vendas` foi criada com o schema correto

### Erro ao fazer upload
- Verifique se o arquivo contém todas as colunas obrigatórias
- Certifique-se de que os dados estão no formato correto (datas, números)

### Cache não atualiza
- Faça uma requisição POST para `/api/sync-data` para limpar o cache

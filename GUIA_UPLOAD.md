# 📤 Sistema de Upload de Arquivos - Guia Completo

## Como Funciona o Upload

O sistema Alpha Insights possui um endpoint robusto para upload de arquivos Excel/CSV que **automaticamente processa e insere os dados no banco Supabase**.

### Endpoint: `POST /api/upload-data`

## ✅ Funcionalidades Implementadas

### 1. **Validação de Arquivo**
- Aceita: `.xlsx`, `.xls`, `.csv`
- Tamanho máximo: 10MB (validado no frontend)
- Rejeita arquivos vazios ou corrompidos

### 2. **Normalização Automática de Colunas**
O sistema é inteligente e reconhece várias variações de nomes:

| Coluna Esperada | Variações Aceitas |
|-----------------|-------------------|
| `data` | data, date, dt_venda, data_venda |
| `id_transacao` | id_transacao, id, transacao, id_venda |
| `produto` | produto, product, item, descricao |
| `categoria` | categoria, category, tipo |
| `regiao` | regiao, region, estado, uf |
| `quantidade` | quantidade, qtd, quantity, qtde |
| `preco_unitario` | preco_unitario, preco, price, valor_unitario |
| `receita_total` | receita_total, total, valor_total, receita |

**Exemplo**: Uma planilha com colunas `Preço`, `Qtde`, `Product` será automaticamente convertida para `preco_unitario`, `quantidade`, `produto`.

### 3. **Preenchimento Automático de Colunas Opcionais**

Se a planilha não tiver todas as colunas, o sistema preenche automaticamente:

- **`id_transacao`**: Gera IDs únicos (TXN000001, TXN000002, ...)
- **`categoria`**: "Sem categoria"
- **`regiao`**: "Não especificada"
- **`preco_unitario`**: Calcula automaticamente (`receita_total ÷ quantidade`)

### 4. **Conversão de Dados**

#### Datas
- Aceita: `01/01/2024`, `2024-01-01`, `01-01-2024`
- Converte para: `2024-01-01` (formato ISO)

#### Números
- Aceita vírgula: `1.250,50` ou ponto: `1250.50`
- Remove símbolos: `R$ 1.250,50` → `1250.50`

### 5. **Limpeza de Dados**
- Remove linhas com dados inválidos
- Remove caracteres especiais em números
- Valida campos obrigatórios: `data`, `produto`, `quantidade`, `receita_total`

### 6. **Inserção em Lotes no Supabase**
- Insere até **1000 registros por vez** (otimizado para Vercel)
- Adiciona metadados:
  - `mes_origem`: Nome do arquivo (para rastreamento)
  - `created_at`: Timestamp do upload

## 📋 Exemplos de Planilhas Aceitas

### ✅ Exemplo Completo
```csv
Data,ID_Transacao,Produto,Categoria,Regiao,Quantidade,Preco_Unitario,Receita_Total
01/01/2024,TXN001,Notebook Dell,Eletrônicos,Sul,5,2500.00,12500.00
```

### ✅ Exemplo Mínimo (colunas opcionais serão preenchidas)
```csv
Data,Produto,Quantidade,Receita_Total
01/01/2024,Mouse Logitech,10,755.00
```

### ✅ Exemplo com Nomes Alternativos
```csv
Date,Product,Qtd,Total,Region,Category
2024-01-01,Teclado Mecânico,3,1350.00,Sudeste,Periféricos
```

## 🎯 Como Testar

### 1. Via Interface Web
1. Acesse a aplicação
2. Clique no botão **"📤 Upload de Arquivo"**
3. Selecione um arquivo Excel/CSV
4. Aguarde a confirmação (mostra quantas linhas foram importadas)
5. Use o botão **"🔄 Atualizar Dados"** para sincronizar métricas

### 2. Via API (cURL)
```bash
curl -X POST http://localhost:5000/api/upload-data \
  -F "file=@seu_arquivo.xlsx"
```

### 3. Via PowerShell
```powershell
$file = "C:\caminho\para\arquivo.xlsx"
$uri = "http://localhost:5000/api/upload-data"
$fileBin = [System.IO.File]::ReadAllBytes($file)
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

$bodyLines = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"$(Split-Path $file -Leaf)`"",
    "Content-Type: application/octet-stream$LF",
    [System.Text.Encoding]::GetString($fileBin),
    "--$boundary--$LF"
) -join $LF

Invoke-RestMethod -Uri $uri -Method Post -ContentType "multipart/form-data; boundary=$boundary" -Body $bodyLines
```

## 🔍 Resposta da API

### Sucesso (200)
```json
{
  "success": true,
  "message": "✅ 1500 linhas importadas com sucesso!",
  "rows_imported": 1500,
  "filename": "vendas_janeiro.xlsx",
  "columns_found": ["data", "produto", "quantidade", "receita_total", "categoria", "regiao"]
}
```

### Erro (400/500)
```json
{
  "success": false,
  "error": "Colunas obrigatórias faltando: data, produto",
  "found_columns": ["id", "item", "qtd", "total"]
}
```

## ⚠️ Limitações

1. **Tamanho do arquivo**: Máximo 10MB (validado no frontend)
2. **Timeout do Vercel**: Uploads muito grandes podem exceder o limite de 10s do Vercel (serverless)
   - Recomendação: Arquivos com até ~5.000 linhas funcionam bem
3. **Formato de data**: Se a data não for reconhecida, a linha será ignorada

## 🚀 Melhorias Futuras

- [ ] Upload assíncrono para arquivos grandes (background job)
- [ ] Preview dos dados antes de confirmar upload
- [ ] Opção de substituir ou mesclar dados existentes
- [ ] Validação de duplicatas por `id_transacao`
- [ ] Download de template de planilha modelo
- [ ] Histórico de uploads com rollback

## 🛠️ Solução de Problemas

### "Colunas obrigatórias faltando"
- Verifique se sua planilha tem pelo menos: `Data`, `Produto`, `Quantidade`, `Receita Total`
- Nomes de colunas são flexíveis (veja tabela de variações aceitas acima)

### "Nenhuma linha válida encontrada"
- Verifique se as datas estão no formato correto
- Certifique-se de que números não contêm texto

### "Timeout" no Vercel
- Reduza o tamanho do arquivo
- Divida em múltiplos uploads menores

### Upload funciona local mas não no Vercel
- Verifique se `pandas` e `openpyxl` estão no `requirements.txt`
- Confirme que as variáveis de ambiente estão configuradas no Vercel

## 📝 Exemplo de Teste Completo

1. Crie um arquivo `teste.csv`:
```csv
Data,Produto,Qtd,Total
15/01/2024,Produto Teste,5,500.00
```

2. Faça upload via interface web

3. Verifique no banco se os dados foram inseridos:
   - Use o endpoint `/api/metrics` para ver se o total de registros aumentou
   - Pergunte à IA: "Quantos produtos foram vendidos em 15 de janeiro?"

---

**Desenvolvido para Alpha Insights - Sistema de Análise de Vendas com IA**

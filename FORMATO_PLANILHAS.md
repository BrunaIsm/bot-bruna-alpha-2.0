# 📋 Formato de Planilhas para Upload

## Colunas Obrigatórias

O sistema espera planilhas Excel (.xlsx, .xls) ou CSV com as seguintes colunas:

| Coluna | Tipo | Exemplo | Descrição |
|--------|------|---------|-----------|
| **Data** | Data | 01/01/2024 | Data da transação |
| **ID_Transacao** | Texto | TXN001 | Identificador único da transação |
| **Produto** | Texto | Notebook Dell | Nome do produto vendido |
| **Categoria** | Texto | Eletrônicos | Categoria do produto |
| **Regiao** | Texto | Sul | Região da venda (Norte, Sul, Nordeste, Sudeste, Centro-Oeste) |
| **Quantidade** | Número | 5 | Quantidade vendida |
| **Preco_Unitario** | Número | 2500.00 | Preço por unidade |
| **Receita_Total** | Número | 12500.00 | Quantidade × Preço Unitário |

## Exemplo de Planilha

```csv
Data,ID_Transacao,Produto,Categoria,Regiao,Quantidade,Preco_Unitario,Receita_Total
01/01/2024,TXN001,Notebook Dell,Eletrônicos,Sul,5,2500.00,12500.00
01/01/2024,TXN002,Mouse Logitech,Periféricos,Norte,10,75.50,755.00
02/01/2024,TXN003,Teclado Mecânico,Periféricos,Sudeste,3,450.00,1350.00
```

## Formatos Suportados

- ✅ Excel 2007+ (.xlsx)
- ✅ Excel 97-2003 (.xls)
- ✅ CSV com separador de vírgula

## Validações Automáticas

O sistema automaticamente:

1. **Padroniza nomes de colunas**:
   - Remove acentos: `Preço` → `preco`
   - Converte para minúsculas
   - Substitui espaços por underscores

2. **Converte tipos de dados**:
   - Datas para formato ISO (YYYY-MM-DD)
   - Números decimais (aceita vírgula ou ponto)
   - Remove linhas com dados inválidos

3. **Adiciona metadados**:
   - `mes_origem`: Nome do arquivo
   - `created_at`: Data/hora do upload

## Tamanho Máximo

- **Limite por arquivo**: 10 MB
- **Registros recomendados**: Até 10.000 por upload
- **Total no banco**: Ilimitado (Supabase Free Tier: até 500 MB)

## Dicas para Melhores Resultados

### ✅ Fazer

- Use nomes de colunas claros e consistentes
- Preencha todas as células obrigatórias
- Use formato de data DD/MM/YYYY ou YYYY-MM-DD
- Separe milhares com ponto e decimais com vírgula (ou vice-versa)
- Nomeie o arquivo com identificação clara (ex: vendas_janeiro_2024.xlsx)

### ❌ Evitar

- Células vazias em colunas obrigatórias
- Caracteres especiais em nomes de produtos
- Formatos de data ambíguos
- Fórmulas do Excel (use apenas valores)
- Linhas de cabeçalho duplicadas
- Múltiplas planilhas no mesmo arquivo (use apenas a primeira)

## Exemplo de Planilha de Teste

Você pode criar uma planilha de teste com estes dados:

| Data | ID_Transacao | Produto | Categoria | Regiao | Quantidade | Preco_Unitario | Receita_Total |
|------|-------------|---------|-----------|--------|------------|----------------|---------------|
| 01/11/2024 | TEST001 | Mouse Gamer | Periféricos | Norte | 2 | 150.00 | 300.00 |
| 01/11/2024 | TEST002 | Teclado RGB | Periféricos | Sul | 1 | 250.00 | 250.00 |
| 02/11/2024 | TEST003 | Monitor 24" | Monitores | Sudeste | 1 | 800.00 | 800.00 |
| 02/11/2024 | TEST004 | Webcam HD | Acessórios | Nordeste | 3 | 200.00 | 600.00 |
| 03/11/2024 | TEST005 | Headset USB | Áudio | Centro-Oeste | 2 | 180.00 | 360.00 |

**Total**: 5 registros, R$ 2.310,00

## Mensagens de Erro Comuns

### "Colunas obrigatórias ausentes"
- **Causa**: Faltam colunas necessárias
- **Solução**: Verifique se todas as 8 colunas obrigatórias existem

### "Nenhum dado válido encontrado"
- **Causa**: Todas as linhas têm dados inválidos
- **Solução**: Verifique formatos de data e números

### "Tipo de arquivo não permitido"
- **Causa**: Formato não suportado
- **Solução**: Converta para .xlsx, .xls ou .csv

### "Arquivo muito grande"
- **Causa**: Arquivo maior que 10 MB
- **Solução**: Divida em múltiplos arquivos menores

## Após o Upload

Você verá a mensagem:
```
✅ X linhas importadas!
🔄 Dados atualizados e prontos para análise.
Você já pode fazer perguntas sobre os novos dados!
```

Os dados ficam permanentemente no Supabase e podem ser consultados junto com uploads anteriores.

---

**Dúvidas?** O sistema valida automaticamente e mostra mensagens claras de erro! 🎯

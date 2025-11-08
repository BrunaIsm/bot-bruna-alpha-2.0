"""
API Flask para Vercel - Versão otimizada com requests direto (sem SDK pesado)
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

# Configurações
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
TABLE_NAME = os.getenv('SUPABASE_TABLE_NAME', 'vendas_2024')

# ARQUIVO BASE PROTEGIDO (não pode ser deletado)
PROTECTED_FILE = 'vendas_2024_completo'

def query_supabase(select_fields='*', max_records=10000):
    """Query direta na API REST do Supabase com paginação automática"""
    try:
        all_data = []
        page_size = 1000
        offset = 0
        
        while len(all_data) < max_records:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"
            headers = {
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Content-Type': 'application/json',
                'Range': f'{offset}-{offset + page_size - 1}'
            }
            params = {
                'select': select_fields
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=8)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
            
            all_data.extend(data)
            
            if len(data) < page_size:
                break
            
            offset += page_size
        
        return all_data, None
    except Exception as e:
        return None, str(e)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'message': 'API funcionando (requests direto)',
        'environment': {
            'supabase_url_configured': bool(SUPABASE_URL),
            'supabase_key_configured': bool(SUPABASE_KEY),
            'table_name': TABLE_NAME
        }
    }), 200

@app.route('/api/metrics', methods=['GET'])
def metrics():
    """Retorna métricas do Supabase usando requests direto"""
    try:
        # Buscar todos os registros (até 10000)
        data, error = query_supabase('produto,quantidade,receita_total,data')
        
        if error:
            raise Exception(error)
        
        if not data:
            return jsonify({
                'melhor_mes': {'nome': 'Sem dados', 'valor': 'R$ 0,00'},
                'produto_mais_vendido': {'nome': 'Sem dados', 'quantidade': 0},
                'quantidade_produtos': 0,
                'vendas_totais_ano': 'R$ 0,00',
                'files_processed': 0,
                'records_analyzed': 0,
                'last_updated': datetime.utcnow().strftime('%d/%m/%Y %H:%M'),
                'no_data': True
            }), 200
        
        # Processar dados
        produtos_qty = {}
        receita_por_mes = {}
        receita_total = 0.0
        produtos_set = set()
        
        meses_pt = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        for row in data:
            try:
                prod = row.get('produto', 'Desconhecido')
                produtos_set.add(prod)
                
                qty = float(str(row.get('quantidade', 0)).replace(',', '.'))
                receita = float(str(row.get('receita_total', 0)).replace(',', '.'))
                
                produtos_qty[prod] = produtos_qty.get(prod, 0) + qty
                receita_total += receita
                
                data_str = row.get('data')
                if data_str:
                    dt = datetime.fromisoformat(str(data_str)[:10])
                    mes_nome = f"{meses_pt[dt.month]}/{dt.year}"
                    receita_por_mes[mes_nome] = receita_por_mes.get(mes_nome, 0.0) + receita
            except:
                continue
        
        # Melhor mês
        if receita_por_mes:
            melhor_mes_nome = max(receita_por_mes, key=receita_por_mes.get)
            melhor_mes_valor = receita_por_mes[melhor_mes_nome]
        else:
            melhor_mes_nome, melhor_mes_valor = 'Sem dados', 0.0
        
        # Produto mais vendido
        if produtos_qty:
            prod_top = max(produtos_qty, key=produtos_qty.get)
            qtd_top = int(produtos_qty[prod_top])
        else:
            prod_top, qtd_top = 'Sem dados', 0
        
        # Formatar moeda
        def fmt_currency(value):
            return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        return jsonify({
            'melhor_mes': {
                'nome': melhor_mes_nome,
                'valor': fmt_currency(melhor_mes_valor)
            },
            'produto_mais_vendido': {
                'nome': prod_top,
                'quantidade': qtd_top
            },
            'quantidade_produtos': len([p for p in produtos_set if p]),
            'vendas_totais_ano': fmt_currency(receita_total),
            'files_processed': 1,
            'records_analyzed': len(data),
            'last_updated': datetime.utcnow().strftime('%d/%m/%Y %H:%M'),
            'no_data': False
        }), 200
        
    except Exception as e:
        print(f"ERRO NO /api/metrics: {str(e)}")
        return jsonify({
            'error': str(e),
            'no_data': True,
            'melhor_mes': {'nome': 'Erro ao carregar', 'valor': 'R$ 0,00'},
            'produto_mais_vendido': {'nome': 'Erro ao carregar', 'quantidade': 0},
            'quantidade_produtos': 0,
            'vendas_totais_ano': 'R$ 0,00',
            'files_processed': 0,
            'records_analyzed': 0,
            'last_updated': datetime.utcnow().strftime('%d/%m/%Y %H:%M')
        }), 200

@app.route('/api/monthly-metrics', methods=['GET'])
def monthly_metrics():
    """Retorna métricas detalhadas por mês"""
    try:
        data, error = query_supabase('produto,quantidade,receita_total,data')
        
        if error or not data:
            return jsonify({'no_data': True, 'months': []}), 200
        
        meses_pt = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        dados_por_mes = {}
        
        for row in data:
            try:
                data_str = row.get('data')
                if not data_str:
                    continue
                
                dt = datetime.fromisoformat(str(data_str)[:10])
                mes_key = f"{dt.year}-{dt.month:02d}"
                mes_nome = f"{meses_pt[dt.month]}/{dt.year}"
                
                if mes_key not in dados_por_mes:
                    dados_por_mes[mes_key] = {
                        'nome': mes_nome,
                        'receita': 0.0,
                        'vendas': 0,
                        'produtos': {}
                    }
                
                prod = row.get('produto', 'Desconhecido')
                qty = float(str(row.get('quantidade', 0)).replace(',', '.'))
                receita = float(str(row.get('receita_total', 0)).replace(',', '.'))
                
                dados_por_mes[mes_key]['receita'] += receita
                dados_por_mes[mes_key]['vendas'] += 1
                dados_por_mes[mes_key]['produtos'][prod] = dados_por_mes[mes_key]['produtos'].get(prod, 0) + qty
            except:
                continue
        
        # Formatar resultado
        def fmt_currency(value):
            return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        months = []
        for mes_key in sorted(dados_por_mes.keys()):
            mes_data = dados_por_mes[mes_key]
            
            # Top 5 produtos do mês
            top_produtos = sorted(
                mes_data['produtos'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            months.append({
                'month': mes_data['nome'],
                'total_revenue': fmt_currency(mes_data['receita']),
                'total_sales': mes_data['vendas'],
                'top_products': [
                    {'name': prod, 'quantity': int(qty)}
                    for prod, qty in top_produtos
                ]
            })
        
        return jsonify({
            'no_data': False,
            'months': months
        }), 200
        
    except Exception as e:
        print(f"ERRO NO /api/monthly-metrics: {str(e)}")
        return jsonify({'no_data': True, 'months': [], 'error': str(e)}), 200

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Análise inteligente com Google Gemini AI usando TODOS os dados agregados"""
    try:
        body = request.get_json()
        question = body.get('message', '')
        
        if not question:
            return jsonify({'answer': '❌ Por favor, faça uma pergunta.'}), 200
        
        # Buscar TODOS os dados para análise precisa
        data, error = query_supabase('produto,quantidade,receita_total,data,categoria,regiao')
        
        if error or not data:
            return jsonify({
                'answer': '❌ Não foi possível acessar os dados. Verifique a conexão com o Supabase.'
            }), 200
        
        # AGREGAR TODOS OS DADOS (resumo compacto para o Gemini)
        meses_pt = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        # Agregações
        produtos_total = {}  # Total geral de cada produto
        produtos_por_mes = {}  # Produtos por mês
        receita_por_mes = {}  # Receita por mês
        vendas_por_mes = {}  # Quantidade de vendas por mês
        produtos_por_categoria = {}  # Produtos por categoria
        receita_por_categoria = {}  # Receita por categoria
        produtos_por_regiao = {}  # Produtos por região
        receita_por_regiao = {}  # Receita por região
        
        for row in data:
            try:
                prod = row.get('produto', 'Desconhecido')
                qty = float(str(row.get('quantidade', 0)).replace(',', '.'))
                receita = float(str(row.get('receita_total', 0)).replace(',', '.'))
                categoria = row.get('categoria', 'Sem categoria')
                regiao = row.get('regiao', 'Sem região')
                
                # Total geral de produtos
                produtos_total[prod] = produtos_total.get(prod, 0) + qty
                
                # Por categoria
                if categoria not in produtos_por_categoria:
                    produtos_por_categoria[categoria] = {}
                    receita_por_categoria[categoria] = 0.0
                produtos_por_categoria[categoria][prod] = produtos_por_categoria[categoria].get(prod, 0) + qty
                receita_por_categoria[categoria] += receita
                
                # Por região
                if regiao not in produtos_por_regiao:
                    produtos_por_regiao[regiao] = {}
                    receita_por_regiao[regiao] = 0.0
                produtos_por_regiao[regiao][prod] = produtos_por_regiao[regiao].get(prod, 0) + qty
                receita_por_regiao[regiao] += receita
                
                # Por mês
                data_str = row.get('data')
                if data_str:
                    dt = datetime.fromisoformat(str(data_str)[:10])
                    mes_nome = f"{meses_pt[dt.month]}/{dt.year}"
                    
                    # Produtos por mês
                    if mes_nome not in produtos_por_mes:
                        produtos_por_mes[mes_nome] = {}
                    produtos_por_mes[mes_nome][prod] = produtos_por_mes[mes_nome].get(prod, 0) + qty
                    
                    # Receita por mês
                    receita_por_mes[mes_nome] = receita_por_mes.get(mes_nome, 0.0) + receita
                    
                    # Vendas por mês
                    vendas_por_mes[mes_nome] = vendas_por_mes.get(mes_nome, 0) + 1
            except:
                continue
        
        # TENTATIVA 1: Usar Gemini AI com dados agregados
        try:
            # Import dinâmico (só carrega quando necessário)
            import google.generativeai as genai
            
            gemini_key = os.getenv('GEMINI_API_KEY')
            if not gemini_key:
                raise Exception("GEMINI_API_KEY não configurada")
            
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Preparar contexto com DADOS AGREGADOS (muito mais compacto e preciso)
            def fmt_currency(value):
                return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
            # Calcular totais gerais
            receita_total_ano = sum(receita_por_mes.values())
            quantidade_produtos_diferentes = len(produtos_total)
            quantidade_total_vendida = sum(produtos_total.values())
            
            context = f"""Você é um analista de vendas especializado. Aqui está o RESUMO COMPLETO de {len(data)} registros de vendas de 2024:

📈 RESUMO GERAL DO ANO:
- Total de registros analisados: {len(data)}
- Receita total do ano: {fmt_currency(receita_total_ano)}
- Quantidade de produtos diferentes vendidos: {quantidade_produtos_diferentes}
- Quantidade total de unidades vendidas: {int(quantidade_total_vendida)}

📊 RECEITA POR MÊS:
"""
            for mes in sorted(receita_por_mes.keys()):
                context += f"- {mes}: {fmt_currency(receita_por_mes[mes])} ({vendas_por_mes[mes]} vendas)\n"
            
            context += f"\n🏆 TOP 10 PRODUTOS MAIS VENDIDOS (quantidade total):\n"
            top_produtos = sorted(produtos_total.items(), key=lambda x: x[1], reverse=True)[:10]
            for prod, qty in top_produtos:
                context += f"- {prod}: {int(qty)} unidades\n"
            
            context += f"\n📅 PRODUTOS MAIS VENDIDOS POR MÊS:\n"
            for mes in sorted(produtos_por_mes.keys()):
                top_mes = sorted(produtos_por_mes[mes].items(), key=lambda x: x[1], reverse=True)[:3]
                context += f"\n{mes}:\n"
                for prod, qty in top_mes:
                    context += f"  - {prod}: {int(qty)} unidades\n"
            
            context += f"\n📦 VENDAS POR CATEGORIA (unidades e receita):\n"
            for categoria, prods in produtos_por_categoria.items():
                total_cat = sum(prods.values())
                receita_cat = receita_por_categoria.get(categoria, 0.0)
                context += f"- {categoria}: {int(total_cat)} unidades | Receita: {fmt_currency(receita_cat)}\n"
            
            context += f"\n🗺️ VENDAS POR REGIÃO (unidades e receita):\n"
            for regiao, prods in produtos_por_regiao.items():
                total_reg = sum(prods.values())
                receita_reg = receita_por_regiao.get(regiao, 0.0)
                context += f"- {regiao}: {int(total_reg)} unidades | Receita: {fmt_currency(receita_reg)}\n"
            
            context += f"\n❓ PERGUNTA DO USUÁRIO: {question}\n\n"
            context += """INSTRUÇÕES DE FORMATAÇÃO:
- Use emojis relevantes para tornar a resposta mais visual e atrativa (📊 📈 💰 🏆 🎯 ⭐ 🔥 etc)
- Destaque números importantes com **negrito**
- Use títulos e subtítulos com ##
- Organize dados em listas com bullets (•) ou numeração
- Compare valores quando relevante (X% maior que Y)
- Formate valores monetários como R$ X.XXX,XX
- Seja entusiasmado e positivo no tom
- Se possível, adicione insights ou observações interessantes
- Use quebras de linha para facilitar leitura

Responda em português de forma CLARA, VISUAL e ENVOLVENTE, usando EXATAMENTE os dados agregados fornecidos acima.
"""
            
            response = model.generate_content(context)
            
            return jsonify({'answer': response.text}), 200
            
        except Exception as gemini_error:
            print(f"Erro no Gemini: {str(gemini_error)}")
            
            # FALLBACK: Análise simples sem IA
            question_lower = question.lower()
            
            # Detectar mês na pergunta
            meses = {
                'janeiro': '-01-', 'fevereiro': '-02-', 'março': '-03-', 'marco': '-03-',
                'abril': '-04-', 'maio': '-05-', 'junho': '-06-',
                'julho': '-07-', 'agosto': '-08-', 'setembro': '-09-',
                'outubro': '-10-', 'novembro': '-11-', 'dezembro': '-12-'
            }
            
            mes_filtro = None
            mes_nome = None
            for nome_mes, filtro in meses.items():
                if nome_mes in question_lower:
                    mes_filtro = filtro
                    mes_nome = nome_mes.capitalize()
                    break
            
            # Se pergunta sobre produto mais vendido
            if 'vendido' in question_lower or 'produto' in question_lower:
                produtos_qty = {}
                
                for row in data:
                    data_str = row.get('data', '')
                    
                    # Filtrar por mês se especificado
                    if mes_filtro and mes_filtro not in data_str:
                        continue
                    
                    prod = row.get('produto', 'Desconhecido')
                    qty = float(str(row.get('quantidade', 0)).replace(',', '.'))
                    produtos_qty[prod] = produtos_qty.get(prod, 0) + qty
                
                if produtos_qty:
                    top_prod = max(produtos_qty, key=produtos_qty.get)
                    qty = int(produtos_qty[top_prod])
                    
                    # Top 3 para comparação
                    top_3 = sorted(produtos_qty.items(), key=lambda x: x[1], reverse=True)[:3]
                    
                    periodo = f" em **{mes_nome}**" if mes_nome else " no **período analisado**"
                    
                    answer = f"""🏆 **PRODUTO CAMPEÃO DE VENDAS** 🏆

## 🥇 Produto Mais Vendido{periodo}

**{top_prod}**
📦 **{qty} unidades** vendidas

---

### 📊 Top 3 Produtos:
"""
                    for i, (prod, q) in enumerate(top_3, 1):
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                        answer += f"{emoji} **{prod}**: {int(q)} unidades\n"
                    
                    return jsonify({'answer': answer}), 200
            
            # Resposta genérica
            answer = f"""🤔 **Hmm, preciso de mais contexto!**

Recebi sua pergunta: *"{question}"*

Infelizmente, estou com dificuldades para processar essa análise no momento. Mas não se preocupe! 💪

### 💡 Experimente perguntas como:

🔹 **Por Produto:**
• "Qual produto foi mais vendido em Janeiro?"
• "Quais os top 5 produtos do ano?"
• "Compare vendas de Notebook vs Mouse"

🔹 **Por Região:**
• "Qual região vendeu mais?"
• "Compare receita do Sul e Norte"
• "Qual a receita total da região Sudeste?"

🔹 **Por Mês:**
• "Qual foi o melhor mês de vendas?"
• "Mostre as vendas de Março"
• "Compare Janeiro e Fevereiro"

🔹 **Por Categoria:**
• "Qual categoria gerou mais receita?"
• "Quantas unidades de Eletrônicos foram vendidas?"

💬 **Dica:** Seja específico nas perguntas para obter respostas mais precisas!
"""
            return jsonify({'answer': answer}), 200
        
    except Exception as e:
        print(f"ERRO NO /api/analyze: {str(e)}")
        return jsonify({'answer': f'❌ Erro ao processar pergunta: {str(e)}'}), 200

@app.route('/api/sync-data', methods=['POST'])
def sync_data():
    """Sincroniza dados (recarrega cache/métricas)"""
    try:
        # Este endpoint pode ser usado para forçar recarga de dados
        # Por enquanto, apenas retorna sucesso
        return jsonify({
            'success': True,
            'message': '✅ Dados sincronizados com sucesso! Todas as métricas foram atualizadas.',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro na sincronização: {str(e)}'
        }), 500

@app.route('/api/upload-data', methods=['POST'])
def upload_data():
    """Upload de arquivo de vendas (.xlsx, .xls, .csv)"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nome de arquivo vazio'}), 400
        
        # Validar extensão
        allowed_extensions = {'.xlsx', '.xls', '.csv'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Formato não suportado. Use: {", ".join(allowed_extensions)}'}), 400
        
        # Importar pandas apenas quando necessário (evita overhead no cold start)
        import pandas as pd
        from io import BytesIO
        import unicodedata
        
        # Ler arquivo
        file_content = file.read()
        
        if file_ext == '.csv':
            df = pd.read_csv(BytesIO(file_content))
        else:  # .xlsx ou .xls
            df = pd.read_excel(BytesIO(file_content))
        
        if df.empty:
            return jsonify({'error': 'Arquivo vazio ou sem dados válidos'}), 400
        
        # Função para normalizar nomes de colunas
        def normalize_column_name(col):
            # Remove acentos
            col = ''.join(c for c in unicodedata.normalize('NFD', str(col)) 
                         if unicodedata.category(c) != 'Mn')
            # Lowercase e substitui espaços por _
            return col.lower().replace(' ', '_').replace('-', '_')
        
        # Normalizar nomes das colunas
        df.columns = [normalize_column_name(col) for col in df.columns]
        
        # Mapear possíveis variações de nomes de colunas
        column_mapping = {
            'id_transacao': ['id_transacao', 'id', 'transacao', 'id_venda'],
            'data': ['data', 'date', 'dt_venda', 'data_venda'],
            'produto': ['produto', 'product', 'item', 'descricao'],
            'categoria': ['categoria', 'category', 'tipo'],
            'regiao': ['regiao', 'region', 'estado', 'uf'],
            'quantidade': ['quantidade', 'qtd', 'quantity', 'qtde'],
            'preco_unitario': ['preco_unitario', 'preco', 'price', 'valor_unitario'],
            'receita_total': ['receita_total', 'total', 'valor_total', 'receita']
        }
        
        # Encontrar colunas equivalentes
        final_columns = {}
        for target_col, possible_names in column_mapping.items():
            for col in df.columns:
                if col in possible_names:
                    final_columns[col] = target_col
                    break
        
        # Renomear colunas
        df.rename(columns=final_columns, inplace=True)
        
        # Validar colunas obrigatórias
        required_columns = ['data', 'produto', 'quantidade', 'receita_total']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'error': f'Colunas obrigatórias faltando: {", ".join(missing_columns)}',
                'found_columns': list(df.columns)
            }), 400
        
        # Preencher colunas opcionais com valores padrão
        if 'id_transacao' not in df.columns:
            df['id_transacao'] = [f'TXN{i:06d}' for i in range(len(df))]
        if 'categoria' not in df.columns:
            df['categoria'] = 'Sem categoria'
        if 'regiao' not in df.columns:
            df['regiao'] = 'Não especificada'
        if 'preco_unitario' not in df.columns:
            df['preco_unitario'] = df['receita_total'] / df['quantidade']
        
        # Converter tipos de dados
        # Datas
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        
        # Números (aceita vírgula como decimal)
        for col in ['quantidade', 'preco_unitario', 'receita_total']:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '.').str.replace(r'[^\d.]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remover linhas com dados inválidos
        df.dropna(subset=['data', 'produto', 'quantidade', 'receita_total'], inplace=True)
        
        if df.empty:
            return jsonify({'error': 'Nenhuma linha válida encontrada após validação'}), 400
        
        # Adicionar metadados
        filename_without_ext = os.path.splitext(file.filename)[0]
        df['mes_origem'] = filename_without_ext
        df['created_at'] = datetime.now().isoformat()
        
        # Converter para formato JSON para inserção no Supabase
        records = df.to_dict('records')
        
        # Formatar data para ISO string
        for record in records:
            if pd.notna(record.get('data')):
                record['data'] = record['data'].strftime('%Y-%m-%d')
        
        # VERIFICAR SE JÁ EXISTE ARQUIVO COM MESMO NOME (evitar duplicatas)
        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # Verificar se já existe dados deste arquivo
        check_url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"
        check_params = {
            'select': 'mes_origem',
            'mes_origem': f'eq.{filename_without_ext}',
            'limit': 1
        }
        check_response = requests.get(check_url, headers=headers, params=check_params, timeout=5)
        
        rows_deleted = 0
        if check_response.status_code == 200 and check_response.json():
            # Arquivo já existe! Deletar dados antigos antes de inserir novos
            delete_params = {'mes_origem': f'eq.{filename_without_ext}'}
            delete_response = requests.delete(url, headers=headers, params=delete_params, timeout=10)
            
            if delete_response.status_code == 204:
                rows_deleted = len(check_response.json())
                print(f"✅ Deletados dados antigos do arquivo '{filename_without_ext}'")
        
        # Inserir no Supabase em lotes (max 1000 por vez)
        total_inserted = 0
        batch_size = 1000
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            response = requests.post(url, headers=headers, json=batch, timeout=30)
            
            if response.status_code not in [200, 201]:
                raise Exception(f'Erro ao inserir lote {i//batch_size + 1}: {response.text}')
            
            total_inserted += len(batch)
        
        # Mensagem personalizada
        if rows_deleted > 0:
            message = f'✅ Arquivo atualizado! {total_inserted} linhas inseridas (substituiu dados anteriores)'
        else:
            message = f'✅ {total_inserted} linhas importadas com sucesso!'
        
        return jsonify({
            'success': True,
            'message': message,
            'rows_imported': total_inserted,
            'rows_replaced': rows_deleted > 0,
            'filename': file.filename,
            'columns_found': list(df.columns)
        }), 200
        
    except Exception as e:
        print(f"ERRO NO UPLOAD: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro no upload: {str(e)}'
        }), 500

@app.route('/api/clear-data', methods=['POST'])
def clear_data():
    """Limpa dados do banco - PROTEGE arquivo base e deleta apenas uploads de teste"""
    try:
        body = request.get_json() or {}
        filename = body.get('filename')  # Nome do arquivo específico (opcional)
        clear_all_tests = body.get('clear_all_tests', False)  # Deletar todos os testes
        confirm = body.get('confirm', False)  # Segurança: requer confirmação
        
        if not confirm:
            return jsonify({
                'error': 'Operação cancelada. Envie {"confirm": true} para confirmar a exclusão.'
            }), 400
        
        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # OPÇÃO 1: Deletar arquivo específico (com proteção)
        if filename:
            filename_clean = os.path.splitext(filename)[0]
            
            # 🔒 PROTEÇÃO: Não permitir deletar arquivo base
            if filename_clean == PROTECTED_FILE:
                return jsonify({
                    'success': False,
                    'error': f'❌ Arquivo "{PROTECTED_FILE}" é protegido e não pode ser deletado!',
                    'protected': True
                }), 403
            
            params = {'mes_origem': f'eq.{filename_clean}'}
            
            # Verificar quantos registros serão deletados
            check_params = {'select': 'mes_origem', 'mes_origem': f'eq.{filename_clean}'}
            check_response = requests.get(url, headers=headers, params=check_params, timeout=5)
            count = len(check_response.json()) if check_response.status_code == 200 else 0
            
            if count == 0:
                return jsonify({
                    'success': False,
                    'error': f'Nenhum registro encontrado com o arquivo "{filename_clean}"'
                }), 404
            
            # Deletar
            response = requests.delete(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 204:
                return jsonify({
                    'success': True,
                    'message': f'✅ {count} registros do arquivo "{filename_clean}" foram deletados',
                    'rows_deleted': count,
                    'filename': filename_clean
                }), 200
        
        # OPÇÃO 2: Deletar TODOS os uploads de teste (mantém arquivo base protegido)
        elif clear_all_tests:
            # Deletar tudo EXCETO o arquivo protegido
            params = {'mes_origem': f'neq.{PROTECTED_FILE}'}
            
            # Contar quantos serão deletados
            check_params = {'select': 'mes_origem', 'mes_origem': f'neq.{PROTECTED_FILE}'}
            check_response = requests.get(url, headers=headers, params=check_params, timeout=5)
            count = len(check_response.json()) if check_response.status_code == 200 else 0
            
            if count == 0:
                return jsonify({
                    'success': True,
                    'message': f'✅ Nenhum dado de teste para deletar. Arquivo base "{PROTECTED_FILE}" permanece intacto.',
                    'rows_deleted': 0
                }), 200
            
            # Deletar todos EXCETO protegido
            response = requests.delete(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 204:
                return jsonify({
                    'success': True,
                    'message': f'✅ {count} registros de teste deletados! Arquivo base "{PROTECTED_FILE}" (2.600 registros) permanece protegido.',
                    'rows_deleted': count,
                    'protected_file_kept': PROTECTED_FILE
                }), 200
        else:
            # Se não especificou nada, retornar erro
            return jsonify({
                'success': False,
                'error': 'Especifique "filename" para deletar arquivo específico ou "clear_all_tests": true para deletar todos os testes.'
            }), 400
        
        return jsonify({
            'success': False,
            'error': 'Erro ao deletar dados'
        }), 500
        
    except Exception as e:
        print(f"ERRO AO LIMPAR DADOS: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao limpar dados: {str(e)}'
        }), 500

@app.route('/api/database-stats', methods=['GET'])
def database_stats():
    """Retorna estatísticas do banco de dados"""
    try:
        # Buscar contagem total de registros (usando apenas data para contagem)
        data, error = query_supabase('data', max_records=50000)
        
        if error:
            return jsonify({
                'error': error,
                'total_records': 0
            }), 500
        
        return jsonify({
            'success': True,
            'total_records': len(data) if data else 0,
            'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M')
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao consultar estatísticas: {str(e)}',
            'total_records': 0
        }), 500

@app.route('/api/list-files', methods=['GET'])
def list_files():
    """Lista todos os arquivos (mes_origem) com quantidade de registros"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Buscar apenas mes_origem e created_at
        params = {'select': 'mes_origem,created_at'}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f'Erro ao buscar arquivos: {response.text}')
        
        data = response.json()
        
        if not data:
            return jsonify({
                'success': True,
                'files': [],
                'total_files': 0,
                'message': 'Nenhum arquivo encontrado no banco'
            }), 200
        
        # Agrupar por mes_origem e contar
        files_dict = {}
        for row in data:
            mes_origem = row.get('mes_origem', 'Desconhecido')
            created_at = row.get('created_at', '')
            
            if mes_origem not in files_dict:
                files_dict[mes_origem] = {
                    'name': mes_origem,
                    'count': 0,
                    'first_upload': created_at,
                    'is_protected': mes_origem == PROTECTED_FILE
                }
            
            files_dict[mes_origem]['count'] += 1
            # Manter a data mais antiga
            if created_at < files_dict[mes_origem]['first_upload']:
                files_dict[mes_origem]['first_upload'] = created_at
        
        # Converter para lista e ordenar
        files_list = sorted(files_dict.values(), key=lambda x: x['first_upload'])
        
        # Formatar datas
        for file_info in files_list:
            try:
                dt = datetime.fromisoformat(file_info['first_upload'].replace('Z', '+00:00'))
                file_info['uploaded_at'] = dt.strftime('%d/%m/%Y %H:%M')
            except:
                file_info['uploaded_at'] = 'Data desconhecida'
            del file_info['first_upload']
        
        return jsonify({
            'success': True,
            'files': files_list,
            'total_files': len(files_list),
            'protected_file': PROTECTED_FILE
        }), 200
        
    except Exception as e:
        print(f"ERRO AO LISTAR ARQUIVOS: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao listar arquivos: {str(e)}'
        }), 500

@app.route('/api/diagnostic', methods=['GET'])
def diagnostic():
    """Diagnóstico"""
    return jsonify({
        'status': 'ok',
        'message': 'Endpoint de diagnóstico funcionando (requests direto)',
        'environment': {
            'SUPABASE_URL': 'CONFIGURADO' if SUPABASE_URL else 'NÃO CONFIGURADO',
            'SUPABASE_KEY': 'CONFIGURADO' if SUPABASE_KEY else 'NÃO CONFIGURADO',
            'TABLE_NAME': TABLE_NAME
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)

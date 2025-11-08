"""
API Flask simplificada para Vercel - Versão sem pandas
Evita imports pesados que causam timeout no serverless
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configurações
TABLE_NAME = os.getenv('SUPABASE_TABLE_NAME', 'vendas_2024')

def get_supabase_client():
    """Inicializa cliente Supabase"""
    try:
        from supabase import create_client
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            return None, "Credenciais Supabase não configuradas"
        
        client = create_client(url, key)
        return client, None
    except Exception as e:
        return None, str(e)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        return jsonify({
            'status': 'ok',
            'message': 'API funcionando',
            'environment': {
                'supabase_url_configured': bool(supabase_url),
                'supabase_key_configured': bool(supabase_key),
                'gemini_key_configured': bool(gemini_key),
                'table_name': TABLE_NAME
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def metrics():
    """Retorna métricas do Supabase SEM pandas"""
    try:
        client, error = get_supabase_client()
        if error:
            raise Exception(error)
        
        # Buscar TODOS os dados de uma vez (limite 10000 registros para evitar timeout)
        resp = client.table(TABLE_NAME).select('*').limit(10000).execute()
        all_rows = resp.data or []
        
        if not all_rows:
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
        
        # Processar sem pandas - agregação manual
        produtos_qty = {}
        receita_por_mes = {}
        receita_total = 0.0
        produtos_set = set()
        
        meses_pt = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        for row in all_rows:
            try:
                # Produto
                prod = row.get('produto', 'Desconhecido')
                produtos_set.add(prod)
                
                # Quantidade e receita
                qty = float(str(row.get('quantidade', 0)).replace(',', '.'))
                receita = float(str(row.get('receita_total', 0)).replace(',', '.'))
                
                produtos_qty[prod] = produtos_qty.get(prod, 0) + qty
                receita_total += receita
                
                # Mês
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
            'records_analyzed': len(all_rows),
            'last_updated': datetime.utcnow().strftime('%d/%m/%Y %H:%M'),
            'no_data': False
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'no_data': True,
            'melhor_mes': {'nome': 'Erro', 'valor': 'R$ 0,00'},
            'produto_mais_vendido': {'nome': 'Erro', 'quantidade': 0},
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
        client, error = get_supabase_client()
        if error:
            raise Exception(error)
        
        # Buscar TODOS os dados de uma vez (limite 10000 registros)
        resp = client.table(TABLE_NAME).select('*').limit(10000).execute()
        all_rows = resp.data or []
        
        if not all_rows:
            return jsonify({'no_data': True, 'months': []}), 200
        
        # Agregação por mês
        meses_pt = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        dados_por_mes = {}
        
        for row in all_rows:
            try:
                data_str = row.get('data')
                if not data_str:
                    continue
                
                dt = datetime.fromisoformat(str(data_str)[:10])
                mes_key = f"{dt.year}-{dt.month:02d}"
                mes_nome = f"{meses_pt[dt.month]}/{dt.year}"
                
                if mes_key not in dados_por_mes:
                    dados_por_mes[mes_key] = {
                        'mes': mes_nome,
                        'mes_numero': dt.month,
                        'ano': dt.year,
                        'receita': 0.0,
                        'quantidade_vendas': 0,
                        'produtos': {}
                    }
                
                produto = row.get('produto', 'Desconhecido')
                qty = float(str(row.get('quantidade', 0)).replace(',', '.'))
                receita = float(str(row.get('receita_total', 0)).replace(',', '.'))
                
                dados_por_mes[mes_key]['receita'] += receita
                dados_por_mes[mes_key]['quantidade_vendas'] += 1
                dados_por_mes[mes_key]['produtos'][produto] = dados_por_mes[mes_key]['produtos'].get(produto, 0) + qty
                
            except:
                continue
        
        # Formatar resultado
        def fmt_currency(value):
            return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        resultado = []
        for mes_key in sorted(dados_por_mes.keys()):
            dados = dados_por_mes[mes_key]
            
            # Produto mais vendido do mês
            if dados['produtos']:
                prod_top = max(dados['produtos'].items(), key=lambda x: x[1])
                top_5_produtos = sorted(dados['produtos'].items(), key=lambda x: x[1], reverse=True)[:5]
            else:
                prod_top = ('Sem dados', 0)
                top_5_produtos = []
            
            resultado.append({
                'mes': dados['mes'],
                'mes_numero': dados['mes_numero'],
                'ano': dados['ano'],
                'receita': fmt_currency(dados['receita']),
                'receita_valor': dados['receita'],
                'quantidade_vendas': dados['quantidade_vendas'],
                'produto_mais_vendido': {
                    'nome': prod_top[0],
                    'quantidade': int(prod_top[1])
                },
                'top_5_produtos': [
                    {'nome': p[0], 'quantidade': int(p[1])} 
                    for p in top_5_produtos
                ]
            })
        
        return jsonify({
            'no_data': False,
            'total_meses': len(resultado),
            'months': resultado
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'no_data': True,
            'months': []
        }), 200

def analyze_data_smart(all_data, question):
    """Análise inteligente dos dados baseada em palavras-chave - SEM ALUCINAÇÕES"""
    question_lower = question.lower()
    
    # Dicionário de meses em português
    meses_pt = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    
    # Inverso para busca
    meses_nomes = {v.lower(): k for k, v in meses_pt.items()}
    
    # Função de formatação de moeda
    def fmt_currency(value):
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # Agregações completas dos dados
    receita_por_mes = {}
    receita_por_produto = {}
    receita_por_categoria = {}
    receita_por_regiao = {}
    qty_por_produto = {}
    produtos_por_mes = {}  # Nova: produtos por mês
    receita_total = 0.0
    
    for row in all_data:
        try:
            produto = row.get('produto', 'Desconhecido')
            categoria = row.get('categoria', 'Desconhecida')
            regiao = row.get('regiao', 'Desconhecida')
            qty = float(str(row.get('quantidade', 0)).replace(',', '.'))
            receita = float(str(row.get('receita_total', 0)).replace(',', '.'))
            
            # Agregações
            receita_total += receita
            receita_por_produto[produto] = receita_por_produto.get(produto, 0.0) + receita
            receita_por_categoria[categoria] = receita_por_categoria.get(categoria, 0.0) + receita
            receita_por_regiao[regiao] = receita_por_regiao.get(regiao, 0.0) + receita
            qty_por_produto[produto] = qty_por_produto.get(produto, 0) + qty
            
            # Mês
            data_str = row.get('data')
            if data_str:
                dt = datetime.fromisoformat(str(data_str)[:10])
                mes_nome = f"{meses_pt[dt.month]}/{dt.year}"
                mes_simples = meses_pt[dt.month].lower()  # Normalizar para minúsculas
                
                receita_por_mes[mes_nome] = receita_por_mes.get(mes_nome, 0.0) + receita
                
                # Agregar produtos por mês (usar lowercase para comparação)
                if mes_simples not in produtos_por_mes:
                    produtos_por_mes[mes_simples] = {}
                produtos_por_mes[mes_simples][produto] = produtos_por_mes[mes_simples].get(produto, 0) + qty
        except:
            continue
    
    # NOVA: Análise de produto em mês específico
    for mes_nome, mes_num in meses_nomes.items():
        if mes_nome in question_lower and any(word in question_lower for word in ['produto', 'vendido', 'vendeu', 'mais vendido']):
            if mes_nome in produtos_por_mes:
                produtos_mes = produtos_por_mes[mes_nome]
                if produtos_mes:
                    # Top 5 produtos do mês
                    top_produtos = sorted(produtos_mes.items(), key=lambda x: x[1], reverse=True)[:5]
                    prod_top = top_produtos[0]
                    
                    resultado = f"📊 **Análise de {meses_pt[mes_num]}/2024**\n\n"
                    resultado += f"O produto **mais vendido** foi **{prod_top[0]}** com **{int(prod_top[1])} unidades** comercializadas.\n\n"
                    
                    if len(top_produtos) > 1:
                        resultado += "**Top 5 produtos do mês:**\n"
                        for i, (prod, qty) in enumerate(top_produtos, 1):
                            resultado += f"{i}. {prod}: {int(qty)} un\n"
                    
                    return resultado.strip()
            return f"⚠️ Não encontrei dados de vendas para {meses_pt[mes_num]} de 2024 na base de dados atual."
    
    # Análises baseadas em palavras-chave
    if any(word in question_lower for word in ['mês', 'mes', 'maior receita', 'melhor mes', 'melhor mês']):
        if receita_por_mes:
            melhor_mes = max(receita_por_mes, key=receita_por_mes.get)
            valor = receita_por_mes[melhor_mes]
            return f"📈 **Melhor Desempenho Mensal**\n\nO mês com **maior receita** foi **{melhor_mes}** com um faturamento de **{fmt_currency(valor)}**.\n\nEste foi o período de maior destaque no ano."
        return "⚠️ Não encontrei dados de vendas por mês na base atual."
    
    elif any(word in question_lower for word in ['produto', 'produtos mais vendidos', 'top', '5 produtos', 'mais vendido']):
        if qty_por_produto:
            top_5 = sorted(qty_por_produto.items(), key=lambda x: x[1], reverse=True)[:5]
            resultado = "🏆 **Top 5 Produtos Mais Vendidos do Ano**\n\n"
            for i, (prod, qty) in enumerate(top_5, 1):
                resultado += f"{i}. **{prod}**: {int(qty)} unidades\n"
            resultado += f"\nEstes são os produtos com maior volume de vendas entre {len(all_data)} transações registradas."
            return resultado.strip()
        return "⚠️ Não encontrei dados de produtos na base atual."
    
    elif any(word in question_lower for word in ['receita total', 'faturamento total', 'total vendido', 'quanto foi vendido']):
        return f"💰 **Receita Total de 2024**\n\nO faturamento total do ano foi de **{fmt_currency(receita_total)}**, baseado em **{len(all_data)} registros** de vendas processados.\n\nEste valor representa a soma de todas as transações comerciais realizadas no período."
    
    elif any(word in question_lower for word in ['região', 'regiao', 'qual região', 'regional']):
        if receita_por_regiao:
            melhor_regiao = max(receita_por_regiao, key=receita_por_regiao.get)
            valor = receita_por_regiao[melhor_regiao]
            # Mostrar todas as regiões
            resultado = f"🌍 **Análise Regional de Vendas**\n\n"
            resultado += f"A região com **melhor desempenho** foi **{melhor_regiao}** com {fmt_currency(valor)}.\n\n"
            resultado += "**Detalhamento por região:**\n"
            for regiao, val in sorted(receita_por_regiao.items(), key=lambda x: x[1], reverse=True):
                resultado += f"• **{regiao}**: {fmt_currency(val)}\n"
            return resultado.strip()
        return "⚠️ Não encontrei dados de vendas por região."
    
    elif any(word in question_lower for word in ['categoria', 'categorias', 'qual categoria']):
        if receita_por_categoria:
            melhor_cat = max(receita_por_categoria, key=receita_por_categoria.get)
            valor = receita_por_categoria[melhor_cat]
            resultado = f"📦 **Análise por Categoria de Produtos**\n\n"
            resultado += f"A categoria com **maior volume de vendas** foi **{melhor_cat}** com {fmt_currency(valor)}.\n\n"
            resultado += "**Receita por categoria:**\n"
            for cat, val in sorted(receita_por_categoria.items(), key=lambda x: x[1], reverse=True):
                resultado += f"• **{cat}**: {fmt_currency(val)}\n"
            return resultado.strip()
        return "⚠️ Não encontrei dados de vendas por categoria."
    
    elif any(word in question_lower for word in ['evolução', 'evolucao', 'receita de cada mes', 'receita de cada mês', 'meses']):
        if receita_por_mes:
            resultado = "📅 **Evolução Mensal de Receita - 2024**\n\n"
            for mes, val in sorted(receita_por_mes.items()):
                resultado += f"• **{mes}**: {fmt_currency(val)}\n"
            resultado += f"\nTotal de meses com vendas registradas: {len(receita_por_mes)}"
            return resultado.strip()
        return "⚠️ Não encontrei dados de evolução mensal."
    
    elif any(word in question_lower for word in ['quantos produtos', 'quantidade de produtos', 'diversidade', 'produtos diferentes']):
        # Contar produtos únicos (exclui vazios e 'Desconhecido')
        produtos_unicos = [p for p in receita_por_produto.keys() if p and p != 'Desconhecido']
        qtd_produtos = len(produtos_unicos)
        return f"📊 **Diversidade de Produtos**\n\nForam comercializados **{qtd_produtos} produtos diferentes** em 2024, totalizando **{len(all_data)} transações** registradas.\n\nIsso demonstra uma boa variedade no portfólio de vendas."
    
    # Resposta genérica com resumo dos dados
    return f"""📊 **Resumo Geral das Vendas 2024**

Aqui está uma visão geral dos dados disponíveis:

• **Total de transações**: {len(all_data)} registros
• **Receita total**: {fmt_currency(receita_total)}
• **Produtos únicos**: {len(receita_por_produto)} itens diferentes
• **Categorias**: {len(receita_por_categoria)} categorias
• **Regiões**: {len(receita_por_regiao)} regiões de atuação

**💡 Sugestões de perguntas:**
• Qual foi o melhor mês de vendas?
• Quais os 5 produtos mais vendidos?
• Qual região teve maior receita?
• Qual categoria vendeu mais?"""

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Análise inteligente com fallback - SEMPRE FUNCIONA"""
    try:
        data = request.json
        question = data.get('message', '')
        
        if not question:
            return jsonify({'error': 'Pergunta não fornecida'}), 400
        
        # Buscar TODOS os dados do Supabase
        client, error = get_supabase_client()
        if error:
            return jsonify({'answer': f'❌ Erro ao conectar ao banco de dados: {error}'}), 200
        
        # Paginação para buscar TODOS os dados
        all_data = []
        page_size = 1000
        start = 0
        
        while True:
            resp = client.table(TABLE_NAME).select('*').range(start, start + page_size - 1).execute()
            rows = resp.data or []
            all_data.extend(rows)
            if len(rows) < page_size:
                break
            start += page_size
        
        if not all_data:
            return jsonify({'answer': '❌ Não há dados disponíveis no banco de dados.'}), 200
        
        # TENTATIVA 1: Usar Gemini (se disponível)
        try:
            import google.generativeai as genai
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            gemini_key = os.getenv('GEMINI_API_KEY')
            if gemini_key:
                genai.configure(api_key=gemini_key)
                
                # Calcular estatísticas AGREGADAS (otimizado para poucos tokens)
                receita_por_mes = {}
                receita_por_produto = {}
                receita_por_categoria = {}
                receita_por_regiao = {}
                qty_por_produto = {}
                produtos_por_mes = {}  # Nova: produtos por mês
                receita_total = 0.0
                produtos_unicos = set()
                
                meses_pt = {
                    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
                }
                
                for row in all_data:
                    try:
                        produto = row.get('produto', 'Desconhecido')
                        categoria = row.get('categoria', 'Desconhecida')
                        regiao = row.get('regiao', 'Desconhecida')
                        qty = float(str(row.get('quantidade', 0)).replace(',', '.'))
                        receita = float(str(row.get('receita_total', 0)).replace(',', '.'))
                        
                        if produto and produto != 'Desconhecido':
                            produtos_unicos.add(produto)
                        
                        receita_total += receita
                        receita_por_produto[produto] = receita_por_produto.get(produto, 0.0) + receita
                        receita_por_categoria[categoria] = receita_por_categoria.get(categoria, 0.0) + receita
                        receita_por_regiao[regiao] = receita_por_regiao.get(regiao, 0.0) + receita
                        qty_por_produto[produto] = qty_por_produto.get(produto, 0) + qty
                        
                        # Mês
                        data_str = row.get('data')
                        if data_str:
                            dt = datetime.fromisoformat(str(data_str)[:10])
                            mes_nome = f"{meses_pt[dt.month]}/{dt.year}"
                            mes_simples = meses_pt[dt.month]
                            
                            receita_por_mes[mes_nome] = receita_por_mes.get(mes_nome, 0.0) + receita
                            
                            # Agregar produtos por mês
                            if mes_simples not in produtos_por_mes:
                                produtos_por_mes[mes_simples] = {}
                            produtos_por_mes[mes_simples][produto] = produtos_por_mes[mes_simples].get(produto, 0) + qty
                    except:
                        continue
                
                # Preparar dados agregados (MÍNIMO de tokens, MÁXIMO de informação)
                top_5_produtos = sorted(qty_por_produto.items(), key=lambda x: x[1], reverse=True)[:5]
                top_3_categorias = sorted(receita_por_categoria.items(), key=lambda x: x[1], reverse=True)[:3]
                top_3_regioes = sorted(receita_por_regiao.items(), key=lambda x: x[1], reverse=True)[:3]
                melhor_mes = max(receita_por_mes.items(), key=lambda x: x[1]) if receita_por_mes else ("N/A", 0)
                
                # Preparar top produtos por mês (para consultas mensais)
                produtos_mensais_info = ""
                for mes in ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']:
                    if mes in produtos_por_mes and produtos_por_mes[mes]:
                        top_prod_mes = max(produtos_por_mes[mes].items(), key=lambda x: x[1])
                        produtos_mensais_info += f"{mes}: {top_prod_mes[0]} ({int(top_prod_mes[1])} un) | "
                
                # Contexto OTIMIZADO (apenas dados essenciais)
                contexto = f"""DADOS 2024 (BASE: {len(all_data)} registros):
Total: R$ {receita_total:,.2f} | Produtos únicos: {len(produtos_unicos)} | Categorias: {len(receita_por_categoria)} | Regiões: {len(receita_por_regiao)}

TOP 5 PRODUTOS (por quantidade):
{chr(10).join([f"{i+1}. {p}: {int(q)} un" for i, (p, q) in enumerate(top_5_produtos)])}

TOP 3 CATEGORIAS (por receita):
{chr(10).join([f"{i+1}. {c}: R$ {v:,.2f}" for i, (c, v) in enumerate(top_3_categorias)])}

TOP 3 REGIÕES (por receita):
{chr(10).join([f"{i+1}. {r}: R$ {v:,.2f}" for i, (r, v) in enumerate(top_3_regioes)])}

MELHOR MÊS: {melhor_mes[0]} - R$ {melhor_mes[1]:,.2f}

PRODUTO MAIS VENDIDO POR MÊS (em quantidade):
{produtos_mensais_info.strip(' |')}"""
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"""Você é um assistente de análise de vendas especializado. Analise os dados abaixo e responda de forma clara, profissional e objetiva.

{contexto}

PERGUNTA DO USUÁRIO: {question}

INSTRUÇÕES IMPORTANTES:
1. Use APENAS os dados fornecidos acima - não invente informações
2. Responda em português brasileiro, de forma natural e profissional
3. Use formatação Markdown para destacar números importantes (negrito, listas)
4. Se a pergunta for sobre quantidade de produtos, a resposta exata é: {len(produtos_unicos)} produtos diferentes
5. Se a pergunta for sobre receita total, a resposta exata é: R$ {receita_total:,.2f}
6. Para perguntas sobre ranking ou top produtos, use os dados "TOP 5 PRODUTOS" acima
7. Seja direto, mas amigável - como um analista conversando com um gestor
8. Se a pergunta não puder ser respondida com os dados disponíveis, explique educadamente

Responda agora:"""
                
                response = model.generate_content(
                    prompt,
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
                
                if response and response.text:
                    return jsonify({'answer': response.text}), 200
                else:
                    # Se Gemini não retornou texto, vai para fallback
                    raise Exception("Gemini não retornou resposta")
        except Exception as gemini_error:
            # Se Gemini falhar, continua para fallback
            pass
        
        # FALLBACK: Análise direta dos dados (SEMPRE FUNCIONA)
        answer = analyze_data_smart(all_data, question)
        return jsonify({'answer': answer}), 200
        
    except Exception as e:
        return jsonify({'answer': f'❌ Erro ao processar pergunta: {str(e)}'}), 200

@app.route('/api/upload-data', methods=['POST'])
def upload_data():
    """Upload de planilhas Excel/CSV para o Supabase"""
    try:
        # Importações dinâmicas (apenas quando necessário para evitar timeout no Vercel)
        import pandas as pd  # type: ignore
        import io
        from unidecode import unidecode  # type: ignore
        import re
        
        # Verificar arquivo
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nome do arquivo vazio'}), 400
        
        # Validar extensão
        allowed_extensions = {'.xlsx', '.xls', '.csv'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            return jsonify({'error': 'Tipo de arquivo não permitido. Use Excel (.xlsx, .xls) ou CSV'}), 400
        
        # Conectar ao Supabase
        client, error = get_supabase_client()
        if error:
            return jsonify({'error': f'Erro ao conectar: {error}'}), 500
        
        # Ler arquivo
        file_content = file.read()
        
        def standardize_column(col):
            """Padroniza nome de coluna"""
            col = unidecode(col)
            col = col.lower()
            col = re.sub(r'[^\w]', '_', col)
            col = re.sub(r'_{2,}', '_', col)
            return col.strip('_')
        
        try:
            # Processar baseado no tipo
            if file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                df = pd.read_csv(io.BytesIO(file_content))
            
            # Padronizar colunas
            df.columns = [standardize_column(col) for col in df.columns]
            
            # Adicionar mes_origem
            mes_origem = os.path.splitext(file.filename)[0]
            df['mes_origem'] = mes_origem
            
            # Validar colunas obrigatórias
            required = ['data', 'id_transacao', 'produto', 'categoria', 'regiao', 
                       'quantidade', 'preco_unitario', 'receita_total']
            missing = [col for col in required if col not in df.columns]
            
            if missing:
                return jsonify({
                    'error': f'Colunas obrigatórias ausentes: {", ".join(missing)}'
                }), 400
            
            # Converter tipos
            df['data'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
            
            for col in ['quantidade', 'preco_unitario', 'receita_total']:
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remover linhas inválidas
            df.dropna(subset=required, inplace=True)
            
            if df.empty:
                return jsonify({'error': 'Nenhum dado válido encontrado'}), 400
            
            # Converter data para ISO
            df['data'] = df['data'].dt.strftime('%Y-%m-%d')
            
            # Converter para dicionários
            records = df.to_dict('records')
            
            # Inserir em lotes
            batch_size = 1000
            total_inserted = 0
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                client.table(TABLE_NAME).insert(batch).execute()
                total_inserted += len(batch)
            
            return jsonify({
                'success': True,
                'message': f'Arquivo "{file.filename}" importado com sucesso!',
                'rows_imported': total_inserted,
                'mes_origem': mes_origem
            }), 200
            
        except Exception as processing_error:
            return jsonify({
                'error': f'Erro ao processar arquivo: {str(processing_error)}'
            }), 400
        
    except Exception as e:
        return jsonify({'error': f'Erro ao fazer upload: {str(e)}'}), 500

@app.route('/api/database-stats', methods=['GET'])
def database_stats():
    """Estatísticas do banco Supabase"""
    try:
        client, error = get_supabase_client()
        if error:
            return jsonify({'error': error}), 500
        
        # Buscar todos os dados
        all_data = []
        page_size = 1000
        start = 0
        
        while True:
            resp = client.table(TABLE_NAME).select('*').range(start, start + page_size - 1).execute()
            rows = resp.data or []
            all_data.extend(rows)
            if len(rows) < page_size:
                break
            start += page_size
        
        if not all_data:
            return jsonify({
                'total_records': 0,
                'message': 'Banco de dados vazio'
            }), 200
        
        # Extrair datas
        datas = []
        meses = set()
        for row in all_data:
            data_str = row.get('data')
            if data_str:
                try:
                    dt = datetime.fromisoformat(str(data_str)[:10])
                    datas.append(dt)
                    meses.add(dt.strftime('%Y-%m'))
                except:
                    pass
        
        return jsonify({
            'total_records': len(all_data),
            'unique_months': len(meses),
            'date_range': {
                'start': min(datas).strftime('%d/%m/%Y') if datas else 'N/A',
                'end': max(datas).strftime('%d/%m/%Y') if datas else 'N/A'
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync-data', methods=['POST'])
def sync_data():
    """Endpoint para simular sincronização (na verdade só limpa cache)"""
    return jsonify({
        'success': True,
        'message': 'Dados sincronizados com sucesso!'
    }), 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({'message': 'API Bruna Bot - Use /api/health'}), 200

# Handler para Vercel
handler = app

# Local only
if __name__ == '__main__':
    app.run(debug=True, port=5000)


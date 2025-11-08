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
        produtos_por_regiao = {}  # Produtos por região
        
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
                produtos_por_categoria[categoria][prod] = produtos_por_categoria[categoria].get(prod, 0) + qty
                
                # Por região
                if regiao not in produtos_por_regiao:
                    produtos_por_regiao[regiao] = {}
                produtos_por_regiao[regiao][prod] = produtos_por_regiao[regiao].get(prod, 0) + qty
                
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
            
            context = f"""Você é um analista de vendas especializado. Aqui está o RESUMO COMPLETO de {len(data)} registros de vendas de 2024:

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
            
            context += f"\n📦 VENDAS POR CATEGORIA:\n"
            for categoria, prods in produtos_por_categoria.items():
                total_cat = sum(prods.values())
                context += f"- {categoria}: {int(total_cat)} unidades\n"
            
            context += f"\n🗺️ VENDAS POR REGIÃO:\n"
            for regiao, prods in produtos_por_regiao.items():
                total_reg = sum(prods.values())
                context += f"- {regiao}: {int(total_reg)} unidades\n"
            
            context += f"\n❓ PERGUNTA DO USUÁRIO: {question}\n\n"
            context += "Responda em português de forma clara e objetiva, usando EXATAMENTE os dados agregados fornecidos acima. "
            context += "Se a pergunta for sobre um mês específico, analise apenas os dados daquele mês. "
            context += "Sempre formate valores monetários como R$ X.XXX,XX."
            
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
                    
                    periodo = f" em {mes_nome}" if mes_nome else " no período analisado"
                    return jsonify({
                        'answer': f'📊 **Análise de Vendas**\n\nO produto mais vendido{periodo} foi **{top_prod}** com **{qty} unidades** vendidas.'
                    }), 200
            
            # Resposta genérica
            return jsonify({
                'answer': f'📊 Recebi sua pergunta: "{question}"\n\nNo momento, estou com dificuldades para processar com IA. Tente perguntas como:\n- "Qual produto foi mais vendido em Janeiro?"\n- "Qual o total de vendas em Março?"\n- "Quais produtos mais vendidos?"'
            }), 200
        
    except Exception as e:
        print(f"ERRO NO /api/analyze: {str(e)}")
        return jsonify({'answer': f'❌ Erro ao processar pergunta: {str(e)}'}), 200

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

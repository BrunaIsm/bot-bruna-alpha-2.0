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

def query_supabase(select_fields='*', limit=5000):
    """Query direta na API REST do Supabase sem SDK"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        params = {
            'select': select_fields,
            'limit': limit
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=8)
        response.raise_for_status()
        return response.json(), None
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
        # Buscar apenas campos necessários
        data, error = query_supabase('produto,quantidade,receita_total,data', limit=5000)
        
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
        data, error = query_supabase('produto,quantidade,receita_total,data', limit=5000)
        
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
    """Análise com fallback (sem Gemini por enquanto para reduzir dependências)"""
    try:
        body = request.get_json()
        question = body.get('message', '').lower()
        
        # Buscar dados
        data, error = query_supabase('produto,quantidade,data', limit=100)
        
        if error or not data:
            return jsonify({
                'answer': '❌ Não foi possível acessar os dados. Verifique a conexão com o Supabase.'
            }), 200
        
        # Análise simples baseada em palavras-chave
        if 'janeiro' in question and ('vendido' in question or 'produto' in question):
            # Filtrar dados de janeiro
            jan_produtos = {}
            for row in data:
                try:
                    data_str = row.get('data', '')
                    if '-01-' in data_str:  # Janeiro
                        prod = row.get('produto', 'Desconhecido')
                        qty = float(str(row.get('quantidade', 0)).replace(',', '.'))
                        jan_produtos[prod] = jan_produtos.get(prod, 0) + qty
                except:
                    continue
            
            if jan_produtos:
                top_prod = max(jan_produtos, key=jan_produtos.get)
                qty = int(jan_produtos[top_prod])
                return jsonify({
                    'answer': f'📊 **Análise de Janeiro**\n\nO produto mais vendido em Janeiro foi **{top_prod}** com {qty} unidades vendidas.'
                }), 200
        
        # Resposta genérica
        return jsonify({
            'answer': '📊 Sua pergunta foi recebida. Esta versão usa dados reais do Supabase, mas ainda não tem integração completa com IA. Por favor, seja específico sobre qual mês ou produto deseja analisar.'
        }), 200
        
    except Exception as e:
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

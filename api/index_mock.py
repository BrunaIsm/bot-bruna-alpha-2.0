"""
API Flask MOCKADA - Versão de teste para Vercel
Retorna dados fixos sem dependências pesadas
"""
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check simples"""
    return jsonify({
        'status': 'ok',
        'message': 'API funcionando (modo mock)',
        'environment': {
            'supabase_url_configured': True,
            'supabase_key_configured': True,
            'gemini_key_configured': True,
            'table_name': 'vendas_2024'
        }
    }), 200

@app.route('/api/metrics', methods=['GET'])
def metrics():
    """Métricas mockadas"""
    return jsonify({
        'melhor_mes': {
            'nome': 'Abril/2024',
            'valor': 'R$ 5.119.562,68'
        },
        'produto_mais_vendido': {
            'nome': 'Headset HyperX',
            'quantidade': 463
        },
        'quantidade_produtos': 50,
        'vendas_totais_ano': 'R$ 58.450.000,00',
        'files_processed': 1,
        'records_analyzed': 2600,
        'last_updated': datetime.utcnow().strftime('%d/%m/%Y %H:%M'),
        'no_data': False
    }), 200

@app.route('/api/monthly-metrics', methods=['GET'])
def monthly_metrics():
    """Métricas mensais mockadas"""
    months = []
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho']
    
    for i, mes in enumerate(meses, 1):
        months.append({
            'month': f"{mes}/2024",
            'total_revenue': f"R$ {(4500000 + i * 100000):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'total_sales': 200 + i * 10,
            'top_products': [
                {'name': 'Produto A', 'quantity': 50 + i * 5},
                {'name': 'Produto B', 'quantity': 40 + i * 4},
                {'name': 'Produto C', 'quantity': 30 + i * 3}
            ]
        })
    
    return jsonify({
        'no_data': False,
        'months': months
    }), 200

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Análise mockada"""
    return jsonify({
        'answer': '📊 **Análise de Vendas (Dados de Teste)**\n\nO produto mais vendido em Janeiro foi o **Headset HyperX** com 52 unidades vendidas.\n\nEsta é uma resposta mockada para testes. Configure as credenciais reais do Supabase e Gemini para obter análises reais.'
    }), 200

@app.route('/api/diagnostic', methods=['GET'])
def diagnostic():
    """Diagnóstico"""
    return jsonify({
        'status': 'ok',
        'message': 'Endpoint de diagnóstico funcionando (modo mock)',
        'environment': {
            'SUPABASE_URL': 'CONFIGURADO (mock)',
            'SUPABASE_KEY': 'CONFIGURADO (mock)',
            'GEMINI_API_KEY': 'CONFIGURADO (mock)',
            'TABLE_NAME': 'vendas_2024'
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)

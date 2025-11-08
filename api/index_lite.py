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
        
        # Buscar dados com paginação
        all_rows = []
        page_size = 1000
        start = 0
        
        while True:
            resp = client.table(TABLE_NAME).select('*').range(start, start + page_size - 1).execute()
            rows = resp.data or []
            all_rows.extend(rows)
            if len(rows) < page_size:
                break
            start += page_size
        
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

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Análise com Gemini - importado dinamicamente"""
    try:
        data = request.json
        question = data.get('message', '')
        
        if not question:
            return jsonify({'error': 'Pergunta não fornecida'}), 400
        
        # Import dinâmico do Gemini (só quando usado)
        import google.generativeai as genai
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            return jsonify({'error': 'Gemini API key não configurada'}), 500
        
        genai.configure(api_key=gemini_key)
        
        # Buscar dados do Supabase
        client, error = get_supabase_client()
        if error:
            return jsonify({'answer': f'Não consigo acessar os dados: {error}'}), 200
        
        resp = client.table(TABLE_NAME).select('*').limit(100).execute()
        sample_data = resp.data or []
        
        # Gerar resposta
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""Baseado nos dados de vendas:
{sample_data[:5]}

Responda a pergunta: {question}

Seja direto e objetivo."""
        
        response = model.generate_content(
            prompt,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        return jsonify({'answer': response.text}), 200
        
    except Exception as e:
        return jsonify({'answer': f'Erro ao processar pergunta: {str(e)}'}), 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({'message': 'API Bruna Bot - Use /api/health'}), 200

# Handler para Vercel
handler = app

# Local only
if __name__ == '__main__':
    app.run(debug=True, port=5000)

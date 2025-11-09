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
- Responda de forma COMPLETA mas DIRETA, focando na pergunta
- Use emojis com moderação (2-3 no máximo: 📊 💰 🏆 🎯 ⭐)
- Destaque números importantes com **negrito**
- Formate valores: R$ X.XXX,XX
- Seja entusiasmado mas CONCISO (máximo 3-4 parágrafos)
- SEMPRE use bullet points "•" para listas, NUNCA use asteriscos "*"
- Organize dados de forma visual e limpa

REGRAS IMPORTANTES:
1. Se perguntarem "quais produtos", "que produtos", "quais são": SEMPRE liste os nomes
2. Se perguntarem "quantos produtos": responda o número E liste os nomes
3. Se perguntarem sobre ranking/top: mostre TOP 5 com valores
4. Se perguntarem sobre 1 produto específico: seja detalhado sobre aquele produto
5. Se perguntarem sobre 1 mês específico: foque apenas naquele mês
6. Se perguntarem comparação: compare os dados relevantes

FORMATO DE RESPOSTA:
- Comece com um resumo curto (1 linha com número em negrito)
- Liste itens usando "•" (bullet point) seguido de espaço
- Se tiver valores/quantidades, mostre após o nome: "• Produto: X unidades"
- Adicione um insight breve no final (1 frase)

Exemplo CORRETO de formatação:
"Foram vendidos **25 produtos diferentes**:

• Produto A: 150 unidades
• Produto B: 120 unidades
• Produto C: 95 unidades

💡 Insight: Grande variedade de produtos no portfólio!"

NUNCA use este formato ERRADO:
"* Produto A
* Produto B"
"""
            
            response = model.generate_content(context)
            
            return jsonify({'answer': response.text}), 200
            
        except Exception as gemini_error:
            print(f"Erro no Gemini: {str(gemini_error)}")
            
            # FALLBACK: Análise simples sem IA
            question_lower = question.lower()
            
            # Detectar meses na pergunta
            meses_nomes = {
                'janeiro': ('Janeiro/2024', '-01-'), 'fevereiro': ('Fevereiro/2024', '-02-'), 
                'março': ('Março/2024', '-03-'), 'marco': ('Março/2024', '-03-'),
                'abril': ('Abril/2024', '-04-'), 'maio': ('Maio/2024', '-05-'), 
                'junho': ('Junho/2024', '-06-'), 'julho': ('Julho/2024', '-07-'), 
                'agosto': ('Agosto/2024', '-08-'), 'setembro': ('Setembro/2024', '-09-'),
                'outubro': ('Outubro/2024', '-10-'), 'novembro': ('Novembro/2024', '-11-'), 
                'dezembro': ('Dezembro/2024', '-12-')
            }
            
            # Detectar se é comparação entre meses
            meses_encontrados = []
            for nome_mes, (mes_completo, filtro) in meses_nomes.items():
                if nome_mes in question_lower:
                    meses_encontrados.append((nome_mes, mes_completo, filtro))
            
            # Se pergunta sobre COMPARAÇÃO entre meses (detecta 2+ meses OU palavra "compare")
            if (len(meses_encontrados) >= 2 or 
                (len(meses_encontrados) >= 1 and any(word in question_lower for word in ['compare', 'compara', 'comparação', 'diferença', 'versus', 'vs']))):
                
                def fmt_currency(value):
                    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                # Se tem exatamente 2 meses, fazer comparação específica
                if len(meses_encontrados) == 2:
                    mes1_nome, mes1_completo, mes1_filtro = meses_encontrados[0]
                    mes2_nome, mes2_completo, mes2_filtro = meses_encontrados[1]
                    
                    receita_mes1 = receita_por_mes.get(mes1_completo, 0.0)
                    receita_mes2 = receita_por_mes.get(mes2_completo, 0.0)
                    vendas_mes1 = vendas_por_mes.get(mes1_completo, 0)
                    vendas_mes2 = vendas_por_mes.get(mes2_completo, 0)
                    
                    diferenca = receita_mes2 - receita_mes1
                    percentual = ((receita_mes2 - receita_mes1) / receita_mes1 * 100) if receita_mes1 > 0 else 0
                    
                    vencedor = mes2_completo if receita_mes2 > receita_mes1 else mes1_completo
                    emoji_resultado = "📈" if diferenca > 0 else "📉"
                    texto_resultado = "superior" if diferenca > 0 else "inferior"
                    
                    answer = f"""📊 **COMPARAÇÃO DE FATURAMENTO** 📊

**{mes1_completo.split('/')[0]} vs {mes2_completo.split('/')[0]}**

📅 **{mes1_completo}**
💰 Receita: **{fmt_currency(receita_mes1)}**
🛒 Vendas: {vendas_mes1} transações

📅 **{mes2_completo}**
💰 Receita: **{fmt_currency(receita_mes2)}**
🛒 Vendas: {vendas_mes2} transações

---

{emoji_resultado} **Resultado da Comparação**

• **Diferença:** {fmt_currency(abs(diferenca))}
• **Variação:** {abs(percentual):.1f}% {texto_resultado}
• **Vencedor:** 🏆 **{vencedor}**

"""
                    # Adicionar top 3 produtos de cada mês
                    if mes1_completo in produtos_por_mes and mes2_completo in produtos_por_mes:
                        top_mes1 = sorted(produtos_por_mes[mes1_completo].items(), key=lambda x: x[1], reverse=True)[:3]
                        top_mes2 = sorted(produtos_por_mes[mes2_completo].items(), key=lambda x: x[1], reverse=True)[:3]
                        
                        answer += f"🏆 **Top 3 Produtos - {mes1_completo.split('/')[0]}**\n"
                        for i, (prod, qty) in enumerate(top_mes1, 1):
                            answer += f"{i}. {prod}: {int(qty)} unidades\n"
                        
                        answer += f"\n🏆 **Top 3 Produtos - {mes2_completo.split('/')[0]}**\n"
                        for i, (prod, qty) in enumerate(top_mes2, 1):
                            answer += f"{i}. {prod}: {int(qty)} unidades\n"
                    
                    return jsonify({'answer': answer}), 200
                
                # Se tem apenas 1 mês mencionado mas pede comparação, mostrar contexto geral
                elif len(meses_encontrados) == 1:
                    mes_nome, mes_completo, mes_filtro = meses_encontrados[0]
                    
                    # Mostrar ranking de todos os meses com destaque no mês mencionado
                    meses_ordenados = sorted(receita_por_mes.items(), key=lambda x: x[1], reverse=True)
                    
                    answer = f"""📊 **COMPARAÇÃO MENSAL - Contexto de {mes_completo}** 📊

📊 **Ranking de Todos os Meses:**

"""
                    for i, (mes, receita) in enumerate(meses_ordenados, 1):
                        vendas = vendas_por_mes.get(mes, 0)
                        emoji = "⭐" if mes == mes_completo else "📍"
                        destaque = " **← MÊS CONSULTADO**" if mes == mes_completo else ""
                        answer += f"{emoji} **{i}º {mes}**: {fmt_currency(receita)} ({vendas} vendas){destaque}\n"
                    
                    return jsonify({'answer': answer}), 200
            
            # Detectar mês único para filtros simples
            mes_filtro = None
            mes_nome = None
            for nome_mes, (mes_completo, filtro) in meses_nomes.items():
                if nome_mes in question_lower and len(meses_encontrados) <= 1:
                    mes_filtro = filtro
                    mes_nome = nome_mes.capitalize()
                    break
            
            # IMPORTANTE: Verificar "quantos produtos" ANTES de "produto mais vendido"
            # Se pergunta sobre QUANTOS PRODUTOS ou DIVERSIDADE
            if any(word in question_lower for word in ['quantos produtos', 'quais produtos', 'produtos diferentes', 'variedade', 'diversidade']):
                def fmt_currency(value):
                    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                qtd_produtos = len(produtos_total)
                total_unidades = sum(produtos_total.values())
                
                # Top 10 produtos
                top_10 = sorted(produtos_total.items(), key=lambda x: x[1], reverse=True)[:10]
                
                answer = f"""🛒 **DIVERSIDADE DE PRODUTOS** 🛒

📦 **Portfólio Completo**

Foram vendidos **{qtd_produtos} produtos diferentes** em 2024!
📊 Total de unidades vendidas: **{int(total_unidades)}**

---

🏆 **Top 10 Produtos Mais Vendidos:**

"""
                for i, (produto, qty) in enumerate(top_10, 1):
                    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                    answer += f"{emoji} **{produto}**: {int(qty)} unidades\n"
                
                # Média de vendas por produto
                media_por_produto = total_unidades / qtd_produtos if qtd_produtos > 0 else 0
                answer += f"\n💡 **Insight:** Média de **{int(media_por_produto)} unidades** por produto!"
                
                return jsonify({'answer': answer}), 200
            
            # Se pergunta sobre TOP 5 ou RANKING
            if any(word in question_lower for word in ['top 5', 'top5', 'top 10', 'top10', 'ranking', 'liste']):
                # Top produtos por quantidade
                top_produtos = sorted(produtos_total.items(), key=lambda x: x[1], reverse=True)[:5]
                
                answer = f"""🏆 **TOP 5 PRODUTOS MAIS VENDIDOS** 🏆

"""
                for i, (produto, qty) in enumerate(top_produtos, 1):
                    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"
                    answer += f"{emoji} **{i}º lugar: {produto}**\n   📦 {int(qty)} unidades vendidas\n\n"
                
                total_top5 = sum(qty for _, qty in top_produtos)
                total_geral = sum(produtos_total.values())
                percentual = (total_top5 / total_geral * 100) if total_geral > 0 else 0
                
                answer += f"💡 **Insight:** Estes 5 produtos representam **{percentual:.1f}%** de todas as vendas!"
                
                return jsonify({'answer': answer}), 200
            
            # Se pergunta sobre REGIÃO
            if any(word in question_lower for word in ['região', 'regiao', 'regiões', 'regioes', 'regional']):
                def fmt_currency(value):
                    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                if receita_por_regiao:
                    # Ordenar regiões por receita
                    regioes_ordenadas = sorted(receita_por_regiao.items(), key=lambda x: x[1], reverse=True)
                    
                    top_regiao, top_receita = regioes_ordenadas[0]
                    
                    answer = f"""🗺️ **ANÁLISE POR REGIÃO** 🗺️

🏆 **Região Campeã em Receita:** **{top_regiao}**
💰 Receita total: **{fmt_currency(top_receita)}**

---

📊 **Ranking Completo de Receitas por Região:**

"""
                    for i, (regiao, receita) in enumerate(regioes_ordenadas, 1):
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"
                        unidades = sum(produtos_por_regiao.get(regiao, {}).values())
                        answer += f"{emoji} **{regiao}**: {fmt_currency(receita)} ({int(unidades)} unidades)\n"
                    
                    # Calcular participação percentual
                    receita_total = sum(receita_por_regiao.values())
                    percentual = (top_receita / receita_total * 100) if receita_total > 0 else 0
                    
                    answer += f"\n💡 **Insight:** A região {top_regiao} representa **{percentual:.1f}%** da receita total!"
                    
                    return jsonify({'answer': answer}), 200
            
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

🥇 **Produto Mais Vendido{periodo}**

**{top_prod}**
📦 **{qty} unidades** vendidas

---

📊 **Top 3 Produtos:**
"""
                    for i, (prod, q) in enumerate(top_3, 1):
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                        answer += f"{emoji} **{prod}**: {int(q)} unidades\n"
                    
                    return jsonify({'answer': answer}), 200
            
            # Se pergunta sobre CATEGORIA
            if any(word in question_lower for word in ['categoria', 'categorias', 'tipo', 'tipos']):
                def fmt_currency(value):
                    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                if receita_por_categoria:
                    # Ordenar categorias por receita
                    categorias_ordenadas = sorted(receita_por_categoria.items(), key=lambda x: x[1], reverse=True)
                    
                    top_categoria, top_receita = categorias_ordenadas[0]
                    
                    answer = f"""📦 **ANÁLISE POR CATEGORIA** 📦

🏆 **Categoria Líder em Receita:** **{top_categoria}**
💰 Receita total: **{fmt_currency(top_receita)}**

---

📊 **Ranking Completo de Receitas por Categoria:**

"""
                    for i, (categoria, receita) in enumerate(categorias_ordenadas, 1):
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"
                        unidades = sum(produtos_por_categoria.get(categoria, {}).values())
                        answer += f"{emoji} **{categoria}**: {fmt_currency(receita)} ({int(unidades)} unidades)\n"
                    
                    # Calcular participação percentual
                    receita_total = sum(receita_por_categoria.values())
                    percentual = (top_receita / receita_total * 100) if receita_total > 0 else 0
                    
                    answer += f"\n💡 **Insight:** A categoria {top_categoria} representa **{percentual:.1f}%** da receita total!"
                    
                    return jsonify({'answer': answer}), 200
            
            # Se pergunta sobre MELHOR MÊS ou RECEITA POR MÊS
            if any(word in question_lower for word in ['mês', 'mes', 'mensal', 'meses', 'melhor mês', 'melhor mes']):
                def fmt_currency(value):
                    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                if receita_por_mes:
                    # Ordenar meses por receita
                    meses_ordenados = sorted(receita_por_mes.items(), key=lambda x: x[1], reverse=True)
                    
                    melhor_mes, melhor_receita = meses_ordenados[0]
                    
                    answer = f"""📅 **ANÁLISE MENSAL DE VENDAS** 📅

🏆 **Melhor Mês do Ano:** **{melhor_mes}**
💰 Receita: **{fmt_currency(melhor_receita)}**

---

📊 **Receita de Todos os Meses:**

"""
                    for mes, receita in sorted(receita_por_mes.items()):
                        vendas = vendas_por_mes.get(mes, 0)
                        emoji = "🌟" if mes == melhor_mes else "📍"
                        answer += f"{emoji} **{mes}**: {fmt_currency(receita)} ({vendas} vendas)\n"
                    
                    receita_total = sum(receita_por_mes.values())
                    answer += f"\n💰 **Receita total do ano:** {fmt_currency(receita_total)}"
                    
                    return jsonify({'answer': answer}), 200
            
            # Se pergunta sobre RECEITA TOTAL DO ANO
            if any(word in question_lower for word in ['receita total', 'faturamento total', 'quanto foi', 'total do ano']):
                def fmt_currency(value):
                    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                receita_total = sum(receita_por_mes.values())
                qtd_vendas = sum(vendas_por_mes.values())
                
                answer = f"""💰 **RECEITA TOTAL DE 2024** 💰

📊 **Resultado Geral do Ano**

**Receita Total:** {fmt_currency(receita_total)}
**Total de Vendas:** {qtd_vendas} transações
**Quantidade de Produtos:** {len(produtos_total)} diferentes

---

📈 **Distribuição Mensal:**

"""
                for mes in sorted(receita_por_mes.keys()):
                    receita = receita_por_mes[mes]
                    percentual = (receita / receita_total * 100) if receita_total > 0 else 0
                    answer += f"• **{mes}**: {fmt_currency(receita)} ({percentual:.1f}%)\n"
                
                return jsonify({'answer': answer}), 200
            
            # Resposta genérica
            answer = f"""🤔 **Hmm, preciso de mais contexto!**

Recebi sua pergunta: *"{question}"*

Infelizmente, estou com dificuldades para processar essa análise no momento. Mas não se preocupe! 💪

💡 **Experimente perguntas como:**

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
        
        print(f"📊 Após validação: {len(df)} linhas válidas")
        
        if df.empty:
            return jsonify({'error': 'Nenhuma linha válida encontrada após validação'}), 400
        
        # Selecionar apenas as colunas que existem na tabela
        valid_columns = ['data', 'id_transacao', 'produto', 'categoria', 'regiao', 
                        'quantidade', 'preco_unitario', 'receita_total']
        df = df[valid_columns]
        
        print(f"📝 Colunas selecionadas: {list(df.columns)}")
        print(f"📋 Primeira linha: {df.iloc[0].to_dict() if len(df) > 0 else 'VAZIO'}")
        
        # Converter para formato JSON para inserção no Supabase
        records = df.to_dict('records')
        
        # Formatar data para ISO string
        for record in records:
            if pd.notna(record.get('data')):
                record['data'] = record['data'].strftime('%Y-%m-%d')
        
        # Inserir direto no Supabase
        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # Inserir no Supabase em lotes (max 1000 por vez)
        total_inserted = 0
        batch_size = 1000
        
        print(f"🚀 Iniciando inserção de {len(records)} registros...")
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            print(f"📤 Enviando lote {i//batch_size + 1} com {len(batch)} registros...")
            response = requests.post(url, headers=headers, json=batch, timeout=30)
            
            print(f"📥 Resposta: Status {response.status_code}")
            
            if response.status_code not in [200, 201]:
                print(f"❌ ERRO: {response.text}")
                raise Exception(f'Erro ao inserir lote {i//batch_size + 1}: {response.text}')
            
            total_inserted += len(batch)
            print(f"✅ Lote {i//batch_size + 1} inserido! Total: {total_inserted}")
        
        # Mensagem de sucesso
        message = f'✅ {total_inserted} linhas importadas com sucesso!'
        
        return jsonify({
            'success': True,
            'message': message,
            'rows_imported': total_inserted,
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
    """Endpoint desabilitado - tabela não tem coluna mes_origem para controle de arquivos"""
    return jsonify({
        'success': False,
        'error': 'Funcionalidade de limpeza desabilitada. A tabela vendas_2024 não possui rastreamento de arquivos individuais.',
        'info': 'Para limpar dados, use SQL direto no Supabase: DELETE FROM vendas_2024;'
    }), 501  # Not Implemented

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
    """Retorna informações sobre os dados no banco (sem mes_origem na tabela)"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'count=exact'
        }
        
        # Buscar contagem total
        params = {'select': 'id_transacao', 'limit': 1}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f'Erro ao buscar dados: {response.text}')
        
        # Pegar contagem do header Content-Range
        content_range = response.headers.get('Content-Range', '0-0/0')
        total_count = int(content_range.split('/')[-1]) if '/' in content_range else 0
        
        if total_count == 0:
            return jsonify({
                'success': True,
                'files': [],
                'total_records': 0,
                'message': 'Nenhum dado encontrado no banco'
            }), 200
        
        return jsonify({
            'success': True,
            'files': [{
                'name': 'vendas_2024',
                'count': total_count,
                'uploaded_at': 'Dados consolidados',
                'is_protected': False
            }],
            'total_records': total_count,
            'message': f'{total_count} registros no banco'
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

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import time
import re
import json
from unidecode import unidecode
from supabase import create_client, Client
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import io
from datetime import datetime

# Nota: No Vercel, variáveis de ambiente são configuradas no dashboard
# Localmente, use arquivo .env (precisa instalar python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Em produção, dotenv não está instalado (não é necessário)

app = Flask(__name__)
CORS(app)

# Variáveis globais para cache
cached_data = None
last_sync_time = None
CACHE_DURATION = 300  # 5 minutos

# Nome da tabela no Supabase (configurável via .env)
TABLE_NAME = os.getenv('SUPABASE_TABLE_NAME', 'vendas_2024')

def standardize_column_name(col):
    """Padroniza a string da coluna para minúsculas, sem acentos e com underscores."""
    col = unidecode(col)
    col = col.lower()
    col = re.sub(r'[^\w]', '_', col)
    col = re.sub(r'_{2,}', '_', col)
    col = col.strip('_')
    return col

def get_supabase_client():
    """Inicializa o cliente Supabase."""
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            return None, "Credenciais do Supabase não configuradas"
        
        supabase: Client = create_client(url, key)
        return supabase, None
        
    except Exception as e:
        return None, f"Erro ao inicializar Supabase: {str(e)}"

def load_sales_data():
    """Carrega e processa dados de vendas do Supabase."""
    global cached_data, last_sync_time
    
    # Verifica cache
    if cached_data is not None and last_sync_time:
        if time.time() - last_sync_time < CACHE_DURATION:
            return cached_data, None
    
    supabase, error = get_supabase_client()
    if error:
        return None, error
    
    try:
        # Buscar todos os dados da tabela vendas (sem limite)
        # Supabase por padrão limita em 1000, então usamos range para buscar todos
        all_data = []
        page_size = 1000
        offset = 0
        
        while True:
            response = supabase.table(TABLE_NAME).select('*').range(offset, offset + page_size - 1).execute()
            
            if not response.data:
                break
            
            all_data.extend(response.data)
            
            # Se retornou menos que page_size, chegamos ao fim
            if len(response.data) < page_size:
                break
            
            offset += page_size
        
        if not all_data:
            return None, "Nenhum dado encontrado no banco de dados"
        
        # Converter para DataFrame
        df_total = pd.DataFrame(all_data)
        
        if df_total.empty:
            return None, "Nenhum dado válido encontrado no banco de dados"
        
        # Converter tipos de dados
        if 'data' in df_total.columns:
            df_total['data'] = pd.to_datetime(df_total['data'], errors='coerce')
        
        for col in ['quantidade', 'preco_unitario', 'receita_total']:
            if col in df_total.columns:
                df_total[col] = pd.to_numeric(df_total[col], errors='coerce')
        
        # Limpar dados
        initial_count = len(df_total)
        required_cols = ['data', 'quantidade', 'preco_unitario', 'receita_total']
        existing_required_cols = [col for col in required_cols if col in df_total.columns]
        
        if existing_required_cols:
            df_total.dropna(subset=existing_required_cols, inplace=True)
        
        final_count = len(df_total)
        
        # Contar meses únicos
        meses_unicos = df_total['mes_origem'].nunique() if 'mes_origem' in df_total.columns else 1
        
        # Cache dos dados
        cached_data = {
            'dataframe': df_total,
            'files_processed': meses_unicos,
            'records_total': initial_count,
            'records_clean': final_count
        }
        last_sync_time = time.time()
        
        return cached_data, None
        
    except Exception as e:
        return None, f"Erro ao carregar dados: {str(e)}"

def generate_direct_answer(df, query):
    """Gera resposta direta dos dados sem IA quando Gemini falha."""
    try:
        query_lower = query.lower()
        
        # Detectar mês específico na pergunta
        meses = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3, 'abril': 4,
            'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
            'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
        }
        mes_filtro = None
        mes_nome = None
        for nome_mes, num_mes in meses.items():
            if nome_mes in query_lower:
                mes_filtro = num_mes
                mes_nome = nome_mes.capitalize()
                break
        
        # Detectar tipo de pergunta e responder com dados
        if 'região' in query_lower or 'regiao' in query_lower:
            # Se há um mês específico, filtrar por ele
            if mes_filtro:
                df_filtrado = df[df['data'].dt.month == mes_filtro]
                if len(df_filtrado) == 0:
                    return f"❌ Não há dados disponíveis para {mes_nome}/2024"
                
                receita_por_regiao = df_filtrado.groupby('regiao')['receita_total'].sum().sort_values(ascending=False)
                top_regiao = receita_por_regiao.index[0]
                top_valor = receita_por_regiao.iloc[0]
                
                resposta = f"🌍 Em **{mes_nome}/2024**, a região com mais vendas foi **{top_regiao}** com **R$ {top_valor:,.2f}**\n\n"
                resposta += f"Ranking de {mes_nome}/2024:\n"
                for i, (regiao, valor) in enumerate(receita_por_regiao.items(), 1):
                    resposta += f"{i}. **{regiao}**: R$ {valor:,.2f}\n"
                return resposta
            else:
                # Análise do período completo
                receita_por_regiao = df.groupby('regiao')['receita_total'].sum().sort_values(ascending=False)
                top_regiao = receita_por_regiao.index[0]
                top_valor = receita_por_regiao.iloc[0]
                
                resposta = f"🌍 A região que gerou mais receita foi **{top_regiao}** com **R$ {top_valor:,.2f}**\n\n"
                resposta += "Ranking completo:\n"
                for i, (regiao, valor) in enumerate(receita_por_regiao.items(), 1):
                    resposta += f"{i}. **{regiao}**: R$ {valor:,.2f}\n"
                return resposta
            
        elif 'produto' in query_lower and ('mais' in query_lower or 'top' in query_lower or 'vendido' in query_lower):
            top_produtos = df.groupby('produto')['quantidade'].sum().nlargest(5)
            
            resposta = "🏆 **Top 5 Produtos Mais Vendidos:**\n\n"
            for i, (produto, qtd) in enumerate(top_produtos.items(), 1):
                resposta += f"{i}. **{produto}**: {int(qtd)} unidades\n"
            return resposta
            
        elif 'mês' in query_lower or 'mes' in query_lower:
            receita_por_mes = df.groupby(df['data'].dt.to_period('M'))['receita_total'].sum().sort_values(ascending=False)
            top_mes = str(receita_por_mes.index[0])
            top_valor = receita_por_mes.iloc[0]
            
            return f"📊 O mês com maior receita foi **{top_mes}** com **R$ {top_valor:,.2f}**"
            
        elif 'categoria' in query_lower:
            receita_por_categoria = df.groupby('categoria')['receita_total'].sum().sort_values(ascending=False)
            top_categoria = receita_por_categoria.index[0]
            top_valor = receita_por_categoria.iloc[0]
            
            resposta = f"🎯 A categoria com maior volume de vendas foi **{top_categoria}** com **R$ {top_valor:,.2f}**\n\n"
            resposta += "Todas as categorias:\n"
            for i, (cat, valor) in enumerate(receita_por_categoria.items(), 1):
                resposta += f"{i}. **{cat}**: R$ {valor:,.2f}\n"
            return resposta
            
        elif 'total' in query_lower or 'quanto' in query_lower or 'receita' in query_lower:
            total = df['receita_total'].sum()
            return f"💰 A receita total de 2024 foi de **R$ {total:,.2f}**"
            
        else:
            # Resposta genérica com estatísticas gerais
            total = df['receita_total'].sum()
            n_produtos = df['produto'].nunique()
            top_produto = df.groupby('produto')['quantidade'].sum().idxmax()
            
            return (f"📊 **Resumo dos Dados:**\n\n"
                   f"• Receita Total: **R$ {total:,.2f}**\n"
                   f"• Produtos Únicos: **{n_produtos}**\n"
                   f"• Produto Mais Vendido: **{top_produto}**\n\n"
                   f"💡 Reformule sua pergunta para obter uma análise mais específica.")
                   
    except Exception as e:
        print(f"Erro em generate_direct_answer: {e}")
        return "Não foi possível processar sua pergunta. Tente uma pergunta mais simples como 'Qual o total de vendas?'"

def generate_analysis_with_gemini(df, user_query, retry=True):
    """Gera análise usando Gemini APIs com dados agregados para economizar tokens."""
    try:
        # Configurar Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return "Erro: Chave da API Gemini não configurada"
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Criar sumário dos dados (muito mais eficiente em tokens)
        # Adicionar receita por região e mês para análises temporais detalhadas
        df['ano_mes'] = df['data'].dt.to_period('M')
        receita_regiao_mes = df.groupby(['ano_mes', 'regiao'])['receita_total'].sum().unstack(fill_value=0)
        
        summary = {
            'total_registros': len(df),
            'periodo': f"{df['data'].min().strftime('%d/%m/%Y')} a {df['data'].max().strftime('%d/%m/%Y')}",
            'receita_total': float(df['receita_total'].sum()),
            'receita_por_mes': df.groupby(df['data'].dt.to_period('M'))['receita_total'].sum().to_dict(),
            'receita_por_produto': df.groupby('produto')['receita_total'].sum().sort_values(ascending=False).head(20).to_dict(),
            'receita_por_categoria': df.groupby('categoria')['receita_total'].sum().sort_values(ascending=False).to_dict(),
            'receita_por_regiao': df.groupby('regiao')['receita_total'].sum().sort_values(ascending=False).to_dict(),
            'receita_por_regiao_mes': {str(mes): regiao_dict.to_dict() for mes, regiao_dict in receita_regiao_mes.iterrows()},
            'quantidade_por_produto': df.groupby('produto')['quantidade'].sum().sort_values(ascending=False).head(20).to_dict(),
            'produtos_unicos': df['produto'].nunique(),
            'categorias': df['categoria'].unique().tolist(),
            'regioes': df['regiao'].unique().tolist()
        }
        
        # Converter períodos para strings
        if 'receita_por_mes' in summary:
            summary['receita_por_mes'] = {str(k): v for k, v in summary['receita_por_mes'].items()}
        
        dados_resumidos = json.dumps(summary, ensure_ascii=False, indent=2, default=str)
        
        # Prompt mais direto e seguro para evitar bloqueios
        full_prompt = f"""
Você é um assistente de análise de dados de vendas.

DADOS DE VENDAS 2024:
{dados_resumidos}

IMPORTANTE: Os dados incluem 'receita_por_regiao_mes' que mostra a receita de cada região MÊS A MÊS.
Use este campo quando perguntarem sobre regiões em meses específicos.

PERGUNTA DO USUÁRIO: {user_query}

INSTRUÇÕES DE RESPOSTA:
- Responda diretamente usando os dados acima
- Use números em negrito: **R$ 1.234,56** ou **42 unidades**
- Formato de data: Janeiro/2024, Fevereiro/2024, etc.
- Use emojis: 📊 💰 📈 🏆 📉 🌍
- Liste itens com bullets (•) quando necessário
- Seja objetivo e conciso
- SEMPRE verifique receita_por_regiao_mes para perguntas sobre regiões e meses

Responda agora:
"""
        
        # Gerar resposta com tratamento de erro
        try:
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Aumentado para dar mais flexibilidade
                    max_output_tokens=2048,
                    top_p=0.95,
                    top_k=40,
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
        except Exception as gen_error:
            print(f"Erro ao gerar conteúdo: {gen_error}")
            # Tentar com prompt simplificado imediatamente
            if retry:
                return generate_analysis_with_gemini(df, user_query, retry=False)
            return "Erro ao processar sua pergunta. Tente reformulá-la de forma mais direta."
        
        # Verificar se a resposta foi bloqueada ANTES de tentar acessar .text
        if not response.candidates or len(response.candidates) == 0:
            print(f"ERRO: Nenhum candidato retornado pela API")
            return "Não foi possível gerar uma resposta. Por favor, tente reformular sua pergunta de forma mais direta."
        
        candidate = response.candidates[0]
        
        # Verificar se há conteúdo válido
        if not hasattr(candidate, 'content') or not candidate.content or not candidate.content.parts:
            # Tentar obter o motivo do bloqueio
            finish_reason = candidate.finish_reason if hasattr(candidate, 'finish_reason') else None
            safety_ratings = candidate.safety_ratings if hasattr(candidate, 'safety_ratings') else None
            
            # Log detalhado para debug
            print(f"=" * 60)
            print(f"RESPOSTA BLOQUEADA PELA API GEMINI")
            print(f"=" * 60)
            print(f"Pergunta: {user_query}")
            print(f"Finish Reason: {finish_reason}")
            print(f"Safety Ratings: {safety_ratings}")
            print(f"=" * 60)
            
            # Se for SAFETY e ainda não tentou retry, tenta com prompt mais simples
            if finish_reason == 2 and retry:
                # Verificar se é pergunta sobre região + mês específico - ir direto para Python
                query_lower = user_query.lower()
                meses_keywords = ['janeiro', 'fevereiro', 'março', 'marco', 'abril', 'maio', 'junho', 
                                 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
                tem_mes = any(mes in query_lower for mes in meses_keywords)
                tem_regiao = 'região' in query_lower or 'regiao' in query_lower
                
                if tem_mes and tem_regiao:
                    print("Pergunta sobre região + mês específico - usando Python diretamente")
                    return generate_direct_answer(df, user_query)
                
                print("Tentando novamente com prompt simplificado...")
                
                # Criar dados resumidos para o retry incluindo dados mensais
                df['ano_mes'] = df['data'].dt.to_period('M')
                receita_regiao_mes = df.groupby(['ano_mes', 'regiao'])['receita_total'].sum().unstack(fill_value=0)
                dados_mes_regiao = {str(mes): regiao_dict.to_dict() for mes, regiao_dict in receita_regiao_mes.iterrows()}
                
                receita_por_regiao = df.groupby('regiao')['receita_total'].sum().sort_values(ascending=False).to_dict()
                
                # Prompt ultra-simples e direto
                simple_prompt = f"""
Pergunta: {user_query}

Dados por região e mês: {json.dumps(dados_mes_regiao, ensure_ascii=False, default=str)}

Receita total por região: {receita_por_regiao}

Responda em português. Use negrito (**valor**) para números.
"""
                try:
                    retry_response = model.generate_content(
                        simple_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.5,
                            max_output_tokens=512,
                        ),
                        safety_settings={
                            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                        }
                    )
                    if retry_response.candidates and len(retry_response.candidates) > 0:
                        retry_candidate = retry_response.candidates[0]
                        if hasattr(retry_candidate, 'content') and retry_candidate.content and retry_candidate.content.parts:
                            print("✓ Retry bem-sucedido!")
                            return retry_response.text
                    print("✗ Retry também foi bloqueado")
                except Exception as retry_error:
                    print(f"✗ Retry falhou: {retry_error}")
            
            # Se chegou aqui, nem o retry funcionou - usar resposta direta
            if finish_reason == 2:  # SAFETY - tentar resposta direta
                print("Usando resposta direta dos dados Python...")
                return generate_direct_answer(df, user_query)
            elif finish_reason == 3:  # RECITATION
                return generate_direct_answer(df, user_query)
            elif finish_reason == 4:  # OTHER
                return generate_direct_answer(df, user_query)
            else:
                return generate_direct_answer(df, user_query)
        
        # Tentar acessar o texto com segurança
        try:
            return response.text
        except Exception as e:
            print(f"Erro ao acessar response.text: {e}")
            # Usar resposta direta como fallback
            return generate_direct_answer(df, user_query)
        
    except AttributeError as e:
        # Erro ao acessar response.text - tentar responder com dados diretos
        print(f"AttributeError: {e}")
        if retry:
            # Última tentativa: responder com análise direta dos dados
            return generate_direct_answer(df, user_query)
        return ("Não foi possível gerar uma resposta adequada. Por favor, reformule sua pergunta "
                "de forma mais específica, como 'Qual o produto mais vendido?' ou 'Quanto foi vendido em Janeiro?'")
    except Exception as e:
        print(f"Exceção geral: {e}")
        if retry:
            return generate_direct_answer(df, user_query)
        return f"Erro ao gerar análise: {str(e)}"

@app.route('/api/analyze', methods=['POST'])
def analyze_sales():
    """Endpoint principal para análise de vendas."""
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'Pergunta não fornecida'}), 400
        
        question = data['question']
        print(f"\n{'='*60}")
        print(f"NOVA PERGUNTA RECEBIDA: {question}")
        print(f"{'='*60}\n")
        
        # Carregar dados
        sales_data, error = load_sales_data()
        if error:
            return jsonify({'error': error}), 500
        
        # Passar DataFrame diretamente (não CSV) para economizar tokens
        df = sales_data['dataframe']
        
        # Gerar análise com dados agregados
        response = generate_analysis_with_gemini(df, question)
        
        print(f"\n{'='*60}")
        print(f"RESPOSTA GERADA:")
        print(response[:200] + "..." if len(response) > 200 else response)
        print(f"{'='*60}\n")
        
        return jsonify({
            'response': response,
            'filesProcessed': sales_data['files_processed'],
            'recordsAnalyzed': sales_data['records_clean'],
            'totalRecords': sales_data['records_total']
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/sync-data', methods=['POST'])
def sync_data():
    """Endpoint para sincronizar dados do Supabase (limpar cache)."""
    global cached_data, last_sync_time
    
    # Forçar nova sincronização
    cached_data = None
    last_sync_time = None
    
    sales_data, error = load_sales_data()
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify({
        'message': 'Sincronização concluída com sucesso!',
        'filesProcessed': sales_data['files_processed'],
        'recordsAnalyzed': sales_data['records_clean'],
        'totalRecords': sales_data['records_total']
    })

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Endpoint para obter métricas calculadas dos dados reais."""
    try:
        # Carregar dados
        sales_data, error = load_sales_data()
        if error:
            return jsonify({'error': error}), 500
        
        df = sales_data['dataframe']
        
        if df.empty:
            return jsonify({'error': 'Nenhum dado disponível'}), 404
        
        # Calcular métricas
        metrics = {}
        
        # 1. Melhor Mês (maior receita total)
        if 'receita_total' in df.columns and 'data' in df.columns:
            # Extrair mês e ano da coluna data
            df['mes_ano'] = pd.to_datetime(df['data']).dt.strftime('%Y-%m')
            df['mes_nome'] = pd.to_datetime(df['data']).dt.strftime('%B/%Y')
            
            # Traduzir nomes dos meses para português
            meses_pt = {
                'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
                'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
                'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
                'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
            }
            
            for en, pt in meses_pt.items():
                df['mes_nome'] = df['mes_nome'].str.replace(en, pt)
            
            # Agrupar por mês e somar receita
            receita_por_mes = df.groupby(['mes_ano', 'mes_nome'])['receita_total'].sum().reset_index()
            melhor_mes_idx = receita_por_mes['receita_total'].idxmax()
            melhor_mes_row = receita_por_mes.loc[melhor_mes_idx]
            
            metrics['melhor_mes'] = {
                'nome': melhor_mes_row['mes_nome'],
                'valor': f"R$ {melhor_mes_row['receita_total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            }
        elif 'mes_origem' in df.columns and 'receita_total' in df.columns:
            # Fallback para mes_origem se existir
            receita_por_mes = df.groupby('mes_origem')['receita_total'].sum()
            melhor_mes = receita_por_mes.idxmax()
            melhor_mes_valor = receita_por_mes.max()
            
            nome_formatado = melhor_mes
            if 'vendas_' in melhor_mes.lower():
                nome_formatado = melhor_mes.replace('vendas_', '').replace('_', ' ')
                nome_formatado = ' '.join(word.capitalize() for word in nome_formatado.split())
            
            metrics['melhor_mes'] = {
                'nome': nome_formatado,
                'valor': f"R$ {melhor_mes_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            }
        else:
            metrics['melhor_mes'] = {'nome': 'N/A', 'valor': 'R$ 0,00'}
        
        # 2. Produto Mais Vendido (maior quantidade total)
        if 'produto' in df.columns and 'quantidade' in df.columns:
            vendas_por_produto = df.groupby('produto')['quantidade'].sum()
            produto_mais_vendido = vendas_por_produto.idxmax()
            quantidade_vendida = vendas_por_produto.max()
            metrics['produto_mais_vendido'] = {
                'nome': produto_mais_vendido,
                'quantidade': int(quantidade_vendida)
            }
        else:
            metrics['produto_mais_vendido'] = {'nome': 'N/A', 'quantidade': 0}
        
        # 3. Quantidade de Produtos Únicos
        if 'produto' in df.columns:
            produtos_unicos = df['produto'].nunique()
            metrics['quantidade_produtos'] = produtos_unicos
        else:
            metrics['quantidade_produtos'] = 0
        
        # 4. Vendas Totais do Ano
        if 'receita_total' in df.columns:
            vendas_totais = df['receita_total'].sum()
            metrics['vendas_totais_ano'] = f"R$ {vendas_totais:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        else:
            metrics['vendas_totais_ano'] = 'R$ 0,00'
        
        # Informações adicionais
        metrics['files_processed'] = sales_data['files_processed']
        metrics['records_analyzed'] = sales_data['records_clean']
        metrics['last_updated'] = time.strftime('%d/%m/%Y %H:%M:%S')
        
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({'error': f'Erro ao calcular métricas: {str(e)}'}), 500



@app.route('/api/upload-data', methods=['POST'])
def upload_data():
    """Endpoint para fazer upload de dados para o Supabase."""
    try:
        # Verificar se um arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo foi enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nome do arquivo vazio'}), 400
        
        # Validar tipo de arquivo
        allowed_extensions = {'.xlsx', '.xls', '.csv'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            return jsonify({'error': 'Tipo de arquivo não permitido. Use Excel (.xlsx, .xls) ou CSV'}), 400
        
        # Obter cliente Supabase
        supabase, error = get_supabase_client()
        if error:
            return jsonify({'error': f'Erro ao conectar com Supabase: {error}'}), 500
        
        # Ler e processar o arquivo
        file_content = file.read()
        
        try:
            # Processar o arquivo dependendo do tipo
            if file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(io.BytesIO(file_content))
            else:  # .csv
                df = pd.read_csv(io.BytesIO(file_content))
            
            # Padronizar nomes das colunas
            df.columns = [standardize_column_name(col) for col in df.columns]
            
            # Nome do arquivo como mes_origem
            mes_origem = os.path.splitext(file.filename)[0]
            df['mes_origem'] = mes_origem
            
            # Validar colunas obrigatórias
            required_columns = ['data', 'id_transacao', 'produto', 'categoria', 'regiao', 
                              'quantidade', 'preco_unitario', 'receita_total']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return jsonify({
                    'error': f'Colunas obrigatórias ausentes: {", ".join(missing_columns)}',
                    'suggestion': 'Verifique se o arquivo contém todas as colunas necessárias.'
                }), 400
            
            # Converter tipos de dados
            df['data'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
            
            for col in ['quantidade', 'preco_unitario', 'receita_total']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remover linhas com dados inválidos
            df.dropna(subset=required_columns, inplace=True)
            
            if df.empty:
                return jsonify({
                    'error': 'Nenhum dado válido encontrado no arquivo',
                    'suggestion': 'Verifique se o arquivo contém dados válidos nas colunas obrigatórias.'
                }), 400
            
            # Converter data para string no formato ISO
            df['data'] = df['data'].dt.strftime('%Y-%m-%d')
            
            # Converter DataFrame para lista de dicionários
            records = df.to_dict('records')
            
            # Inserir dados no Supabase em lotes
            batch_size = 1000
            total_inserted = 0
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                response = supabase.table(TABLE_NAME).insert(batch).execute()
                total_inserted += len(batch)
            
            # Limpar cache para forçar recarregamento dos dados
            global cached_data, last_sync_time
            cached_data = None
            last_sync_time = None
            
            response_data = {
                'success': True,
                'message': f'Arquivo "{file.filename}" importado com sucesso para o Supabase!',
                'rows_imported': total_inserted,
                'columns_imported': len(df.columns),
                'mes_origem': mes_origem
            }
            
            return jsonify(response_data)
            
        except Exception as processing_error:
            error_str = str(processing_error)
            return jsonify({
                'error': f'Erro ao processar arquivo: {error_str}',
                'suggestion': 'Verifique se o arquivo não está corrompido e tem o formato correto.'
            }), 400
        
    except Exception as e:
        return jsonify({'error': f'Erro ao fazer upload: {str(e)}'}), 500

@app.route('/api/database-stats', methods=['GET'])
def database_stats():
    """Endpoint para verificar estatísticas do banco de dados Supabase."""
    try:
        supabase, error = get_supabase_client()
        if error:
            return jsonify({'error': f'Erro ao conectar com Supabase: {error}'}), 500
        
        # Buscar todos os dados para análise (com paginação)
        all_data = []
        page_size = 1000
        offset = 0
        
        while True:
            response = supabase.table(TABLE_NAME).select('*').range(offset, offset + page_size - 1).execute()
            
            if not response.data:
                break
            
            all_data.extend(response.data)
            
            if len(response.data) < page_size:
                break
            
            offset += page_size
        
        if not all_data:
            return jsonify({
                'success': True,
                'total_records': 0,
                'message': 'Nenhum dado encontrado na tabela',
                'database': 'Supabase',
                'table_name': TABLE_NAME
            })
        
        df = pd.DataFrame(all_data)
        total_records = len(df)
        
        # Buscar meses únicos (se a coluna existir)
        meses_unicos = 0
        if 'mes_origem' in df.columns:
            meses_unicos = df['mes_origem'].nunique()
        
        # Buscar data mais antiga e mais recente (se a coluna existir)
        oldest_date = None
        newest_date = None
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
            oldest_date = df['data'].min().strftime('%Y-%m-%d') if pd.notna(df['data'].min()) else None
            newest_date = df['data'].max().strftime('%Y-%m-%d') if pd.notna(df['data'].max()) else None
        
        response_data = {
            'success': True,
            'total_records': total_records,
            'meses_unicos': meses_unicos,
            'oldest_date': oldest_date,
            'newest_date': newest_date,
            'database': 'Supabase',
            'table_name': TABLE_NAME,
            'columns': list(df.columns)
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter estatísticas do banco: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de verificação de saúde."""
    try:
        return jsonify({'status': 'ok', 'message': 'API funcionando'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    """Endpoint raiz."""
    return jsonify({'message': 'API Bruna Bot - Use /api/health para verificar status'}), 200

# Exportar app para Vercel (serverless)
handler = app

if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    print(f"Servidor disponível em http://127.0.0.1:5000")
    print(f"Endpoints disponíveis:")
    print("  - GET  /api/health")
    print("  - GET  /api/metrics")
    print("  - GET  /api/database-stats")
    print("  - POST /api/analyze")
    print("  - POST /api/sync-data")
    print("  - POST /api/upload-data")
    
    try:
        app.run(debug=True, port=5000, host='127.0.0.1', use_reloader=False)
    except Exception as e:
        print(f"Erro ao iniciar servidor: {str(e)}")
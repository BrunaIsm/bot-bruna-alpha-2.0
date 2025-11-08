from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Endpoint super simples para testar Vercel
        try:
            env_status = {
                'SUPABASE_URL': 'CONFIGURADO' if os.getenv('SUPABASE_URL') else 'FALTANDO',
                'SUPABASE_KEY': 'CONFIGURADO' if os.getenv('SUPABASE_KEY') else 'FALTANDO',
                'GEMINI_API_KEY': 'CONFIGURADO' if os.getenv('GEMINI_API_KEY') else 'FALTANDO',
                'SUPABASE_TABLE_NAME': os.getenv('SUPABASE_TABLE_NAME', 'vendas_2024'),
                'PYTHON_VERSION': os.sys.version
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps({
                'status': 'ok',
                'message': 'Endpoint de diagnóstico funcionando',
                'environment': env_status
            }, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'error',
                'message': str(e)
            }).encode())

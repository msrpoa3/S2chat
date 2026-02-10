import os
import requests
import urllib.parse
from flask import Flask, render_template_string
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configurações do Supabase extraídas do seu ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
BUCKET_NAME = os.getenv("BUCKET_NAME", "").strip()

def gerar_diagnostico_link(nome_arquivo):
    """Tenta gerar a assinatura e retorna detalhes do erro se falhar."""
    nome_limpo = urllib.parse.unquote(nome_arquivo)
    
    # Endpoint oficial de assinatura
    url_request = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{nome_limpo}"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.post(url_request, headers=headers, json={"expiresIn": 3600}, timeout=10)
        
        if res.status_code == 200:
            link_relativo = res.json().get("signedURL")
            # Forçamos a reconstrução absoluta
            url_final = f"{SUPABASE_URL}{link_relativo}"
            return {"status": "✅ SUCESSO", "url": url_final, "debug": "Token gerado com sucesso."}
        else:
            return {"status": f"❌ ERRO {res.status_code}", "url": None, "debug": res.text}
            
    except Exception as e:
        return {"status": "❌ FALHA CRÍTICA", "url": None, "debug": str(e)}

@app.route("/")
def index():
    # 1. Tenta listar os ficheiros existentes
    list_url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}"}
    
    lista_arquivos = []
    try:
        res_list = requests.post(list_url, headers=headers, json={"prefix": ""}, timeout=10)
        if res_list.status_code == 200:
            for item in res_list.json():
                if item['name'] != ".emptyFolderPlaceholder":
                    diag = gerar_diagnostico_link(item['name'])
                    lista_arquivos.append({"nome": item['name'], "diag": diag})
    except Exception as e:
        print(f"Erro ao listar: {e}")

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Diagnóstico Supabase V3</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: 'Courier New', monospace; background: #0d1117; color: #58a6ff; padding: 20px; line-height: 1.5; }
            .container { max-width: 900px; margin: 0 auto; }
            .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 15px; margin-bottom: 20px; }
            .status-ok { color: #3fb950; font-weight: bold; }
            .status-err { color: #f85149; font-weight: bold; }
            .url-box { background: #000; padding: 10px; border-radius: 4px; font-size: 11px; word-break: break-all; color: #8b949e; margin: 10px 0; border: 1px dashed #30363d; }
            img { max-width: 100%; border: 2px solid #30363d; margin-top: 10px; border-radius: 4px; background: #21262d; }
            .hint { font-size: 12px; color: #d29922; background: rgba(210, 153, 34, 0.1); padding: 10px; border-radius: 4px; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛠 Diagnóstico de Storage</h1>
            <p><strong>URL:</strong> {{ url_base }} | <strong>Bucket:</strong> {{ bucket }}</p>

            <hr style="border: 0; border-top: 1px solid #30363d; margin: 20px 0;">

            {% for item in lista %}
            <div class="card">
                <div><strong>Ficheiro:</strong> <span style="color: #c9d1d9;">{{ item.nome }}</span></div>
                <div><strong>Status:</strong> 
                    <span class="{{ 'status-ok' if '✅' in item.diag.status else 'status-err' }}">
                        {{ item.diag.status }}
                    </span>
                </div>

                {% if item.diag.url %}
                    <div class="url-box">{{ item.diag.url }}</div>
                    
                    <p><strong>Teste de Visualização:</strong></p>
                    <img src="{{ item.diag.url }}" alt="Erro ao carregar imagem">
                    
                    <div class="hint">
                        💡 <strong>Se a imagem acima não carregar:</strong> <br>
                        1. Clique com o botão direito na imagem e escolha "Abrir em novo separador".<br>
                        2. Se ela abrir lá, o problema é <strong>CORS</strong> (bloqueio do navegador).<br>
                        3. Se ela der erro 403 lá também, o problema é a <strong>Política SQL (RLS)</strong>.
                    </div>
                {% else %}
                    <div class="url-box" style="color: #f85149;">{{ item.diag.debug }}</div>
                {% endif %}
            </div>
            {% endfor %}

            <footer style="text-align: center; margin-top: 50px; font-size: 12px; color: #8b949e;">
                Teste de Stress V3 - Sistema de Chat Privado
            </footer>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, lista=lista_arquivos, url_base=SUPABASE_URL, bucket=BUCKET_NAME)

if __name__ == "__main__":
    app.run(debug=True)

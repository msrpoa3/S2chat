import os
import requests
import urllib.parse
from flask import Flask, render_template_string
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
BUCKET_NAME = os.getenv("BUCKET_NAME", "").strip()

def gerar_diagnostico_link(nome_arquivo):
    """Gera link assinado e limpa o caminho para evitar 'request path is invalid'."""
    
    # 1. Garante que o nome do ficheiro está "limpo" para o pedido API
    # Decodificamos primeiro para evitar dupla codificação
    nome_puro = urllib.parse.unquote(nome_arquivo).strip()
    
    # 2. Endpoint: O nome do ficheiro deve ser codificado para a URL de pedido
    nome_encoded = urllib.parse.quote(nome_puro)
    url_request = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{nome_encoded}"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Pedimos o link válido por 2 horas
        res = requests.post(url_request, headers=headers, json={"expiresIn": 7200}, timeout=15)
        
        if res.status_code == 200:
            link_relativo = res.json().get("signedURL")
            
            # 3. LIMPEZA DA URL FINAL (Onde o erro de 'path invalid' morre)
            # Removemos qualquer barra extra entre o domínio e o caminho relativo
            link_relativo = link_relativo.lstrip('/')
            url_final = f"{SUPABASE_URL}/{link_relativo}"
            
            return {"status": "✅ SUCESSO", "url": url_final, "debug": "URL reconstruída com sucesso."}
        else:
            return {"status": f"❌ ERRO {res.status_code}", "url": None, "debug": res.text}
            
    except Exception as e:
        return {"status": "❌ FALHA", "url": None, "debug": str(e)}

@app.route("/")
def index():
    # Tenta listar os ficheiros existentes no bucket
    list_url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}"}
    
    resultados = []
    try:
        res_list = requests.post(list_url, headers=headers, json={"prefix": ""}, timeout=15)
        if res_list.status_code == 200:
            for item in res_list.json():
                nome = item['name']
                if nome != ".emptyFolderPlaceholder":
                    diag = gerar_diagnostico_link(nome)
                    resultados.append({"nome": nome, "diag": diag})
        else:
            return f"Erro ao listar bucket: {res_list.text}"
    except Exception as e:
        return f"Erro de conexão: {str(e)}"

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Diagnóstico V4 - Path Fix</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; background: #0b0e14; color: #adbac7; padding: 20px; }
            .card { background: #1c2128; border: 1px solid #444c56; padding: 15px; margin-bottom: 20px; border-radius: 8px; }
            .success { color: #57ab5a; font-weight: bold; }
            .error { color: #f47067; }
            .url-box { background: #0d1117; padding: 10px; font-size: 11px; word-break: break-all; margin: 10px 0; border-radius: 4px; border: 1px solid #30363d; }
            img { max-width: 100%; max-height: 300px; border: 2px solid #444c56; margin-top: 10px; border-radius: 4px; }
            .btn { display: inline-block; padding: 5px 10px; background: #347d39; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; }
        </style>
    </head>
    <body>
        <h1>Stress Test V4: Path Correction</h1>
        
        {% for item in resultados %}
        <div class="card">
            <strong>Ficheiro:</strong> {{ item.nome }} <br>
            <strong>Status:</strong> <span class="{{ 'success' if '✅' in item.diag.status else 'error' }}">{{ item.diag.status }}</span>
            
            {% if item.diag.url %}
                <div class="url-box">{{ item.diag.url }}</div>
                <a href="{{ item.diag.url }}" target="_blank" class="btn">Abrir Original em Nova Aba</a>
                <br>
                <img src="{{ item.diag.url }}" alt="A carregar...">
            {% else %}
                <p class="error">Debug: {{ item.diag.debug }}</p>
            {% endif %}
        </div>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html, resultados=resultados)

if __name__ == "__main__":
    app.run(debug=True)

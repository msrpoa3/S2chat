import os
import requests
import urllib.parse
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configurações extraídas do seu .env no Render
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
BUCKET_NAME = os.getenv("BUCKET_NAME", "").strip()

def gerar_link_estilo_manual(nome_arquivo):
    """Gera o link assinado e reconstrói a URL para bater com o formato manual."""
    
    # 1. Limpa o nome do ficheiro para o pedido
    nome_puro = urllib.parse.unquote(nome_arquivo).strip()
    
    # 2. Pedido de assinatura ao Supabase
    # Endpoint: /storage/v1/object/sign/BUCKET/FILE
    url_request = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{nome_puro}"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Solicitamos validade de 1 hora (3600 segundos)
        res = requests.post(url_request, headers=headers, json={"expiresIn": 3600}, timeout=10)
        
        if res.status_code == 200:
            dados = res.json()
            link_relativo = dados.get("signedURL") # Vem algo como "/storage/v1/object/sign/..."
            
            # 3. A MONTAGEM CRUCIAL:
            # O segredo é garantir que o link relativo comece logo após o domínio, sem // extras.
            link_limpo = link_relativo.lstrip('/')
            url_final = f"{SUPABASE_URL}/{link_limpo}"
            
            return {"status": "✅ SUCESSO", "url": url_final}
        else:
            return {"status": f"❌ ERRO {res.status_code}", "msg": res.text}
            
    except Exception as e:
        return {"status": "❌ FALHA", "msg": str(e)}

@app.route("/")
def index():
    # Lista os ficheiros para testar
    list_url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}"}
    
    resultados = []
    try:
        res_list = requests.post(list_url, headers=headers, json={"prefix": ""})
        if res_list.status_code == 200:
            # Testamos apenas os últimos 5 para ser rápido
            for item in res_list.json()[-5:]:
                nome = item['name']
                if nome != ".emptyFolderPlaceholder":
                    resultados.append({"nome": nome, "diag": gerar_link_estilo_manual(nome)})
    except Exception as e:
        return f"Erro de conexão: {e}"

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stress Test V5 - Final</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; background: #121212; color: white; padding: 20px; }
            .card { background: #1e1e1e; border: 1px solid #333; padding: 15px; margin-bottom: 20px; border-radius: 10px; }
            .url-box { background: #000; padding: 10px; font-size: 10px; word-break: break-all; color: #888; margin: 10px 0; border-radius: 5px; }
            img { max-width: 100%; border: 2px solid #444; border-radius: 5px; margin-top: 10px; }
            .success { color: #00ff00; }
            .error { color: #ff0000; }
        </style>
    </head>
    <body>
        <h1>Stress Test V5: Link Match</h1>
        <p>Este teste simula a URL exata que funcionou manualmente.</p>

        {% for r in resultados %}
        <div class="card">
            <strong>Ficheiro:</strong> {{ r.nome }} <br>
            <strong>Status:</strong> <span class="{{ 'success' if '✅' in r.diag.status else 'error' }}">{{ r.diag.status }}</span>
            
            {% if r.diag.url %}
                <div class="url-box">{{ r.diag.url }}</div>
                <img src="{{ r.diag.url }}" alt="A carregar imagem...">
            {% else %}
                <p class="error">Erro: {{ r.diag.msg }}</p>
            {% endif %}
        </div>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html, resultados=resultados)

if __name__ == "__main__":
    app.run(debug=True)

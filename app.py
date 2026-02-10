import os
import requests
import urllib.parse
from flask import Flask, request, render_template_string
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL").strip().rstrip('/')
SUPABASE_KEY = os.getenv("SUPABASE_KEY").strip()
BUCKET_NAME = os.getenv("BUCKET_NAME").strip()

def testar_assinatura(nome_arquivo):
    """Tenta gerar a URL e valida se o Supabase responde 200."""
    # 1. Decodifica o nome para garantir que o Supabase entenda (ex: %20 vira espaço)
    nome_puro = urllib.parse.unquote(nome_arquivo)
    
    url_request = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{nome_puro}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.post(url_request, headers=headers, json={"expiresIn": 600}, timeout=10)
        if res.status_code == 200:
            dados = res.json()
            url_relativa = dados.get("signedURL")
            # RECONSTRUÇÃO: Forçamos o domínio HTTPS para o navegador não se perder
            return {"status": "✅ OK", "url": f"{SUPABASE_URL}{url_relativa}"}
        else:
            return {"status": f"❌ ERRO {res.status_code}", "msg": res.text}
    except Exception as e:
        return {"status": "❌ FALHA CONEXÃO", "msg": str(e)}

@app.route("/")
def index():
    # Tenta listar os arquivos para ver se a chave service_role está funcionando
    list_url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}"}
    res_list = requests.post(list_url, headers=headers, json={"prefix": ""})
    
    resultados = []
    if res_list.status_code == 200:
        for item in res_list.json():
            nome = item['name']
            if nome != ".emptyFolderPlaceholder":
                info = testar_assinatura(nome)
                resultados.append({"nome": nome, "info": info})
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Diagnóstico de Storage</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: monospace; background: #121212; color: #00ff00; padding: 20px; }
            .card { border: 1px solid #333; padding: 15px; margin-bottom: 20px; background: #1e1e1e; }
            .url { color: #888; font-size: 11px; word-break: break-all; background: #000; padding: 5px; display: block; margin: 10px 0; }
            img { max-width: 200px; border: 1px solid #00ff00; display: block; margin-top: 10px; }
            .erro { color: #ff4444; }
        </style>
    </head>
    <body>
        <h1>Supabase Stress Test V2</h1>
        <p>Bucket: {{ bucket }}</p>

        {% for item in resultados %}
        <div class="card">
            <strong>Ficheiro:</strong> {{ item.nome }} <br>
            <strong>Status Assinatura:</strong> {{ item.info.status }}
            
            {% if "OK" in item.info.status %}
                <span class="url">{{ item.info.url }}</span>
                <img src="{{ item.info.url }}" alt="Erro de renderização">
            {% else %}
                <p class="erro">Motivo: {{ item.info.msg }}</p>
            {% endif %}
        </div>
        {% endfor %}
        
        <br><a href="/" style="color: white;">Recarregar Teste</a>
    </body>
    </html>
    """
    return render_template_string(html, resultados=resultados, bucket=BUCKET_NAME)

if __name__ == "__main__":
    app.run(debug=True)

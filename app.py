import os
import requests
import urllib.parse
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configurações extraídas do seu .env
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
BUCKET_NAME = os.getenv("BUCKET_NAME", "").strip()

def gerar_link_corrigido(nome_arquivo):
    """
    Gera o link assinado e reconstrói a URL injetando o prefixo /storage/v1
    que a API costuma omitir, causando o 'Invalid Path'.
    """
    # 1. Nome do arquivo como está no bucket
    nome_puro = urllib.parse.unquote(nome_arquivo).strip()
    
    # 2. Endpoint de solicitação da assinatura
    url_request = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{nome_puro}"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Solicitamos validade de 1 hora
        res = requests.post(url_request, headers=headers, json={"expiresIn": 3600}, timeout=10)
        
        if res.status_code == 200:
            link_relativo = res.json().get("signedURL") # Ex: /object/sign/arquivos/foto.jpg...
            
            # A CORREÇÃO:
            # Se a API devolver o link sem o prefixo /storage/v1, nós o adicionamos manualmente.
            # Isso garante que a URL fique idêntica à que funciona no seu painel.
            if not link_relativo.startswith("/storage/v1"):
                link_corrigido = f"/storage/v1{link_relativo}"
            else:
                link_corrigido = link_relativo
            
            url_final = f"{SUPABASE_URL}{link_corrigido}"
            
            return {"status": "✅ SUCESSO", "url": url_final}
        else:
            return {"status": f"❌ ERRO {res.status_code}", "msg": res.text}
            
    except Exception as e:
        return {"status": "❌ FALHA", "msg": str(e)}

@app.route("/")
def index():
    # Listar arquivos para teste
    list_url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}"}
    
    resultados = []
    try:
        res_list = requests.post(list_url, headers=headers, json={"prefix": ""}, timeout=10)
        if res_list.status_code == 200:
            ficheiros = res_list.json()
            for f in ficheiros[-5:]: # Testar os últimos 5
                if f['name'] != ".emptyFolderPlaceholder":
                    diag = gerar_link_corrigido(f['name'])
                    resultados.append({"nome": f['name'], "diag": diag})
        else:
            return f"Erro Supabase List: {res_list.text}"
    except Exception as e:
        return f"Erro Conexão: {e}"

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stress Test V7 - Final Path Fix</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f1f5f9; padding: 20px; }
            .card { background: #1e293b; border: 1px solid #334155; padding: 20px; margin-bottom: 25px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
            .url-box { background: #020617; padding: 12px; font-size: 11px; word-break: break-all; color: #94a3b8; border-radius: 6px; margin: 15px 0; border: 1px solid #1e293b; }
            img { max-width: 100%; border: 3px solid #334155; border-radius: 8px; margin-top: 10px; }
            .success { color: #4ade80; font-weight: bold; }
            .info { color: #38bdf8; font-size: 13px; }
        </style>
    </head>
    <body>
        <h1>🚀 Stress Test V7: O Ajuste Final</h1>
        <p class="info">Injetando <code>/storage/v1</code> na reconstrução da URL.</p>
        <hr style="border-color: #334155;">

        {% for r in resultados %}
        <div class="card">
            <strong>Arquivo:</strong> {{ r.nome }} <br>
            <strong>Status:</strong> <span class="success">{{ r.diag.status }}</span>
            
            {% if r.diag.url %}
                <div class="url-box">{{ r.diag.url }}</div>
                <img src="{{ r.diag.url }}" alt="Se você vê isso, o Invalid Path foi corrigido!">
            {% else %}
                <p style="color:#f87171;">Erro: {{ r.diag.msg }}</p>
            {% endif %}
        </div>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html, resultados=resultados)

if __name__ == "__main__":
    app.run(debug=True)

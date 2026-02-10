import os
import requests
import urllib.parse
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configurações do Render
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
BUCKET_NAME = os.getenv("BUCKET_NAME", "").strip()

def gerar_link_puro(nome_arquivo):
    """
    Pede a assinatura sem qualquer manipulação de string no nome.
    O objetivo é ver o que a API devolve exatamente.
    """
    # Nome exatamente como vem da lista do bucket
    nome_cru = nome_arquivo
    
    # Endpoint de solicitação
    url_request = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{nome_cru}"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Pedimos validade de 1 hora
        res = requests.post(url_request, headers=headers, json={"expiresIn": 3600}, timeout=10)
        
        if res.status_code == 200:
            link_relativo = res.json().get("signedURL") # Ex: /storage/v1/object/sign/...
            
            # Montagem do link final unindo o domínio ao caminho relativo
            # O lstrip('/') garante que não haja duas barras após o domínio
            url_final = f"{SUPABASE_URL}/{link_relativo.lstrip('/')}"
            
            return {"status": "✅ SUCESSO", "url": url_final, "debug": "Link gerado via API."}
        else:
            return {"status": f"❌ ERRO {res.status_code}", "url": None, "debug": res.text}
            
    except Exception as e:
        return {"status": "❌ FALHA CRÍTICA", "url": None, "debug": str(e)}

@app.route("/")
def index():
    # 1. Listar ficheiros reais do bucket
    list_url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}"}
    
    lista_resultados = []
    try:
        res_list = requests.post(list_url, headers=headers, json={"prefix": ""}, timeout=10)
        if res_list.status_code == 200:
            ficheiros = res_list.json()
            # Testamos os últimos 3 para comparação
            for f in ficheiros[-3:]:
                if f['name'] != ".emptyFolderPlaceholder":
                    diag = gerar_link_puro(f['name'])
                    lista_resultados.append({"nome": f['name'], "diag": diag})
        else:
            return f"Erro ao aceder ao Supabase: {res_list.text}"
    except Exception as e:
        return f"Erro de ligação: {str(e)}"

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Investigação Supabase V6</title>
        <style>
            body { font-family: monospace; background: #000; color: #0f0; padding: 20px; }
            .box { border: 1px solid #333; padding: 15px; margin-bottom: 30px; background: #0a0a0a; }
            .url { color: #888; font-size: 11px; word-break: break-all; background: #111; padding: 10px; display: block; margin: 10px 0; border: 1px dashed #444; }
            img { max-width: 300px; display: block; margin-top: 10px; border: 1px solid #0f0; }
            .label { color: yellow; font-weight: bold; }
        </style>
    </head>
    <body>
        <h2>🕵️ Investigação de Links (V6)</h2>
        <p>URL Base: {{ base }} | Bucket: {{ bucket }}</p>
        <hr>

        {% for r in resultados %}
        <div class="box">
            <span class="label">Ficheiro:</span> {{ r.nome }} <br>
            <span class="label">Status API:</span> {{ r.diag.status }} <br>
            
            {% if r.diag.url %}
                <span class="label">Link Gerado (Copie e compare):</span>
                <span class="url">{{ r.diag.url }}</span>
                
                <span class="label">Pré-visualização:</span><br>
                <img src="{{ r.diag.url }}" alt="Erro: Path Invalid no navegador">
            {% else %}
                <p style="color:red">Debug: {{ r.diag.debug }}</p>
            {% endif %}
        </div>
        {% endfor %}

        <div style="background: #222; padding: 15px; border-radius: 5px; color: white;">
            <strong>Como testar o "Erro Ridículo":</strong><br>
            1. Abra o painel do Supabase e gere um link manual para o ficheiro <u>{{ resultados[0].nome if resultados else 'acima' }}</u>.<br>
            2. Copie esse link manual.<br>
            3. Copie o link cinzento gerado acima pelo site.<br>
            4. Compare os dois num bloco de notas.<br>
            5. O caminho entre o domínio e o <code>?token=</code> tem de ser exatamente igual.
        </div>
    </body>
    </html>
    """
    return render_template_string(html, resultados=lista_resultados, base=SUPABASE_URL, bucket=BUCKET_NAME)

if __name__ == "__main__":
    app.run(debug=True)

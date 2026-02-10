import os, requests, urllib.parse
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
BUCKET_NAME = os.getenv("BUCKET_NAME", "").strip()

def testar_variantes(nome_arquivo):
    nome_puro = urllib.parse.unquote(nome_arquivo).strip()
    url_request = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{nome_puro}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    
    try:
        res = requests.post(url_request, headers=headers, json={"expiresIn": 3600})
        if res.status_code == 200:
            link_relativo = res.json().get("signedURL").lstrip('/')
            
            # TESTAMOS 3 CONSTRUÇÕES DIFERENTES
            v1 = f"{SUPABASE_URL}/{link_relativo}" # Padrão
            v2 = f"{SUPABASE_URL}/storage/v1/object/sign/{link_relativo}" # Forçado
            v3 = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{nome_puro}" # Teste Público
            
            return {"status": "✅", "v1": v1, "v2": v2, "v3": v3}
        return {"status": "❌", "erro": res.text}
    except Exception as e:
        return {"status": "❌", "erro": str(e)}

@app.route("/")
def index():
    # Listar arquivos
    res_list = requests.post(f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}", 
                             headers={"Authorization": f"Bearer {SUPABASE_KEY}"}, 
                             json={"prefix": ""})
    
    resultados = []
    if res_list.status_code == 200:
        for item in res_list.json()[:3]: # Testar apenas os 3 primeiros para não poluir
            nome = item['name']
            if nome != ".emptyFolderPlaceholder":
                resultados.append({"nome": nome, "testes": testar_variantes(nome)})

    html = """
    <body style="background:#000; color:#0f0; font-family:monospace; padding:20px;">
        <h2>INVESTIGAÇÃO DE PATH INVALID</h2>
        {% for r in resultados %}
            <div style="border:1px solid #333; padding:10px; margin-bottom:20px;">
                <strong>Arquivo:</strong> {{ r.nome }} <br>
                {% if r.testes.status == '✅' %}
                    <p>Variante 1 (Normal): <a href="{{ r.testes.v1 }}" style="color:cyan" target="_blank">Testar</a></p>
                    <p>Variante 2 (Full Path): <a href="{{ r.testes.v2 }}" style="color:cyan" target="_blank">Testar</a></p>
                    <p>Variante 3 (Public - Só funciona se bucket for public): <a href="{{ r.testes.v3 }}" style="color:cyan" target="_blank">Testar</a></p>
                {% else %}
                    <p style="color:red">Erro: {{ r.testes.erro }}</p>
                {% endif %}
            </div>
        {% endfor %}
    </body>
    """
    return render_template_string(html, resultados=resultados)

if __name__ == "__main__":
    app.run(debug=True)

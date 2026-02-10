import os
import requests
from flask import Flask, request, render_template_string, redirect, url_for
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "teste_stress_supabase"

# Variáveis de Ambiente (Mantenha as mesmas no Render)
SUPABASE_URL = os.getenv("SUPABASE_URL").strip().rstrip('/')
SUPABASE_KEY = os.getenv("SUPABASE_KEY").strip()
BUCKET_NAME = os.getenv("BUCKET_NAME").strip()

def obter_link_direto(nome_arquivo):
    """Solicita URL assinada pura ao Supabase."""
    url = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{nome_arquivo}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    
    try:
        res = requests.post(url, headers=headers, json={"expiresIn": 600})
        if res.status_code == 200:
            link_relativo = res.json().get("signedURL")
            # Garante que o link seja absoluto para o navegador não se perder
            return f"{SUPABASE_URL}{link_relativo}"
        return f"Erro Supabase: {res.status_code} - {res.text}"
    except Exception as e:
        return f"Erro de Conexão: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def index():
    log_upload = ""
    
    # Lógica de Upload
    if request.method == "POST":
        file = request.files.get("foto")
        if file:
            filename = f"teste_{datetime.now().strftime('%H%M%S')}_{file.filename}"
            upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}"
            headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": file.content_type}
            
            res = requests.post(upload_url, headers=headers, data=file.read())
            if res.status_code == 200:
                log_upload = f"✅ Sucesso: {filename} enviado!"
            else:
                log_upload = f"❌ Falha: {res.status_code} - {res.text}"

    # Lógica de Listagem (Para testar se a chave lê o bucket)
    list_url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}"}
    res_list = requests.post(list_url, headers=headers, json={"prefix": ""})
    
    arquivos_links = []
    if res_list.status_code == 200:
        for item in res_list.json():
            nome = item['name']
            if nome != ".emptyFolderPlaceholder":
                link = obter_link_direto(nome)
                arquivos_links.append({"nome": nome, "url": link})

    # Interface Ultra Simples
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TESTE DE STRESS SUPABASE</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; padding: 20px; background: #f0f0f0; }
            .card { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #ccc; }
            img { max-width: 100%; border: 2px solid red; margin-top: 10px; }
            .debug { font-size: 10px; color: gray; word-break: break-all; }
        </style>
    </head>
    <body>
        <h1>Stress Test: Storage</h1>
        <p>URL: {{ url_base }} | Bucket: {{ bucket }}</p>
        
        <div class="card">
            <h3>1. Testar Upload</h3>
            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="foto">
                <button type="submit">Enviar Foto</button>
            </form>
            <p>{{ log_upload }}</p>
        </div>

        <div class="card">
            <h3>2. Arquivos no Bucket (Com links assinados)</h3>
            {% for arq in lista %}
                <div style="margin-bottom: 30px; border-bottom: 1px solid #eee;">
                    <b>Nome:</b> {{ arq.nome }} <br>
                    <p class="debug">URL GERADA: {{ arq.url }}</p>
                    {% if "http" in arq.url %}
                        <img src="{{ arq.url }}" alt="Erro ao renderizar tag img">
                    {% else %}
                        <p style="color:red">Link inválido gerado</p>
                    {% endif %}
                </div>
            {% endfor %}
        </div>
        
        <a href="/">Atualizar Página</a>
    </body>
    </html>
    """
    return render_template_string(html, 
                                log_upload=log_upload, 
                                lista=arquivos_links, 
                                url_base=SUPABASE_URL, 
                                bucket=BUCKET_NAME)

if __name__ == "__main__":
    app.run(debug=True)

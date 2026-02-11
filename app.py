# ==========================================
# BLOCO 1: IMPORTAÇÕES E CONFIGURAÇÕES INICIAIS
# ==========================================
import os
import psycopg2
import requests
import random
import string
import re
import urllib.parse
from flask import Flask, request, render_template_string, session, redirect, url_for, make_response
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cafe_com_seguranca_2026") 
app.permanent_session_lifetime = timedelta(hours=2) # TTL de 2 horas

# Variáveis de Ambiente
SENHA_ELE = os.getenv("SENHA_ELE")
SENHA_ELA = os.getenv("SENHA_ELA")
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# ==========================================
# BLOCO 2: UTILITÁRIOS E CONEXÕES
# ==========================================
def get_db_connection():
    """Estabelece a conexão com o PostgreSQL (Removida duplicata)."""
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)

def obter_url_assinada(path_ou_url):
    """Gera URL temporária via Supabase API (Expira em 1h)."""
    if not path_ou_url:
        return None
    
    nome_arquivo = path_ou_url.split('/')[-1].strip()
    nome_limpo = urllib.parse.unquote(nome_arquivo)
    
    url_request = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{nome_limpo}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    
    try:
        res = requests.post(url_request, headers=headers, json={"expiresIn": 3600}, timeout=10)
        if res.status_code == 200:
            link_relativo = res.json().get("signedURL")
            link_corrigido = f"/storage/v1{link_relativo}" if link_relativo and not link_relativo.startswith("/storage/v1") else link_relativo
            return f"{SUPABASE_URL}{link_corrigido}"
    except Exception as e:
        print(f"Erro na assinatura: {e}")
    return None

# ==========================================
# BLOCO 3: GESTÃO DE ACESSO (LOGIN/LOGOUT)
# ==========================================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session.clear() # Limpeza de rastros ao carregar login
        
    id_campo = ''.join(random.choices(string.ascii_letters, k=6))

    if request.method == "POST":
        # Captura dinâmica da senha ignorando o ID aleatório
        senha_digitada = next((val for key, val in request.form.items() if key.startswith('pass_')), None)
        
        if senha_digitada in [SENHA_ELE, SENHA_ELA]:
            session.permanent = True
            session["senha"] = senha_digitada
            return redirect(url_for("chat"))
        
        return render_template_string(HTML_LOGIN, erro="Senha incorreta.", id=id_campo)

    return render_template_string(HTML_LOGIN, id=id_campo)

@app.route("/sair")
def sair():
    session.clear() # Destruição de estado
    return redirect(url_for("login"))

# Template Login com Detecção de Quota (Navegação Anônima)
HTML_LOGIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Cofre Privado</title>
    <style>
        body { background: #0b141a; color: white; font-family: sans-serif; margin: 0; display: flex; align-items: center; justify-content: center; height: 100vh; overflow: hidden; }
        .container { width: 90%; max-width: 400px; text-align: center; }
        input[type="password"] { width: 100%; padding: 22px; font-size: 20px; border-radius: 15px; border: 2px solid #2a3942; background: #2a3942; color: white; box-sizing: border-box; text-align: center; margin-bottom: 15px; outline: none; }
        button { width: 100%; padding: 22px; font-size: 18px; font-weight: bold; border-radius: 15px; border: none; background: #00a884; color: white; cursor: pointer; }
        #bloqueio { display: none; background: #111b21; padding: 40px 20px; border-radius: 25px; border: 1px solid #ef5350; }
        #form-login { display: none; }
        .erro { color: #ef5350; background: rgba(239, 83, 80, 0.1); padding: 10px; border-radius: 8px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div id="loader">Validando segurança...</div>
        <div id="bloqueio">
            <h2>🛡️ Acesso Restrito</h2>
            <p>Use o <b>Modo Anônimo</b> para entrar no cofre.</p>
        </div>
        <div id="form-login">
            <h2>🔐 Cofre Privado</h2>
            {% if erro %}<div class="erro">{{ erro }}</div>{% endif %}
            <form method="POST" autocomplete="off">
                <input type="password" name="pass_{{ id }}" placeholder="Senha" autofocus autocomplete="new-password">
                <button type="submit">ENTRAR</button>
            </form>
        </div>
    </div>
    <script>
        async function verificarSeguranca() {
            if ('storage' in navigator && 'estimate' in navigator.storage) {
                const {quota} = await navigator.storage.estimate();
                const quotaMB = Math.round(quota / (1024 * 1024));
                document.getElementById('loader').style.display = 'none';
                if (quotaMB < 1200) { document.getElementById('form-login').style.display = 'block'; }
                else { document.getElementById('bloqueio').style.display = 'block'; }
            }
        }
        setTimeout(verificarSeguranca, 600);
    </script>
</body>
</html>
"""

# ==========================================
# BLOCO 4: NÚCLEO DO CHAT
# ==========================================

@app.route("/chat", methods=["GET", "POST"])
def chat():
    senha = session.get('senha')
    if not senha: return redirect(url_for('login'))
    
    if senha == SENHA_ELE: meu_nome, cor_minha, cor_outra, parceiro = "Ele", "#005c4b", "#202c33", "Ela"
    else: meu_nome, cor_minha, cor_outra, parceiro = "Ela", "#c2185b", "#202c33", "Ele"

    if request.method == "POST":
        msg = request.form.get("msg", "")
        file = request.files.get("arquivo")
        file_ref = None
        
        if file and file.filename != "":
            nome_limpo = re.sub(r'[^a-zA-Z0-9._-]', '', file.filename.replace(" ", "_"))
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nome_limpo}"
            upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}"
            headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": file.content_type}
            res = requests.post(upload_url, headers=headers, data=file.read())
            if res.status_code == 200: file_ref = filename

        if msg.strip() or file_ref:
            hora_atual = (datetime.utcnow() - timedelta(hours=3)).strftime('%d/%m %H:%M')
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO mensagens (autor, texto, data, arquivo_url) VALUES (%s, %s, %s, %s)", 
                        (meu_nome, msg, hora_atual, file_ref))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('chat'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT autor, texto, data, arquivo_url FROM mensagens ORDER BY id DESC LIMIT 50")
    msgs_raw = cur.fetchall()
    cur.close()
    conn.close()

    msgs_processadas = []
    for m in msgs_raw:
        url_segura = obter_url_assinada(m[3]) if m[3] else None
        msgs_processadas.append((m[0], m[1], m[2], url_segura))
    
    return renderizar_interface(msgs_processadas[::-1], meu_nome, cor_minha, cor_outra, parceiro)

def renderizar_interface(msgs, meu_nome, cor_minha, cor_outra, parceiro):
    resp = make_response(render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                body { font-family: sans-serif; margin: 0; background: #0b141a; color: #e9edef; }
                .header { background: #202c33; padding: 10px; position: sticky; top:0; z-index:100; display: flex; justify-content: space-between; align-items: center; }
                .chat-container { display: flex; flex-direction: column; padding: 10px; margin-bottom: 80px; }
                .msg-row { display: flex; margin-bottom: 12px; }
                .mine { justify-content: flex-end; }
                .mine .bubble { background: {{cor_minha}}; border-radius: 12px 0 12px 12px; }
                .other { justify-content: flex-start; }
                .other .bubble { background: {{cor_outra}}; border-radius: 0 12px 12px 12px; }
                .bubble { max-width: 85%; padding: 8px 12px; font-size: 15px; }
                .media-bar { background: #111b21; padding: 10px; display: flex; gap: 8px; overflow-x: auto; border-bottom: 1px solid #222; }
                .img-thumb { width: 60px; height: 60px; object-fit: cover; border-radius: 8px; }
                .footer { position: fixed; bottom: 0; width: 100%; background: #202c33; padding: 10px; display: flex; align-items: center; box-sizing: border-box; }
                .input-msg { flex: 1; background: #2a3942; border: none; padding: 12px; border-radius: 25px; color: white; margin: 0 10px; }
                #overlay { position: fixed; display: none; width: 100%; height: 100%; top: 0; left: 0; background: rgba(0,0,0,0.9); z-index: 2000; justify-content: center; align-items: center; }
            </style>
        </head>
        <body oncontextmenu="return false;">
            <div class="header">
                <div style="display:flex; align-items:center;">
                    <div style="width:35px; height:35px; background:{{cor_minha}}; border-radius:50%; margin-right:10px; display:flex; align-items:center; justify-content:center;">{{parceiro[0]}}</div>
                    <b>{{parceiro}}</b>
                </div>
                <a href="/sair" style="color:#8696a0;"><i class="fa-solid fa-right-from-bracket"></i></a>
            </div>
            <div class="media-bar">
                {% for m in msgs if m[3] %}<img src="{{m[3]}}" class="img-thumb" onclick="openImg('{{m[3]}}')">{% endfor %}
            </div>
            <div class="chat-container">
                {% for m in msgs %}
                <div class="msg-row {% if m[0] == meu_nome %}mine{% else %}other{% endif %}">
                    <div class="bubble">
                        {% if m[1] %}<div>{{m[1]}}</div>{% endif %}
                        {% if m[3] %}<div style="color:#00a884; margin-top:5px;" onclick="openImg('{{m[3]}}')"><i class="fa-solid fa-camera"></i> Foto</div>{% endif %}
                        <small style="opacity:0.5; float:right; margin-top:5px;">{{ m[2] }}</small>
                    </div>
                </div>
                {% endfor %}
            </div>
            <div id="overlay" onclick="closeImg()"><img id="imgFull" style="max-width:95%; max-height:95%;"></div>
            <form method="POST" enctype="multipart/form-data" class="footer">
                <label for="arquivo" style="color:#8696a0; font-size:22px;"><i class="fa-solid fa-paperclip"></i></label>
                <input type="file" id="arquivo" name="arquivo" style="display:none">
                <input type="text" name="msg" id="msgInput" class="input-msg" placeholder="Mensagem" autocomplete="off">
                <button type="submit" style="background:none; border:none; color:#00a884; font-size:22px;"><i class="fa-solid fa-paper-plane"></i></button>
            </form>
            <script>
                window.scrollTo(0, document.body.scrollHeight);
                function openImg(src) { document.getElementById('imgFull').src = src; document.getElementById('overlay').style.display = 'flex'; }
                function closeImg() { document.getElementById('overlay').style.display = 'none'; }
                setInterval(() => {
                    if (document.activeElement.tagName !== 'INPUT' && document.getElementById('overlay').style.display !== 'flex') {
                        window.location.reload();
                    }
                }, 10000);
            </script>
        </body>
        </html>
    """, msgs=msgs, meu_nome=meu_nome, cor_minha=cor_minha, cor_outra=cor_outra, parceiro=parceiro))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # Proteção contra botão "Voltar"
    return resp

if __name__ == "__main__":
    app.run(debug=False)

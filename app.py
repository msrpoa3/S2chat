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
app.permanent_session_lifetime = timedelta(hours=2)

# Variáveis de Ambiente
SENHA_ELE = os.getenv("SENHA_ELE")
SENHA_ELA = os.getenv("SENHA_ELA")
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)

# ==========================================
# BLOCO 2: UTILITÁRIOS E CONEXÕES
# ==========================================
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)

# ==========================================
# BLOCO 3: GESTÃO DE ACESSO (LOGIN/LOGOUT)
# ==========================================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session.clear()
        
    id_campo = ''.join(random.choices(string.ascii_letters, k=6))

    if request.method == "POST":
        senha_digitada = next((val for key, val in request.form.items() if key.startswith('pass_')), None)
        
        if senha_digitada in [SENHA_ELE, SENHA_ELA]:
            session.permanent = True
            session["senha"] = senha_digitada
            return redirect(url_for("chat"))
        
        return render_template_string(HTML_LOGIN, erro="Senha incorreta.", id=id_campo)

    return render_template_string(HTML_LOGIN, id=id_campo)

@app.route("/sair")
def sair():
    session.clear()
    return redirect("https://www.google.com")

# Template de Login com Limpeza Anti-Rastro
HTML_LOGIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body { background: #0b141a; color: white; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .container { width: 90%; max-width: 400px; text-align: center; }
        input { width: 100%; padding: 22px; font-size: 20px; border-radius: 15px; border: 2px solid #2a3942; background: #2a3942; color: white; box-sizing: border-box; text-align: center; margin-bottom: 15px; }
        button { width: 100%; padding: 22px; background: #00a884; color: white; border: none; border-radius: 15px; font-weight: bold; cursor: pointer; }
        #bloqueio, #form-login { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div id="loader">Validando segurança...</div>
        <div id="bloqueio"><h2>Acesso Restrito</h2><p>Use o Modo Anônimo.</p></div>
        <div id="form-login">
            <h2 style="font-weight: 300;">Cofre Privado</h2>
            <form method="POST" id="loginForm" autocomplete="off">
                <input type="password" name="pass_{{ id }}" id="passField" placeholder="Senha" required autocomplete="new-password">
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
        document.getElementById('loginForm').onsubmit = function() {
            setTimeout(() => { document.getElementById('passField').value = ''; }, 10);
        };
        setTimeout(verificarSeguranca, 600);
    </script>
</body>
</html>
"""

# ==========================================
# BLOCO 4: NÚCLEO DO CHAT (LÓGICA E STORAGE)
# ==========================================

def obter_url_assinada(path_ou_url):
    """Gera URL temporária via Supabase."""
    if not path_ou_url: return None
    nome_arquivo = path_ou_url.split('/')[-1].strip()
    nome_limpo = urllib.parse.unquote(nome_arquivo)
    url_request = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{nome_limpo}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    try:
        res = requests.post(url_request, headers=headers, json={"expiresIn": 3600}, timeout=10)
        if res.status_code == 200:
            link = res.json().get("signedURL")
            return f"{SUPABASE_URL}{link if link.startswith('/storage/v1') else '/storage/v1'+link}"
    except: return None
    return None

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
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                body { font-family: 'Segoe UI', sans-serif; margin: 0; background-color: #0b141a; color: #e9edef; overflow-x: hidden; }
                .header { background: #202c33; padding: 10px 15px; display: flex; align-items: center; position: sticky; top:0; z-index:100; justify-content: space-between; }
                .chat-container { display: flex; flex-direction: column; padding: 10px; margin-bottom: 80px; }
                .msg-row { display: flex; margin-bottom: 12px; }
                .msg-bubble { max-width: 85%; padding: 8px 12px; border-radius: 12px; position: relative; }
                .mine { justify-content: flex-end; } .mine .msg-bubble { background: {{cor_minha}}; border-top-right-radius: 0; }
                .other { justify-content: flex-start; } .other .msg-bubble { background: {{cor_outra}}; border-top-left-radius: 0; }
                
                /* Privacidade */
                body.blur-active .msg-canvas, body.blur-active .img-thumb, body.blur-active .photo-label { filter: blur(10px); transition: 0.2s; }
                body.blur-active .msg-bubble:active .msg-canvas, body.blur-active .img-thumb:active { filter: blur(0); }
                
                .media-bar { background: #111b21; padding: 10px; display: flex; gap: 8px; overflow-x: auto; border-bottom: 1px solid #222; }
                .img-thumb { width: 60px; height: 60px; object-fit: cover; border-radius: 8px; }
                .footer { position: fixed; bottom: 0; width: 100%; background: #202c33; padding: 10px; display: flex; align-items: center; box-sizing: border-box; }
                .input-msg { flex: 1; background: #2a3942; border: none; padding: 12px; border-radius: 25px; color: white; margin: 0 10px; outline: none; }
                #overlay { position: fixed; display: none; width: 100%; height: 100%; top: 0; left: 0; background: rgba(0,0,0,0.95); z-index: 2000; justify-content: center; align-items: center; }
            </style>
        </head>
        <body oncontextmenu="return false;">
            <div class="header">
                <div style="display:flex; align-items:center;">
                    <div style="width:35px; height:35px; background:{{cor_minha}}; border-radius:50%; margin-right:10px; display:flex; align-items:center; justify-content:center; font-weight:bold;">{{parceiro[0]}}</div>
                    <div><span style="font-weight:bold;">{{parceiro}}</span><br><small style="color:#00a884;">online</small></div>
                </div>
                <div style="display:flex; gap: 20px;">
                    <i class="fa-solid fa-eye" id="privacyBtn" onclick="togglePrivacy()" style="cursor:pointer; color:#8696a0; font-size:20px;"></i>
                    <a href="/sair" style="color:#8696a0; font-size:20px;"><i class="fa-solid fa-right-from-bracket"></i></a>
                </div>
            </div>

            <div class="media-bar">
                {% for m in msgs if m[3] %}<img src="{{m[3]}}" class="img-thumb" onclick="openImg('{{m[3]}}')">{% endfor %}
            </div>

            <div class="chat-container" id="chat">
                {% for m in msgs %}
                <div class="msg-row {% if m[0] == meu_nome %}mine{% else %}other{% endif %}">
                    <div class="msg-bubble">
                        {% if m[1] %}<canvas class="msg-canvas" data-raw="{{m[1]}}"></canvas>{% endif %}
                        {% if m[3] %}<div class="photo-label" style="margin-top:5px; color:#00a884; font-weight:bold;" onclick="openImg('{{m[3]}}')"><i class="fa-solid fa-camera"></i> Foto</div>{% endif %}
                        <span style="font-size: 0.65em; color: rgba(255,255,255,0.4); display: block; text-align: right; margin-top: 5px;">{{ m[2] }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>

            <div id="overlay" onclick="closeImg()"><img id="imgFull" style="max-width:100%; max-height:100%;"></div>

            <form method="POST" enctype="multipart/form-data" class="footer" id="mainForm" autocomplete="off">
                <label for="arquivo" style="color:#8696a0; font-size:22px;"><i class="fa-solid fa-paperclip"></i></label>
                <input type="file" id="arquivo" name="arquivo" style="display:none">
                <input type="text" name="msg" id="msgInput" class="input-msg" placeholder="Mensagem" autocomplete="off">
                <button type="submit" style="background:none; border:none; color:#00a884; font-size:22px;"><i class="fa-solid fa-paper-plane"></i></button>
            </form>

            <script>
                function drawCanvas() {
                    const maxWidth = window.innerWidth * 0.7;
                    document.querySelectorAll('.msg-canvas').forEach(canvas => {
                        const ctx = canvas.getContext('2d');
                        const text = canvas.getAttribute('data-raw');
                        const fontSize = 16;
                        ctx.font = fontSize + "px Segoe UI";
                        
                        const words = text.split(' ');
                        let line = '', lines = [], testLine, metrics;
                        for (let n = 0; n < words.length; n++) {
                            testLine = line + words[n] + ' ';
                            metrics = ctx.measureText(testLine);
                            if (metrics.width > maxWidth && n > 0) { lines.push(line); line = words[n] + ' '; }
                            else { line = testLine; }
                        }
                        lines.push(line);

                        canvas.width = Math.min(maxWidth, ctx.measureText(text).width + 10);
                        canvas.height = lines.length * (fontSize + 6);
                        ctx.fillStyle = "white";
                        ctx.font = fontSize + "px Segoe UI";
                        ctx.textBaseline = "top";
                        lines.forEach((l, i) => ctx.fillText(l.trim(), 0, i * (fontSize + 6)));
                    });
                }

                function togglePrivacy() {
                    document.body.classList.toggle('blur-active');
                    const icon = document.getElementById('privacyBtn');
                    icon.className = document.body.classList.contains('blur-active') ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye';
                }

                document.getElementById('mainForm').onsubmit = function() {
                    setTimeout(() => { document.getElementById('msgInput').value = ''; }, 10);
                };

                function openImg(src) { document.getElementById('imgFull').src = src; document.getElementById('overlay').style.display = 'flex'; }
                function closeImg() { document.getElementById('overlay').style.display = 'none'; }

                window.onload = () => { drawCanvas(); window.scrollTo(0, document.body.scrollHeight); };
            </script>
        </body>
        </html>
    """, msgs=msgs, meu_nome=meu_nome, cor_minha=cor_minha, cor_outra=cor_outra, parceiro=parceiro))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp

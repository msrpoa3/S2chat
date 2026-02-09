# ==========================================
# BLOCO 1: IMPORTAÇÕES E CONFIGURAÇÕES INICIAIS
# ==========================================
import os
import psycopg2
import requests
import random
import string
from flask import Flask, request, render_template_string, session, redirect, url_for, make_response
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = "cafe_com_seguranca_2026" 
app.permanent_session_lifetime = timedelta(hours=2)

# Variáveis de Ambiente
SENHA_ELE = os.getenv("SENHA_ELE")
SENHA_ELA = os.getenv("SENHA_ELA")
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

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
    if request.method == "POST":
        senha_digitada = next((val for key, val in request.form.items() if key.startswith('pass_')), None)
        if senha_digitada in [SENHA_ELE, SENHA_ELA]:
            session.permanent = True
            session['senha'] = senha_digitada
            return redirect(url_for('chat'))
        return 'Senha incorreta. <a href="/">Tentar novamente</a>'
    
    session.clear()
    campo_id = ''.join(random.choices(string.ascii_letters, k=8))
    return render_template_string('''
        <body style="background:#0b141a; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
            <div style="background:#202c33; padding:30px; border-radius:15px; text-align:center; box-shadow:0 10px 20px rgba(0,0,0,0.5);">
                <h2 style="color:#e9edef;">Cofre Privado</h2>
                <form method="POST" autocomplete="off">
                    <input type="password" name="pass_{{id}}" id="senha_campo" placeholder="Sua Senha" 
                           autocomplete="new-password" style="padding:12px; border-radius:8px; border:none; width:200px; font-size:16px;" required>
                    <button type="submit" style="display:block; width:100%; margin-top:15px; padding:12px; background:#00a884; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">Entrar</button>
                </form>
            </div>
            <script>window.onload = () => { document.getElementById('senha_campo').value = ""; };</script>
        </body>
    ''', id=campo_id)

@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for('login'))

# ==========================================
# BLOCO 4: NÚCLEO DO CHAT (LÓGICA E STORAGE)
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
        file_url = None
        
        # Upload para Supabase
        if file and file.filename != "":
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}"
            headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": file.content_type}
            res = requests.post(upload_url, headers=headers, data=file.read())
            if res.status_code == 200:
                file_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{filename}"

        # Persistência no Banco
        if msg.strip() or file_url:
            hora_atual = (datetime.utcnow() - timedelta(hours=3)).strftime('%d/%m %H:%M')
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO mensagens (autor, texto, data, arquivo_url) VALUES (%s, %s, %s, %s)", 
                        (meu_nome, msg, hora_atual, file_url))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('chat'))

    # Busca de Mensagens
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT autor, texto, data, arquivo_url FROM mensagens ORDER BY id DESC LIMIT 50")
    msgs_raw = cur.fetchall()
    cur.close()
    conn.close()

    # ==========================================
    # BLOCO 5: INTERFACE (HTML/CSS/JS)
    # ==========================================
    resp = make_response(render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                body { font-family: 'Segoe UI', sans-serif; margin: 0; background-color: #0b141a; color: #e9edef; overflow-x: hidden; }
                .header { background: #202c33; padding: 10px 20px; display: flex; align-items: center; position: sticky; top:0; z-index:100; justify-content: space-between; }
                .chat-container { display: flex; flex-direction: column; padding: 10px; margin-bottom: 80px; }
                .msg-row { display: flex; width: 100%; margin-bottom: 12px; }
                .msg-bubble { max-width: 85%; padding: 8px 12px; border-radius: 12px; font-size: 15px; }
                .mine { justify-content: flex-end; }
                .mine .msg-bubble { background: {{cor_minha}}; border-top-right-radius: 0; }
                .other { justify-content: flex-start; }
                .other .msg-bubble { background: {{cor_outra}}; border-top-left-radius: 0; }
                .time { font-size: 0.65em; color: rgba(255,255,255,0.4); text-align: right; margin-top: 5px; display: block; }
                .footer { position: fixed; bottom: 0; width: 100%; background: #202c33; padding: 10px; display: flex; align-items: center; box-sizing: border-box; }
                .input-msg { flex: 1; background: #2a3942; border: none; padding: 12px; border-radius: 25px; color: white; outline: none; margin: 0 10px; font-size: 16px; }
                .icon-btn { color: #8696a0; font-size: 22px; cursor: pointer; }
                .clip-active { color: #00a884 !important; }
                .media-bar { background: #111b21; padding: 10px; overflow-x: auto; display: flex; gap: 8px; border-bottom: 1px solid #222; white-space: nowrap; }
                .img-thumb { width: 60px; height: 60px; object-fit: cover; border-radius: 8px; flex-shrink: 0; border: 1px solid #333; }
                #overlay { position: fixed; display: none; width: 100%; height: 100%; top: 0; left: 0; background: rgba(0,0,0,0.98); z-index: 2000; justify-content: center; align-items: center; }
                #overlay img { max-width: 100%; max-height: 100%; }
                #cancelFile { display: none; color: #ef5350; margin-left: 5px; font-size: 18px; }
            </style>
        </head>
        <body oncontextmenu="return false;">
            <div class="header">
                <div style="display:flex; align-items:center;">
                    <div style="width:35px; height:35px; background:{{cor_minha}}; border-radius:50%; margin-right:12px; display:flex; align-items:center; justify-content:center; font-weight:bold;">{{parceiro[0]}}</div>
                    <div><span style="font-weight:bold;">{{parceiro}}</span><br><small style="color:#00a884;">online</small></div>
                </div>
                <a href="/sair" class="icon-btn"><i class="fa-solid fa-right-from-bracket"></i></a>
            </div>

            <div class="media-bar">
                {% for m in msgs if m[3] %}<img src="{{m[3]}}" class="img-thumb" onclick="openImg('{{m[3]}}')">{% endfor %}
            </div>

            <div class="chat-container" id="chat">
                {% for m in msgs|reverse %}
                <div class="msg-row {% if m[0] == meu_nome %}mine{% else %}other{% endif %}">
                    <div class="msg-bubble">
                        {% if m[1] %}<div style="word-wrap: break-word;">{{m[1]}}</div>{% endif %}
                        {% if m[3] %}<div style="margin-top:5px; color:#00a884; font-weight:bold; cursor:pointer;" onclick="openImg('{{m[3]}}')"><i class="fa-solid fa-camera"></i> Foto</div>{% endif %}
                        <span class="time">{{ m[2] }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>

            <div id="overlay" onclick="closeImg()"><img id="imgFull"></div>

            <form method="POST" enctype="multipart/form-data" class="footer" id="mainForm">
                <label for="arquivo" class="icon-btn" id="clipLabel"><i class="fa-solid fa-paperclip"></i></label>
                <i class="fa-solid fa-circle-xmark" id="cancelFile" onclick="clearFile()"></i>
                <input type="file" id="arquivo" name="arquivo" style="display:none" onchange="fileSelected()">
                <input type="text" name="msg" id="msgInput" class="input-msg" placeholder="Mensagem" autocomplete="off">
                <button type="submit" class="icon-btn" style="background:none; border:none;"><i class="fa-solid fa-paper-plane" style="color:#00a884;"></i></button>
            </form>

            <script>
                window.scrollTo(0, document.body.scrollHeight);
                let isOverlayOpen = false;
                let isWindowFocused = true;

                window.onfocus = () => { isWindowFocused = true; };
                window.onblur = () => { isWindowFocused = false; };

                function fileSelected() {
                    const fileInput = document.getElementById('arquivo');
                    if (fileInput.files.length > 0) {
                        document.getElementById('clipLabel').classList.add('clip-active');
                        document.getElementById('cancelFile').style.display = "inline";
                        document.getElementById('msgInput').placeholder = "Foto selecionada...";
                    }
                }

                function clearFile() {
                    document.getElementById('arquivo').value = "";
                    document.getElementById('clipLabel').classList.remove('clip-active');
                    document.getElementById('cancelFile').style.display = "none";
                    document.getElementById('msgInput').placeholder = "Mensagem";
                }

                function openImg(src) { document.getElementById('imgFull').src = src; document.getElementById('overlay').style.display = 'flex'; isOverlayOpen = true; }
                function closeImg() { document.getElementById('overlay').style.display = 'none'; isOverlayOpen = false; }

                setInterval(() => {
                    const hasFile = document.getElementById('arquivo').files.length > 0;
                    const hasText = document.getElementById('msgInput').value !== "";
                    if (document.activeElement.tagName !== 'INPUT' && !isOverlayOpen && !hasText && !hasFile && isWindowFocused) {
                        window.location.reload();
                    }
                }, 10000);
            </script>
        </body>
        </html>
    """, msgs=msgs_raw, meu_nome=meu_nome, cor_minha=cor_minha, cor_outra=cor_outra, parceiro=parceiro))
    
    # Headers de Cache
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

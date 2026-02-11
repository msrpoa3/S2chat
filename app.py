# ==========================================
# BLOCO 1: CONFIGURAÇÕES E AMBIENTE
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

# Carrega variáveis de ambiente (Senhas, URLs de DB e Supabase)
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cafe_com_seguranca_2026") 
app.permanent_session_lifetime = timedelta(hours=2) # Tempo de vida da sessão: 2h

# Variáveis de Ambiente
SENHA_ELE = os.getenv("SENHA_ELE")
SENHA_ELA = os.getenv("SENHA_ELA")
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

def get_db_connection():
    """Estabelece a conexão com o banco de dados PostgreSQL."""
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)

# ==========================================
# BLOCO 2: UTILITÁRIOS DE SEGURANÇA E MÍDIA
# ==========================================

def obter_url_assinada(path_ou_url):
    """Gera URL temporária e criptografada via Supabase que expira em 1 hora."""
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
            # Corrige o prefixo /storage/v1 se necessário
            link_corrigido = link_relativo if link_relativo.startswith("/storage/v1") else f"/storage/v1{link_relativo}"
            return f"{SUPABASE_URL}{link_corrigido}"
    except Exception as e:
        print(f"Erro na assinatura de mídia: {e}")
    return None

# ==========================================
# BLOCO 3: GESTÃO DE ACESSO (LOGIN/LOGOUT)
# ==========================================

@app.route("/", methods=["GET", "POST"])
def login():
    """Login com validação de furtividade e ambiente anônimo."""
    if request.method == "GET":
        session.clear() # Limpa rastros ao carregar o login
        
    # Ofuscação de campo: Gera ID aleatório para o input de senha
    id_campo = ''.join(random.choices(string.ascii_letters, k=6))

    if request.method == "POST":
        # Captura dinâmica do valor enviado através do prefixo pass_
        senha_digitada = next((val for key, val in request.form.items() if key.startswith('pass_')), None)
        
        if senha_digitada in [SENHA_ELE, SENHA_ELA]:
            session.permanent = True
            session["senha"] = senha_digitada
            return redirect(url_for("chat"))
        
        return render_template_string(HTML_LOGIN, erro="Senha incorreta.", id=id_campo)

    return render_template_string(HTML_LOGIN, id=id_campo)

@app.route("/sair")
def sair():
    """Logout total e destruição de sessão."""
    session.clear()
    return redirect(url_for("login"))

# ==========================================
# BLOCO 4: MÓDULO DE CHAT
# ==========================================

@app.route("/chat", methods=["GET", "POST"])
def chat():
    """Módulo de Chat com visualização segura e processamento de mídia."""
    senha = session.get('senha')
    if not senha: 
        return redirect(url_for('login')) # Proteção de rota
    
    # Identificação de perfil e cores
    if senha == SENHA_ELE: 
        meu_nome, cor_minha, cor_outra, parceiro = "Ele", "#005c4b", "#202c33", "Ela"
    else: 
        meu_nome, cor_minha, cor_outra, parceiro = "Ela", "#c2185b", "#202c33", "Ele"

    if request.method == "POST":
        msg = request.form.get("msg", "")
        file = request.files.get("arquivo")
        file_ref = None
        
        # Processamento e sanitização de arquivo
        if file and file.filename != "":
            nome_limpo = re.sub(r'[^a-zA-Z0-9._-]', '', file.filename.replace(" ", "_"))
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nome_limpo}"
            upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}"
            headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": file.content_type}
            
            res = requests.post(upload_url, headers=headers, data=file.read())
            if res.status_code == 200:
                file_ref = filename # Armazena apenas a referência

        if msg.strip() or file_ref:
            # Normalização de Cronologia (UTC-3)
            hora_atual = (datetime.utcnow() - timedelta(hours=3)).strftime('%d/%m %H:%M')
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO mensagens (autor, texto, data, arquivo_url) VALUES (%s, %s, %s, %s)", 
                        (meu_nome, msg, hora_atual, file_ref))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('chat'))

    # Recuperação e processamento de histórico
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT autor, texto, data, arquivo_url FROM mensagens ORDER BY id DESC LIMIT 50")
    msgs_raw = cur.fetchall()
    cur.close()
    conn.close()

    msgs_processadas = []
    for m in msgs_raw:
        autor, texto, data, ref_arquivo = m
        url_segura = obter_url_assinada(ref_arquivo) if ref_arquivo else None
        msgs_processadas.append((autor, texto, data, url_segura))
    
    # Inversão para ordem cronológica correta na interface
    msgs_processadas = msgs_processadas[::-1]

    return renderizar_interface(msgs_processadas, meu_nome, cor_minha, cor_outra, parceiro)

# ==========================================
# BLOCO 5: INTERFACE (TEMPLATES)
# ==========================================

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
        #bloqueio, #form-login { display: none; }
        .erro { color: #ef5350; background: rgba(239, 83, 80, 0.1); padding: 10px; border-radius: 8px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div id="loader">Validando segurança...</div>
        <div id="bloqueio">
            <h2>🛡️ Acesso Restrito</h2>
            <p>Use o <b>Modo Anônimo</b> para entrar.</p>
        </div>
        <div id="form-login">
            <h2>🔐 Cofre</h2>
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
                // Barreira de Quota: Libera apenas se ambiente for volátil/anônimo
                if (quotaMB < 1200) { document.getElementById('form-login').style.display = 'block'; }
                else { document.getElementById('bloqueio').style.display = 'block'; }
            }
        }
        setTimeout(verificarSeguranca, 600);
    </script>
</body>
</html>
"""

def renderizar_interface(msgs, meu_nome, cor_minha, cor_outra, parceiro):
    resp = make_response(render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                body { font-family: sans-serif; margin: 0; background-color: #0b141a; color: #e9edef; }
                .header { background: #202c33; padding: 10px; display: flex; align-items: center; position: sticky; top:0; z-index:100; justify-content: space-between; }
                .chat-container { display: flex; flex-direction: column; padding: 10px; margin-bottom: 80px; }
                .msg-row { display: flex; width: 100%; margin-bottom: 12px; }
                .msg-bubble { max-width: 85%; padding: 8px 12px; border-radius: 12px; }
                .mine { justify-content: flex-end; } .mine .msg-bubble { background: {{cor_minha}}; }
                .other { justify-content: flex-start; } .other .msg-bubble { background: {{cor_outra}}; }
                .footer { position: fixed; bottom: 0; width: 100%; background: #202c33; padding: 10px; display: flex; box-sizing: border-box; }
                .media-bar { background: #111b21; padding: 10px; overflow-x: auto; display: flex; gap: 8px; }
                .img-thumb { width: 60px; height: 60px; object-fit: cover; border-radius: 8px; }
            </style>
        </head>
        <body oncontextmenu="return false;">
            <div class="header">
                <span><b>{{parceiro}}</b> (online)</span>
                <a href="/sair" style="color:#8696a0;"><i class="fa-solid fa-right-from-bracket"></i></a>
            </div>
            <div class="media-bar">
                {% for m in msgs if m[3] %}<img src="{{m[3]}}" class="img-thumb">{% endfor %}
            </div>
            <div class="chat-container">
                {% for m in msgs %}
                <div class="msg-row {% if m[0] == meu_nome %}mine{% else %}other{% endif %}">
                    <div class="msg-bubble">
                        {% if m[1] %}<div>{{m[1]}}</div>{% endif %}
                        {% if m[3] %}<div style="color:#00a884; margin-top:5px;"><i class="fa-solid fa-camera"></i> Foto</div>{% endif %}
                        <small style="opacity:0.5;">{{ m[2] }}</small>
                    </div>
                </div>
                {% endfor %}
            </div>
            <form method="POST" enctype="multipart/form-data" class="footer">
                <input type="file" name="arquivo" id="arquivo" style="display:none">
                <label for="arquivo" style="color:#8696a0; font-size:24px; margin-right:10px;"><i class="fa-solid fa-paperclip"></i></label>
                <input type="text" name="msg" style="flex:1; border-radius:20px; border:none; padding:10px;" placeholder="Mensagem">
                <button type="submit" style="background:none; border:none; color:#00a884; font-size:24px;"><i class="fa-solid fa-paper-plane"></i></button>
            </form>
            <script>
                window.scrollTo(0, document.body.scrollHeight);
                // Auto-Refresh Inteligente (10s)
                setInterval(() => {
                    if (document.activeElement.tagName !== 'INPUT') { window.location.reload(); }
                }, 10000);
            </script>
        </body>
        </html>
    """, msgs=msgs, meu_nome=meu_nome, cor_minha=cor_minha, cor_outra=cor_outra, parceiro=parceiro))
    
    # Proteção contra Cache/Botão Voltar
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp

if __name__ == "__main__":
    app.run(debug=False)

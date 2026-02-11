import os
import psycopg2
import requests
import random
import string
import re
from flask import Flask, request, render_template_string, session, redirect, url_for, make_response
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ==========================================
# CONFIGURAÇÕES E VARIÁVEIS DE AMBIENTE
# ==========================================
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cafe_com_seguranca_2026") 
app.permanent_session_lifetime = timedelta(hours=2) # TTL de 2 horas

SENHA_ELE = os.getenv("SENHA_ELE")
SENHA_ELA = os.getenv("SENHA_ELA")
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

def get_db_connection():
    """Estabelece conexão única com o PostgreSQL."""
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)

# ==========================================
# GESTÃO DE ACESSO (LOGIN/LOGOUT)
# ==========================================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session.clear() # Limpeza de rastros ao carregar
        
    # Gera ID dinâmico para ofuscar o campo de senha contra gerenciadores
    id_campo = ''.join(random.choices(string.ascii_letters, k=6))

    if request.method == "POST":
        # Captura o valor independente do sufixo dinâmico
        senha_digitada = next((val for key, val in request.form.items() if key.startswith('pass_')), None)
        
        if senha_digitada in [SENHA_ELE, SENHA_ELA]:
            session.permanent = True
            session["senha"] = senha_digitada
            return redirect(url_for("chat"))
        
        return render_template_string(HTML_LOGIN, erro="Senha incorreta.", id=id_campo)

    return render_template_string(HTML_LOGIN, id=id_campo)

@app.route("/sair")
def sair():
    session.clear() # Destruição total da sessão
    return redirect(url_for("login"))

# ==========================================
# NÚCLEO DO CHAT E STORAGE
# ==========================================

def obter_url_assinada(path_ref):
    """Gera URL temporária (1h) para mídias via Supabase."""
    if not path_ref: return None
    
    # Endpoint de assinatura corrigido /storage/v1
    url_request = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{path_ref}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    
    try:
        res = requests.post(url_request, headers=headers, json={"expiresIn": 3600}, timeout=10)
        if res.status_code == 200:
            link = res.json().get("signedURL", "")
            return f"{SUPABASE_URL}{link}" if link.startswith("/storage") else f"{SUPABASE_URL}/storage/v1{link}"
    except Exception as e:
        print(f"Erro Storage: {e}")
    return None

@app.route("/chat", methods=["GET", "POST"])
def chat():
    senha = session.get('senha')
    if not senha: return redirect(url_for('login')) # Proteção server-side
    
    # Define perfil e interface visual baseada na senha
    if senha == SENHA_ELE: meu_nome, cor_minha, cor_outra, parceiro = "Ele", "#005c4b", "#202c33", "Ela"
    else: meu_nome, cor_minha, cor_outra, parceiro = "Ela", "#c2185b", "#202c33", "Ele"

    if request.method == "POST":
        msg = request.form.get("msg", "")
        file = request.files.get("arquivo")
        file_ref = None
        
        if file and file.filename != "":
            # Sanitização de nome: remove caracteres especiais e espaços
            nome_limpo = re.sub(r'[^a-zA-Z0-9._-]', '', file.filename.replace(" ", "_"))
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nome_limpo}"
            
            upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}"
            headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": file.content_type}
            
            if requests.post(upload_url, headers=headers, data=file.read()).status_code == 200:
                file_ref = filename

        if msg.strip() or file_ref:
            # Normalização de Cronologia (UTC-3 Brasília)
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
        url_segura = obter_url_assinada(m[3]) if m[3] else None
        msgs_processadas.append((m[0], m[1], m[2], url_segura))
    
    return renderizar_interface(msgs_processadas[::-1], meu_nome, cor_minha, cor_outra, parceiro)

# ==========================================
# INTERFACE E TEMPLATES (MOBILE-FIRST)
# ==========================================

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Cofre Privado</title>
    <style>
        body { background: #0b141a; color: white; font-family: sans-serif; margin: 0; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .container { width: 90%; max-width: 400px; text-align: center; }
        input[type="password"] { width: 100%; padding: 22px; font-size: 20px; border-radius: 15px; border: 2px solid #2a3942; background: #2a3942; color: white; box-sizing: border-box; margin-bottom: 15px; text-align: center; }
        button { width: 100%; padding: 22px; font-size: 18px; font-weight: bold; border-radius: 15px; border: none; background: #00a884; color: white; }
        #bloqueio, #form-login { display: none; }
        .erro { color: #ef5350; margin-bottom: 15px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div id="loader">Validando ambiente...</div>
        <div id="bloqueio">
            <h2>🛡️ Acesso Restrito</h2>
            <p>Ative o <b>Modo Anônimo</b> para acessar este cofre.</p>
        </div>
        <div id="form-login">
            <h2 style="font-weight: 300;">🔐 Cofre Privado</h2>
            {% if erro %}<div class="erro">{{ erro }}</div>{% endif %}
            <form method="POST" autocomplete="off">
                <input type="password" name="pass_{{ id }}" placeholder="Senha" autofocus autocomplete="new-password">
                <button type="submit">ENTRAR</button>
            </form>
        </div>
    </div>
    <script>
        async function check() {
            if ('storage' in navigator && 'estimate' in navigator.storage) {
                const {quota} = await navigator.storage.estimate();
                const isAnon = (quota / (1024 * 1024)) < 1200; // Detecção por cota de disco
                document.getElementById('loader').style.display = 'none';
                document.getElementById(isAnon ? 'form-login' : 'bloqueio').style.display = 'block';
            }
        }
        setTimeout(check, 500);
    </script>
</body>
</html>
"""

def renderizar_interface(msgs, meu_nome, cor_minha, cor_outra, parceiro):
    # Template do Chat omitido aqui para brevidade, mas integrado no app.py funcional
    # [A lógica de Renderizar Interface permanece a mesma do seu arquivo original]
    # Certifique-se de manter os Headers de Cache Control no retorno
    pass 

if __name__ == "__main__":
    app.run(debug=False)

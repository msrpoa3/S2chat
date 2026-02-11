# ==========================================
# BLOCO 1: IMPORTAÇÕES E CONFIGURAÇÕES
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

# Carrega variáveis de ambiente
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
# BLOCO 2: UTILITÁRIOS (LIMPO E SEM DUPLICATAS)
# ==========================================
def get_db_connection():
    """Estabelece conexão com PostgreSQL"""
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)

def obter_url_assinada(path_ou_url):
    """Gera URL temporária (1h) via Supabase API"""
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
            # Garante que o prefixo storage/v1 esteja presente sem duplicar barras
            if link_relativo and not link_relativo.startswith("/storage/v1"):
                link_relativo = f"/storage/v1{link_relativo}"
            return f"{SUPABASE_URL}{link_relativo}"
    except Exception as e:
        print(f"Erro na assinatura: {e}")
    return None

# ==========================================
# BLOCO 3: GESTÃO DE ACESSO
# ==========================================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session.clear() # Limpeza de rastro inicial
        
    # ID dinâmico para ofuscação de campo
    id_campo = ''.join(random.choices(string.ascii_letters, k=6))

    if request.method == "POST":
        # Captura o valor independente do ID dinâmico
        senha_digitada = next((val for key, val in request.form.items() if key.startswith('pass_')), None)
        
        if senha_digitada in [SENHA_ELE, SENHA_ELA]:
            session.permanent = True
            session["senha"] = senha_digitada
            return redirect(url_for("chat"))
        
        return render_template_string(HTML_LOGIN, erro="Senha incorreta.", id=id_campo)

    return render_template_string(HTML_LOGIN, id=id_campo)

@app.route("/sair")
def sair():
    session.clear() # Encerramento de estado
    return redirect(url_for("login"))

# ==========================================
# BLOCO 4: NÚCLEO DO CHAT
# ==========================================
@app.route("/chat", methods=["GET", "POST"])
def chat():
    senha = session.get('senha')
    if not senha: 
        return redirect(url_for('login')) # Restrição server-side
    
    # Define perfil e cores baseadas na senha
    if senha == SENHA_ELE: 
        meu_nome, cor_minha, cor_outra, parceiro = "Ele", "#005c4b", "#202c33", "Ela"
    else: 
        meu_nome, cor_minha, cor_outra, parceiro = "Ela", "#c2185b", "#202c33", "Ele"

    if request.method == "POST":
        msg = request.form.get("msg", "")
        file = request.files.get("arquivo")
        file_ref = None
        
        # Upload e Sanitização
        if file and file.filename != "":
            nome_limpo = re.sub(r'[^a-zA-Z0-9._-]', '', file.filename.replace(" ", "_"))
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nome_limpo}"
            upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}"
            headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": file.content_type}
            res = requests.post(upload_url, headers=headers, data=file.read())
            if res.status_code == 200:
                file_ref = filename

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

    # Recuperação e Inversão de Histórico
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
    
    return renderizar_interface(msgs_processadas[::-1], meu_nome, cor_minha, cor_outra, parceiro)

# ==========================================
# BLOCO 5: TEMPLATES E INTERFACE
# ==========================================
HTML_LOGIN = """
"""

def renderizar_interface(msgs, meu_nome, cor_minha, cor_outra, parceiro):
    # Lógica de interface com Cache-Control: no-store
    resp = make_response(render_template_string(HTML_CHAT, msgs=msgs, meu_nome=meu_nome, ...))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp

HTML_CHAT = """
"""

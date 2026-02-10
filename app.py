# ==========================================
# BLOCO 1: IMPORTAÇÕES E CONFIGURAÇÕES INICIAIS
# ==========================================
import os
import psycopg2
import requests
import random
import string
import re  # Novo: Para tratar links legados
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
    # Limpa a sessão ao carregar a página de login para garantir que está "limpo"
    if request.method == "GET":
        session.clear()
        
    id_campo = ''.join(random.choices(string.ascii_letters, k=6))

    if request.method == "POST":
        # Pega a senha independente do ID dinâmico do campo
        senha_digitada = next((val for key, val in request.form.items() if key.startswith('pass_')), None)
        
        if senha_digitada in [SENHA_ELE, SENHA_ELA]:
            session.permanent = True
            session["senha"] = senha_digitada
            return redirect(url_for("chat"))
        
        return render_template_string(HTML_LOGIN, erro="Senha incorreta. Tente novamente.", id=id_campo)

    return render_template_string(HTML_LOGIN, id=id_campo)

@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))

# Template de Login Mobile com Trava de Anonimato
HTML_LOGIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Cofre Privado</title>
    <style>
        body { 
            background: #0b141a; color: white; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            margin: 0; display: flex; align-items: center; justify-content: center; 
            height: 100vh; overflow: hidden; 
        }
        .container { width: 90%; max-width: 400px; text-align: center; }
        .logo { font-size: 60px; margin-bottom: 20px; }
        
        input[type="password"] { 
            width: 100%; padding: 22px; font-size: 20px; border-radius: 15px; border: 2px solid #2a3942; 
            background: #2a3942; color: white; box-sizing: border-box; text-align: center; 
            margin-bottom: 15px; outline: none; appearance: none;
        }
        input[type="password"]:focus { border-color: #00a884; }
        
        button { 
            width: 100%; padding: 22px; font-size: 18px; font-weight: bold; border-radius: 15px; border: none; 
            background: #00a884; color: white; cursor: pointer; transition: 0.2s;
        }
        button:active { transform: scale(0.96); opacity: 0.9; }
        
        #bloqueio { display: none; background: #111b21; padding: 40px 20px; border-radius: 25px; border: 1px solid #ef5350; }
        #bloqueio h2 { color: #ef5350; font-size: 24px; margin-top: 0; }
        #bloqueio p { color: #8696a0; line-height: 1.6; font-size: 16px; }
        
        #form-login { display: none; }
        .erro { color: #ef5350; background: rgba(239, 83, 80, 0.1); padding: 10px; border-radius: 8px; margin-bottom: 15px; font-size: 14px; }
        .loading { font-size: 16px; color: #8696a0; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <div id="loader" class="loading">Iniciando protocolo de segurança...</div>

        <div id="bloqueio">
            <div class="logo">🛡️</div>
            <h2>Acesso Restrito</h2>
            <p>Este cofre contém informações sensíveis e não deixa rastros.</p>
            <p>Para entrar, você <b>deve</b> usar o <b>Modo Anônimo</b> do seu navegador.</p>
            <div style="margin-top: 30px; font-size: 12px; color: #667781; border-top: 1px solid #222; padding-top: 20px;">
                Abra as configurações do navegador e selecione "Nova guia anônima".
            </div>
        </div>

        <div id="form-login">
            <div class="logo">🔐</div>
            <h2 style="margin-bottom: 30px; font-weight: 300;">Cofre Privado</h2>
            {% if erro %}<div class="erro">{{ erro }}</div>{% endif %}
            <form method="POST" autocomplete="off">
                <input type="password" name="pass_{{ id }}" placeholder="Digite a senha" autofocus autocomplete="new-password">
                <button type="submit">ENTRAR</button>
            </form>
        </div>
    </div>

    <script>
        async function verificarSeguranca() {
            const loader = document.getElementById('loader');
            const bloqueio = document.getElementById('bloqueio');
            const form = document.getElementById('form-login');

            if ('storage' in navigator && 'estimate' in navigator.storage) {
                try {
                    const {quota} = await navigator.storage.estimate();
                    const quotaMB = Math.round(quota / (1024 * 1024));
                    
                    loader.style.display = 'none';

                    // Se a quota for baixa (< 1200MB no mobile), libera o acesso
                    if (quotaMB < 1200) {
                        form.style.display = 'block';
                    } else {
                        bloqueio.style.display = 'block';
                    }
                } catch (e) {
                    loader.innerText = "Erro ao validar segurança.";
                }
            } else {
                loader.innerText = "Navegador não suportado.";
            }
        }
        
        // Pequeno delay para estabilidade da API
        setTimeout(verificarSeguranca, 600);
    </script>
</body>
</html>
"""


# ==========================================
# BLOCO 4: NÚCLEO DO CHAT (LÓGICA E STORAGE)
# ==========================================

def obter_url_assinada(path_ou_url):
    """Gera URL temporária e garante o domínio completo e seguro do Supabase."""
    if not path_ou_url:
        return None
    
    # 1. Limpeza total de strings (remove espaços e barras extras)
    base_url = SUPABASE_URL.strip().rstrip('/')
    key = SUPABASE_KEY.strip()
    bucket = BUCKET_NAME.strip()
    
    # 2. Extrai o nome do arquivo (trata links antigos ou nomes puros)
    nome_arquivo = path_ou_url.split('/')[-1].strip()
    
    # 3. Endpoint para assinatura
    url_request = f"{base_url}/storage/v1/object/sign/{bucket}/{nome_arquivo}"
    
    headers = {
        "Authorization": f"Bearer {key}", 
        "Content-Type": "application/json"
    }
    
    try:
        # Tenta obter o link assinado por 1 hora
        res = requests.post(url_request, headers=headers, json={"expiresIn": 3600}, timeout=10)
        
        if res.status_code == 200:
            url_relativa = res.json().get("signedURL")
            if url_relativa:
                # GARANTIA DE DOMÍNIO: Se o Supabase devolver só o caminho, forçamos o domínio HTTPS
                if url_relativa.startswith('/'):
                    return f"{base_url}{url_relativa}"
                return url_relativa
        else:
            # Log de erro para o painel do Render (ajuda no diagnóstico)
            print(f"⚠️ Erro Supabase {res.status_code}: {res.text} | Arq: {nome_arquivo}")
    except Exception as e:
        print(f"❌ Erro crítico na assinatura: {e}")
        
    return None

@app.route("/chat", methods=["GET", "POST"])
def chat():
    senha = session.get('senha')
    if not senha: 
        return redirect(url_for('login'))
    
    # Define perfil e cores baseadas na sessão
    if senha == SENHA_ELE:
        meu_nome, cor_minha, cor_outra, parceiro = "Ele", "#005c4b", "#202c33", "Ela"
    else:
        meu_nome, cor_minha, cor_outra, parceiro = "Ela", "#c2185b", "#202c33", "Ele"

    if request.method == "POST":
        msg = request.form.get("msg", "")
        file = request.files.get("arquivo")
        file_ref = None
        
        if file and file.filename != "":
            # Higieniza o nome do arquivo para evitar quebras na URL
            safe_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename.replace(' ', '_')}"
            upload_url = f"{SUPABASE_URL.strip().rstrip('/')}/storage/v1/object/{BUCKET_NAME.strip()}/{safe_filename}"
            
            headers = {
                "Authorization": f"Bearer {SUPABASE_KEY.strip()}", 
                "Content-Type": file.content_type
            }
            
            res = requests.post(upload_url, headers=headers, data=file.read())
            if res.status_code == 200:
                file_ref = safe_filename

        if msg.strip() or file_ref:
            # Brasília UTC-3
            hora_atual = (datetime.utcnow() - timedelta(hours=3)).strftime('%d/%m %H:%M')
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO mensagens (autor, texto, data, arquivo_url) VALUES (%s, %s, %s, %s)", 
                (meu_nome, msg, hora_atual, file_ref)
            )
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('chat'))

    # Histórico de 50 mensagens
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT autor, texto, data, arquivo_url FROM mensagens ORDER BY id DESC LIMIT 50")
    msgs_raw = cur.fetchall()
    cur.close()
    conn.close()

    # Processamento de URLs (Transforma ref em link assinado)
    msgs_processadas = []
    for m in msgs_raw:
        autor, texto, data, ref_arquivo = m
        url_segura = obter_url_assinada(ref_arquivo) if ref_arquivo else None
        msgs_processadas.append((autor, texto, data, url_segura))

    return renderizar_interface(msgs_processadas, meu_nome, cor_minha, cor_outra, parceiro)

# ==========================================
# BLOCO 5: INTERFACE (HTML/JS) E RENDERIZAÇÃO
# ==========================================

def renderizar_interface(msgs, meu_nome, cor_minha, cor_outra, parceiro):
    # O HTML permanece o mesmo que você já usa, mas encapsulado para retorno limpo
    html = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Cofre Privado</title>
        <style>
            body { font-family: sans-serif; background-color: #0b141a; color: #e9edef; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
            .header { background-color: #202c33; padding: 15px; text-align: center; font-weight: bold; font-size: 1.2em; border-bottom: 1px solid #3b4a54; }
            .chat-container { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column-reverse; background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); background-attachment: fixed; }
            .msg { max-width: 80%; margin-bottom: 12px; padding: 8px 12px; border-radius: 12px; position: relative; font-size: 0.95em; line-height: 1.4; word-wrap: break-word; }
            .minha { align-self: flex-end; border-bottom-right-radius: 2px; }
            .outra { align-self: flex-start; border-bottom-left-radius: 2px; }
            .data { font-size: 0.7em; opacity: 0.6; margin-top: 4px; display: block; text-align: right; }
            .img-chat { width: 100%; max-width: 250px; border-radius: 8px; margin-top: 5px; cursor: pointer; display: block; }
            
            .input-area { background-color: #202c33; padding: 10px; display: flex; align-items: center; gap: 8px; }
            .msg-input { flex: 1; background-color: #2a3942; border: none; color: white; padding: 12px; border-radius: 20px; outline: none; font-size: 16px; }
            .btn-send { background: none; border: none; color: #00a884; font-size: 24px; cursor: pointer; display: flex; align-items: center; }
            
            .clip-btn { color: #8696a0; font-size: 22px; cursor: pointer; padding: 5px; }
            .clip-active { color: #00a884 !important; }

            /* Lightbox Overlay */
            #overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); display: none; justify-content: center; align-items: center; z-index: 1000; }
            #imgFull { max-width: 95%; max-height: 95%; border-radius: 5px; }
        </style>
    </head>
    <body oncontextmenu="return false;">
        <div class="header">Chat Privado</div>
        
        <div class="chat-container">
            {% for m in msgs %}
                <div class="msg {{ 'minha' if m[0] == meu_nome else 'outra' }}" 
                     style="background-color: {{ cor_minha if m[0] == meu_nome else cor_outra }}">
                    
                    {% if m[3] %}
                        <img src="{{ m[3] }}" class="img-chat" onclick="openImg('{{ m[3] }}')">
                    {% endif %}
                    
                    {% if m[1] %}<div style="margin-top: 5px;">{{ m[1] }}</div>{% endif %}
                    <span class="data">{{ m[2] }}</span>
                </div>
            {% endfor %}
        </div>

        <form method="POST" enctype="multipart/form-data" class="input-area" id="chatForm">
            <label for="arquivo" class="clip-btn" id="clipLabel">📎</label>
            <input type="file" name="arquivo" id="arquivo" hidden onchange="fileSelected()">
            
            <input type="text" name="msg" class="msg-input" placeholder="Mensagem" id="msgInput" autocomplete="off">
            
            <button type="submit" class="btn-send">➤</button>
            <button type="button" id="cancelFile" style="display:none; background:none; border:none; color:#f44336; font-size:20px;" onclick="clearFile()">✕</button>
        </form>

        <div id="overlay" onclick="closeImg()">
            <img id="imgFull" src="">
        </div>

        <script>
            let isOverlayOpen = false;
            let isWindowFocused = true;
            window.onfocus = () => { isWindowFocused = true; };
            window.onblur = () => { isWindowFocused = false; };

            function fileSelected() {
                const file = document.getElementById('arquivo');
                if (file.files.length > 0) {
                    document.getElementById('clipLabel').classList.add('clip-active');
                    document.getElementById('cancelFile').style.display = "block";
                    document.getElementById('msgInput').placeholder = "Imagem selecionada...";
                }
            }

            function clearFile() {
                document.getElementById('arquivo').value = "";
                document.getElementById('clipLabel').classList.remove('clip-active');
                document.getElementById('cancelFile').style.display = "none";
                document.getElementById('msgInput').placeholder = "Mensagem";
            }

            function openImg(src) { 
                document.getElementById('imgFull').src = src; 
                document.getElementById('overlay').style.display = 'flex'; 
                isOverlayOpen = true; 
            }
            function closeImg() { 
                document.getElementById('overlay').style.display = 'none'; 
                isOverlayOpen = false; 
            }

            setInterval(() => {
                const hasFile = document.getElementById('arquivo').files.length > 0;
                const hasText = document.getElementById('msgInput').value !== "";
                if (!isOverlayOpen && !hasText && !hasFile && isWindowFocused) {
                    window.location.reload();
                }
            }, 10000);
        </script>
    </body>
    </html>
    """
    resp = make_response(render_template_string(html, msgs=msgs, meu_nome=meu_nome, cor_minha=cor_minha, cor_outra=cor_outra, parceiro=parceiro))
    
    # HEADERS DE SEGURANÇA E CACHE (Cruciais para Navegação Anônima e Mobile)
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    resp.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    # Permite que o navegador carregue imagens do domínio do Supabase
    resp.headers["Content-Security-Policy"] = f"img-src 'self' {SUPABASE_URL.strip()} data: blob:;"
    
    return resp

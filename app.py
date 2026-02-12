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
    session.clear()
    id_aleatorio = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    if request.method == "POST":
        senha_input = request.form.get("senha")
        if senha_input in [SENHA_ELE, SENHA_ELA]:
            session['senha'] = senha_input
            session.permanent = True
            return redirect(url_for('chat'))
        return redirect(url_for('login'))

    return render_template_string("""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
            <title>Cofre Privado</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                body { font-family: 'Segoe UI', sans-serif; background-color: #0b141a; color: #e9edef; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .login-card { background: #202c33; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 100%; max-width: 320px; text-align: center; }
                .icon-lock { font-size: 50px; color: #00a884; margin-bottom: 20px; }
                h2 { margin-bottom: 30px; font-weight: 300; }
                /* Ofuscação do campo de senha */
                .input-field { width: 100%; padding: 15px; margin-bottom: 20px; border: none; border-radius: 10px; background: #2a3942; color: white; font-size: 18px; box-sizing: border-box; text-align: center; }
                .btn-login { width: 100%; padding: 15px; border: none; border-radius: 10px; background: #00a884; color: white; font-size: 18px; font-weight: bold; cursor: pointer; }
                #warning { color: #ef5350; font-size: 14px; display: none; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="login-card" id="loginCard" style="display:none;">
                <i class="fa-solid fa-shield-halved icon-lock"></i>
                <h2>Cofre Privado</h2>
                <form method="POST" id="loginForm" autocomplete="off">
                    <input type="password" name="senha" id="pass_{{id_aleatorio}}" 
                           class="input-field" placeholder="Chave de Acesso" 
                           required autocomplete="new-password">
                    <button type="submit" class="btn-login">ACESSAR</button>
                </form>
            </div>
            
            <div id="restriction" style="display:none; text-align:center; padding: 20px;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size:50px; color:#ff9800;"></i>
                <h2 style="color:#ff9800;">Acesso Restrito</h2>
                <p>Para sua segurança, utilize o <b>Modo Anônimo</b>.</p>
            </div>

            <script>
                // VALIDAÇÃO DE AMBIENTE (CHECKLIST: BARREIRA DE NAVEGAÇÃO)
                async function checkStorage() {
                    if (navigator.storage && navigator.storage.estimate) {
                        const {quota} = await navigator.storage.estimate();
                        const quotaMB = quota / (1024 * 1024);
                        
                        // Se quota > 1200MB, detecta Navegação Normal e bloqueia
                        if (quotaMB > 1200) {
                            document.getElementById('restriction').style.display = 'block';
                        } else {
                            document.getElementById('loginCard').style.display = 'block';
                        }
                    } else {
                        // Fallback para navegadores sem API de estimativa
                        document.getElementById('loginCard').style.display = 'block';
                    }
                }

                // IMPLEMENTAÇÃO C: LIMPEZA INSTANTÂNEA (ANTI-BACK)
                document.getElementById('loginForm').onsubmit = function() {
                    const passField = document.getElementById('pass_{{id_aleatorio}}');
                    setTimeout(() => {
                        passField.value = ''; // Limpa o rastro visual no milissegundo do envio
                    }, 10);
                };

                checkStorage();
            </script>
        </body>
        </html>
    """, id_aleatorio=id_aleatorio)

@app.route("/sair")
def sair():
    session.clear()
    # Redirecionamento Furtivo (Mapa de Funções)
    return redirect("https://www.google.com")


# ==========================================
# BLOCO 4: NÚCLEO DO CHAT (LÓGICA E STORAGE)
# ==========================================

# ... (Manter função obter_url_assinada e a rota chat() igual à anterior) ...

def renderizar_interface(msgs_processadas, meu_nome, cor_minha, cor_outra, parceiro):
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
                .msg-row { display: flex; width: 100%; margin-bottom: 12px; }
                .msg-bubble { max-width: 85%; padding: 8px 12px; border-radius: 12px; font-size: 15px; position: relative; }
                .mine { justify-content: flex-end; }
                .mine .msg-bubble { background: {{cor_minha}}; border-top-right-radius: 0; }
                .other { justify-content: flex-start; }
                .other .msg-bubble { background: {{cor_outra}}; border-top-left-radius: 0; }
                
                /* MODO PRIVACIDADE ATIVÁVEL */
                body.blur-active .msg-text, body.blur-active .img-thumb, body.blur-active .photo-label { 
                    filter: blur(10px); 
                }
                body.blur-active .msg-bubble:active .msg-text, 
                body.blur-active .msg-bubble:active .photo-label, 
                body.blur-active .img-thumb:active { 
                    filter: blur(0); 
                }

                .time { font-size: 0.65em; color: rgba(255,255,255,0.4); text-align: right; margin-top: 5px; display: block; }
                .footer { position: fixed; bottom: 0; width: 100%; background: #202c33; padding: 10px; display: flex; align-items: center; box-sizing: border-box; }
                .input-msg { flex: 1; background: #2a3942; border: none; padding: 12px; border-radius: 25px; color: white; outline: none; margin: 0 10px; font-size: 16px; }
                .icon-btn { color: #8696a0; font-size: 20px; cursor: pointer; background: none; border: none; }
                .media-bar { background: #111b21; padding: 10px; overflow-x: auto; display: flex; gap: 8px; border-bottom: 1px solid #222; }
                .img-thumb { width: 60px; height: 60px; object-fit: cover; border-radius: 8px; flex-shrink: 0; transition: filter 0.2s; }
                #overlay { position: fixed; display: none; width: 100%; height: 100%; top: 0; left: 0; background: rgba(0,0,0,0.95); z-index: 2000; justify-content: center; align-items: center; }
                #overlay img { max-width: 100%; max-height: 100%; }
                canvas.msg-canvas { max-width: 100%; display: block; }
            </style>
        </head>
        <body oncontextmenu="return false;">
            <div class="header">
                <div style="display:flex; align-items:center;">
                    <div style="width:35px; height:35px; background:{{cor_minha}}; border-radius:50%; margin-right:10px; display:flex; align-items:center; justify-content:center; font-weight:bold;">{{parceiro[0]}}</div>
                    <div><span style="font-weight:bold;">{{parceiro}}</span><br><small style="color:#00a884;">online</small></div>
                </div>
                <div style="display:flex; gap: 20px; align-items:center;">
                    <div onclick="togglePrivacy()" class="icon-btn" id="privacyBtn">
                        <i class="fa-solid fa-eye"></i>
                    </div>
                    <a href="/sair" class="icon-btn"><i class="fa-solid fa-right-from-bracket"></i></a>
                </div>
            </div>

            <div class="media-bar">
                {% for m in msgs if m[3] %}<img src="{{m[3]}}" class="img-thumb" onclick="openImg('{{m[3]}}')">{% endfor %}
            </div>

            <div class="chat-container" id="chat">
                {% for m in msgs %}
                <div class="msg-row {% if m[0] == meu_nome %}mine{% else %}other{% endif %}">
                    <div class="msg-bubble">
                        {% if m[1] %}
                            <div class="msg-text" data-raw="{{m[1]}}">
                                <canvas class="msg-canvas"></canvas>
                            </div>
                        {% endif %}
                        {% if m[3] %}
                            <div class="photo-label" style="margin-top:5px; color:#00a884; font-weight:bold; cursor:pointer;" onclick="openImg('{{m[3]}}')">
                                <i class="fa-solid fa-camera"></i> Foto
                            </div>
                        {% endif %}
                        <span class="time">{{ m[2] }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>

            <div id="overlay" onclick="closeImg()"><img id="imgFull"></div>

            <form method="POST" enctype="multipart/form-data" class="footer" id="mainForm" autocomplete="off">
                <label for="arquivo" class="icon-btn"><i class="fa-solid fa-paperclip"></i></label>
                <input type="file" id="arquivo" name="arquivo" style="display:none" onchange="fileSelected()">
                <input type="text" name="msg" id="msgInput" class="input-msg" placeholder="Mensagem" autocomplete="off">
                <button type="submit" class="icon-btn"><i class="fa-solid fa-paper-plane" style="color:#00a884;"></i></button>
            </form>

            <script>
                // CANVAS COM WORD WRAP (FONT SIZE FIXO)
                function wrapText(ctx, text, maxWidth) {
                    const words = text.split(' ');
                    let line = '';
                    const lines = [];
                    for (let n = 0; n < words.length; n++) {
                        let testLine = line + words[n] + ' ';
                        let metrics = ctx.measureText(testLine);
                        if (metrics.width > maxWidth && n > 0) {
                            lines.push(line);
                            line = words[n] + ' ';
                        } else { line = testLine; }
                    }
                    lines.push(line);
                    return lines;
                }

                function drawCanvasText() {
                    const containers = document.querySelectorAll('.msg-text');
                    const maxWidth = window.innerWidth * 0.7; // Limite lateral da bolha
                    
                    containers.forEach(div => {
                        const text = div.getAttribute('data-raw');
                        const canvas = div.querySelector('canvas');
                        const ctx = canvas.getContext('2d');
                        const fontSize = 16;
                        ctx.font = fontSize + "px 'Segoe UI', sans-serif";
                        
                        const lines = wrapText(ctx, text, maxWidth);
                        const canvasWidth = Math.min(maxWidth, ctx.measureText(text).width + 10);
                        
                        canvas.width = canvasWidth;
                        canvas.height = lines.length * (fontSize + 6);
                        
                        ctx.fillStyle = "white";
                        ctx.font = fontSize + "px 'Segoe UI', sans-serif";
                        ctx.textBaseline = "top";
                        
                        lines.forEach((line, i) => {
                            ctx.fillText(line.trim(), 0, i * (fontSize + 6));
                        });
                    });
                }

                // TOGGLE PRIVACIDADE
                function togglePrivacy() {
                    document.body.classList.toggle('blur-active');
                    const btn = document.getElementById('privacyBtn');
                    if(document.body.classList.contains('blur-active')) {
                        btn.innerHTML = '<i class="fa-solid fa-eye-slash" style="color:#ef5350;"></i>';
                    } else {
                        btn.innerHTML = '<i class="fa-solid fa-eye"></i>';
                    }
                }

                // LIMPEZA INSTANTÂNEA AO ENVIAR
                document.getElementById('mainForm').onsubmit = function() {
                    const input = document.getElementById('msgInput');
                    setTimeout(() => { input.value = ''; }, 10);
                };

                window.onload = () => {
                    drawCanvasText();
                    window.scrollTo(0, document.body.scrollHeight);
                };

                function openImg(src) { document.getElementById('imgFull').src = src; document.getElementById('overlay').style.display = 'flex'; }
                function closeImg() { document.getElementById('overlay').style.display = 'none'; }
                
                // ... (Manter resto dos scripts de foco e refresh do arquivo anterior) ...
            </script>
        </body>
        </html>
    """, msgs=msgs_processadas, meu_nome=meu_nome, cor_minha=cor_minha, cor_outra=cor_outra, parceiro=parceiro))
    
    # Headers de Cache (Checklist)
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp

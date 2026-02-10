# app.py (Versão de Teste com Blindagem V5.0)
import os
import psycopg2
import random
import string
from flask import Flask, request, render_template_string, session, redirect, url_for, make_response
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "teste_blindagem_2026")

# Configurações para o Render/Supabase
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session.clear()
        
    id_campo = ''.join(random.choices(string.ascii_letters, k=6))

    if request.method == "POST":
        # Captura a senha independente do ID dinâmico
        senha_digitada = next((val for key, val in request.form.items() if key.startswith('pass_')), None)
        
        # Simulação de senhas para o teste
        if senha_digitada in ["123", "456"]:
            session["senha"] = senha_digitada
            return redirect(url_for("chat"))
        
        return render_template_string(HTML_LOGIN, erro="Senha incorreta.", id=id_campo)

    return render_template_string(HTML_LOGIN, id=id_campo)

@app.route("/chat")
def chat():
    if "senha" not in session:
        return redirect(url_for("login"))
    
    # Mensagens de exemplo para validar Canvas e Blur
    msgs = [
        {"id": 1, "autor": "Ele", "texto": "Esta mensagem é um desenho no Canvas.", "hora": "12:00"},
        {"id": 2, "autor": "Ela", "texto": "Toque e segure para desborrar.", "hora": "12:05"}
    ]
    return render_template_string(HTML_CHAT, msgs=msgs)

# ==========================================
# TEMPLATES COM AS TÉCNICAS DE SEGURANÇA
# ==========================================

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #0b141a; color: white; font-family: sans-serif; text-align: center; padding-top: 50px; }
        input { padding: 15px; border-radius: 10px; border: none; width: 80%; margin-bottom: 10px; }
        button { padding: 15px; width: 85%; background: #00a884; border: none; color: white; font-weight: bold; border-radius: 10px; }
    </style>
</head>
<body>
    <h2>Cofre Privado</h2>
    {% if erro %}<p style="color: red;">{{ erro }}</p>{% endif %}
    
    <form id="loginForm" method="POST" onsubmit="limparInput('pass_field')">
        <input type="password" id="pass_field" name="pass_{{ id }}" placeholder="Senha" autocomplete="new-password">
        <button type="submit">ENTRAR</button>
    </form>

    <script>
        function limparInput(id) {
            const el = document.getElementById(id);
            setTimeout(() => { el.value = ""; el.blur(); }, 10); // Limpa milissegundos após o envio
        }
    </script>
</body>
</html>
"""

HTML_CHAT = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <style>
        body { background: #0b141a; color: white; font-family: sans-serif; }
        /* TÉCNICA 1: CSS BLUR (Anti-Screenshot) */
        .msg-bubble { 
            background: #202c33; padding: 10px; margin: 10px; border-radius: 10px; 
            filter: blur(12px); transition: 0.2s; user-select: none;
        }
        .msg-bubble:active { filter: blur(0px); } /* Desfoca ao soltar */
        canvas { max-width: 100%; }
        .footer { position: fixed; bottom: 0; width: 100%; background: #202c33; padding: 10px; }
        #msgInput { width: 70%; padding: 10px; border-radius: 20px; border: none; }
    </style>
</head>
<body>
    <div id="chat-container">
        {% for m in msgs %}
        <div class="msg-bubble">
            <canvas class="canvas-msg" data-text="{{ m.texto }}"></canvas>
        </div>
        {% endfor %}
    </div>

    <form class="footer" onsubmit="enviar(event)">
        <input type="text" id="msgInput" placeholder="Mensagem">
        <button type="submit" style="background: none; border: none; color: #00a884; font-size: 20px;">➔</button>
    </form>

    <script>
        function renderCanvas() {
            document.querySelectorAll('.canvas-msg').forEach(canv => {
                const ctx = canv.getContext('2d');
                const text = canv.getAttribute('data-text');
                canv.width = 300; canv.height = 30;
                ctx.fillStyle = "white"; ctx.font = "16px Arial";
                ctx.fillText(text, 10, 20);
            });
        }

        function enviar(e) {
            e.preventDefault();
            const input = document.getElementById('msgInput');
            console.log("Enviando:", input.value);
            input.value = ""; // LIMPEZA INSTANTÂNEA
            input.blur(); // FECHA TECLADO
            alert("Enviado e campo limpo!");
        }

        window.onload = renderCanvas;
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)

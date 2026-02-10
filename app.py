import os
import psycopg2
from flask import Flask, request, render_template_string, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = "teste_seguranca_blindada"

# Configurações de Ambiente para Teste
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Simulação de login simples para teste
        session['usuario'] = "Teste"
        return redirect(url_for('chat_test'))
    return render_template_string('''
        <form method="post">
            <input type="password" name="pw" placeholder="Senha de Teste">
            <button type="submit">Entrar no Ambiente Blindado</button>
        </form>
    ''')

@app.route("/chat_test")
def chat_test():
    if 'usuario' not in session: return redirect(url_for('login'))
    
    # Mensagens estáticas para testar a renderização
    test_msgs = [
        {"id": 1, "autor": "Ele", "texto": "Esta mensagem está em um Canvas.", "hora": "10:00"},
        {"id": 2, "autor": "Ela", "texto": "E esta só aparece com o toque.", "hora": "10:05"}
    ]

    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
            <style>
                body { background: #0b141a; color: white; font-family: sans-serif; }
                .chat-container { display: flex; flex-direction: column; padding: 10px; }
                
                /* TÉCNICA 1: CSS BLUR */
                .msg-bubble {
                    background: #1b272e;
                    padding: 10px;
                    border-radius: 10px;
                    margin-bottom: 10px;
                    max-width: 80%;
                    filter: blur(15px); /* Desfoque agressivo */
                    transition: filter 0.2s;
                    user-select: none;
                    cursor: pointer;
                }
                .msg-bubble.reveal { filter: blur(0px); }
                
                canvas { max-width: 100%; height: auto; }
                .time { font-size: 10px; color: #8696a0; display: block; margin-top: 5px; }
            </style>
        </head>
        <body>
            <div class="chat-container">
                {% for m in msgs %}
                <div class="msg-bubble" 
                     ontouchstart="this.classList.add('reveal')" 
                     ontouchend="this.classList.remove('reveal')"
                     onmousedown="this.classList.add('reveal')" 
                     onmouseup="this.classList.remove('reveal')">
                    
                    <canvas id="canvas_{{ m.id }}" data-text="{{ m.texto }}"></canvas>
                    
                    <span class="time">{{ m.hora }}</span>
                </div>
                {% endfor %}
            </div>

            <script>
                // Função para desenhar texto no Canvas (Impede leitura por apps de acessibilidade)
                function renderCanvasMessages() {
                    const canvases = document.querySelectorAll('.canvas-msg, canvas[data-text]');
                    canvases.forEach(canvas => {
                        const ctx = canvas.getContext('2d');
                        const text = canvas.getAttribute('data-text');
                        
                        // Ajuste de DPI para não ficar serrilhado
                        canvas.width = 400;
                        canvas.height = 50;
                        
                        ctx.fillStyle = "white";
                        ctx.font = "24px Arial";
                        ctx.fillText(text, 10, 35);
                    });
                }

                window.onload = renderCanvasMessages;

                // TÉCNICA 3: MENSAGEM CRIPTOGRAFADA (Simulação de Envio)
                function enviarMensagemBlindada() {
                    let rawText = document.getElementById('inputMsg').value;
                    // Aqui entraria a Web Crypto API para cifrar antes do POST
                    let encrypted = btoa(rawText); // Simulação simples com Base64
                    console.log("Enviando para o servidor:", encrypted);
                }
            </script>
        </body>
        </html>
    ''', msgs=test_msgs)

if __name__ == "__main__":
    app.run(debug=True)

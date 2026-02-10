# app_blindado_teste.py
from flask import Flask, render_template_string, request, session

app = Flask(__name__)
app.secret_key = "segredo_extremo"

@app.route("/")
def index():
    # Simulação de mensagens para o Canvas
    msgs = [{"id": 1, "texto": "Mensagem protegida pelo Canvas"}]
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                .msg-bubble { filter: blur(10px); background: #222; color: white; padding: 10px; margin: 10px; }
                .msg-bubble:active { filter: blur(0px); } /* Desfoca ao soltar o dedo */
                #msgInput { width: 80%; padding: 10px; }
            </style>
        </head>
        <body>
            <div id="chat">
                {% for m in msgs %}
                <div class="msg-bubble">
                    <canvas class="canvas-msg" data-text="{{ m.texto }}"></canvas>
                </div>
                {% endfor %}
            </div>

            <form id="chatForm" onsubmit="enviar(event)">
                <input type="text" id="msgInput" placeholder="Digite aqui...">
                <button type="submit">Enviar</button>
            </form>

            <script>
                // 1. RENDERIZA O CANVAS (Cega a Acessibilidade)
                function render() {
                    document.querySelectorAll('.canvas-msg').forEach(canv => {
                        const ctx = canv.getContext('2d');
                        canv.width = 300; canv.height = 30;
                        ctx.fillStyle = "white"; ctx.font = "16px Arial";
                        ctx.fillText(canv.getAttribute('data-text'), 10, 20);
                    });
                }

                // 2. LIMPEZA AGRESSIVA (Protege contra Screen Loggers no envio)
                function enviar(e) {
                    e.preventDefault();
                    const input = document.getElementById('msgInput');
                    const textoOriginal = input.value;

                    // Limpa IMEDIATAMENTE antes de qualquer processamento
                    input.value = ""; 
                    input.blur(); // Tira o foco para fechar o teclado do celular rápido
                    
                    console.log("Enviando via AJAX/Fetch para o servidor:", textoOriginal);
                    alert("Mensagem enviada e campo limpo instantaneamente!");
                }

                window.onload = render;
            </script>
        </body>
        </html>
    ''', msgs=msgs)

if __name__ == "__main__":
    app.run(debug=True)

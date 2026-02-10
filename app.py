import os
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route("/")
def test_anonimo():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Teste de Segurança</title>
            <style>
                body { 
                    background: #0b141a; 
                    color: white; 
                    font-family: sans-serif; 
                    display: flex; 
                    flex-direction: column; 
                    align-items: center; 
                    justify-content: center; 
                    height: 100vh; 
                    margin: 0; 
                }
                #status_box { 
                    padding: 30px; 
                    border-radius: 15px; 
                    text-align: center; 
                    transition: 0.5s;
                    width: 80%;
                    max-width: 400px;
                }
                .pendente { background: #2a3942; }
                .anonimo { background: #00a884; border: 2px solid #fff; }
                .normal { background: #ef5350; border: 2px solid #fff; }
                h1 { margin: 0 0 10px 0; font-size: 20px; }
                p { margin: 5px 0; font-size: 14px; opacity: 0.8; }
            </style>
        </head>
        <body>

            <div id="status_box" class="pendente">
                <h1 id="msg">Analisando Navegação...</h1>
                <p id="detalhe">Aguardando resposta do sistema...</p>
            </div>

            <script>
                async function validarAcesso() {
                    const box = document.getElementById('status_box');
                    const msg = document.getElementById('msg');
                    const detalhe = document.getElementById('detalhe');

                    if ('storage' in navigator && 'estimate' in navigator.storage) {
                        const {quota} = await navigator.storage.estimate();
                        const quotaMB = Math.round(quota / (1024 * 1024));
                        
                        // No Chrome Mobile, a quota em modo anônimo é drasticamente reduzida
                        // O limite de 1000MB (1GB) costuma ser a linha divisória clara
                        if (quotaMB < 1000) {
                            box.className = "anonimo";
                            msg.innerText = "✅ MODO ANÔNIMO DETECTADO";
                            detalhe.innerText = "Sua cota de disco é limitada: " + quotaMB + "MB. Seguro para o Cofre.";
                        } else {
                            box.className = "normal";
                            msg.innerText = "❌ NAVEGAÇÃO NORMAL";
                            detalhe.innerText = "Cota de disco alta: " + quotaMB + "MB. Risco de histórico detectado.";
                        }
                    } else {
                        msg.innerText = "⚠️ Erro de Compatibilidade";
                        detalhe.innerText = "Seu navegador não suporta a API de detecção.";
                    }
                }

                // Executa a validação após 1 segundo para garantir o carregamento
                setTimeout(validarAcesso, 1000);
            </script>
        </body>
        </html>
    ''')

if __name__ == "__main__":
    app.run(debug=True)

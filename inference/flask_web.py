from flask import Flask, request, jsonify
try:
    from .generator import TextGenerator
except ImportError:
    from generator import TextGenerator


def start_demo(model_path="../models/all_models/latest.pt", vocab_path="../processed_data/vocabulary.json"):
    """Start simple Flask demo"""
    app = Flask(__name__)
    generator = TextGenerator(model_path, vocab_path)

    @app.route('/')
    def index():
        return '''
        <!DOCTYPE html>
        <html>
        <head>
                <title>EL EL M</title>
            <style>
                body {
                    margin: 0;
                    font-family: Arial, sans-serif;
                    background: #f5f5f5;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    width: 100%;
                    padding: 20px;
                    flex: 1;
                    overflow-y: auto;
                }
                .message {
                    margin: 10px 0;
                    padding: 10px 15px;
                    border-radius: 10px;
                    max-width: 80%;
                }
                .user {
                    background: #965Fd4;
                    color: white;
                    margin-left: auto;
                    text-align: right;
                }
                .assistant {
                    background: #e9ecef;
                    color: #333;
                }
                .input-area {
                    background: white;
                    padding: 20px;
                    border-top: 1px solid #ddd;
                }
                .input-container {
                    max-width: 800px;
                    margin: 0 auto;
                    display: flex;
                    gap: 10px;
                }
                textarea {
                    flex: 1;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    resize: none;
                    font-family: Arial, sans-serif;
                }
                button {
                    padding: 10px 20px;
                    background: #965Fd4;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
                button:hover {
                    background: #0056b3;
                }
            </style>
        </head>
        <body>
            <div class="container" id="chat"></div>
            <div class="input-area">
                <div class="input-container">
                    <textarea id="prompt" rows="3" placeholder="Type a message..."></textarea>
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
            <script>
                async function sendMessage() {
                    const prompt = document.getElementById('prompt').value;
                    if (!prompt) return;

                    // Add user message
                    const chat = document.getElementById('chat');
                    chat.innerHTML += `<div class="message user">${prompt}</div>`;

                    // Clear user input
                    document.getElementById('prompt').value = '';

                    // Get the response
                    const response = await fetch('/generate', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({prompt: prompt})
                    });
                    const data = await response.json();

                    // Add the LLM message
                    chat.innerHTML += `<div class="message assistant">${data.result}</div>`;
                    chat.scrollTop = chat.scrollHeight;
                }

                // Enter to send
                document.getElementById('prompt').addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                });
            </script>
        </body>
        </html>
        '''

    @app.route('/generate', methods=['POST'])
    def generate():
        prompt = request.json['prompt']
        result = generator.generate(prompt, 30, 0.8)
        return jsonify({'result': result})

    print("Starting demo at http://localhost:5000")
    app.run(port=5000)


if __name__ == "__main__":
    start_demo()
from flask import Flask, request, jsonify
from flask_cors import CORS
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import psutil
import os
import json

try:
    from .generator import TextGenerator
except ImportError:
    from generator import TextGenerator

# Prometheus
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
GENERATION_COUNT = Counter('text_generations_total', 'Total text generations', ['status'])
GENERATION_DURATION = Histogram('text_generation_duration_seconds', 'Text generation duration')


def create_app(model_path="../models/all_models/latest.pt", vocab_path="../processed_data/vocabulary.json"):
    """Create Flask webapp"""
    app = Flask(__name__)
    CORS(app)

    # Initialize generator
    try:
        generator = TextGenerator(model_path, vocab_path)
        app_healthy = True
        startup_error = None
    except Exception as e:
        generator = None
        app_healthy = False
        startup_error = str(e)
        print(f"Failed to initialize generator: {e}")

    @app.before_request
    def before_request():
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            REQUEST_DURATION.observe(duration)
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=response.status_code
            ).inc()
        return response

    @app.route('/')
    def index():
        return '''
        <!DOCTYPE html>
        <html>
        <head>
                <title>Jenkins LLM API</title>
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
                .status {
                    text-align: center;
                    padding: 10px;
                    background: #e8f5e8;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .status.error {
                    background: #ffe6e6;
                    color: #cc0000;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="status''' + (' error' if not app_healthy else '') + '''">
                    Status: ''' + (
            'Generator Error - ' + (startup_error or 'Unknown error') if not app_healthy else 'System Ready') + '''
                </div>
                <div id="chat"></div>
            </div>
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

                    const chat = document.getElementById('chat');
                    chat.innerHTML += `<div class="message user">${prompt}</div>`;

                    document.getElementById('prompt').value = '';

                    try {
                        const response = await fetch('/generate', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({prompt: prompt})
                        });
                        const data = await response.json();

                        if (data.error) {
                            chat.innerHTML += `<div class="message assistant" style="background: #ffe6e6; color: #cc0000;">Error: ${data.error}</div>`;
                        } else {
                            chat.innerHTML += `<div class="message assistant">${data.result}</div>`;
                        }
                    } catch (error) {
                        chat.innerHTML += `<div class="message assistant" style="background: #ffe6e6; color: #cc0000;">Connection error: ${error.message}</div>`;
                    }

                    chat.scrollTop = chat.scrollHeight;
                }

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
        start_time = time.time()

        if not app_healthy or not generator:
            GENERATION_COUNT.labels(status='error').inc()
            return jsonify({
                'error': 'Generator not available',
                'details': startup_error
            }), 503

        try:
            prompt = request.json.get('prompt', '') if request.json else ''
            result = generator.generate(prompt, 30, 0.8)

            duration = time.time() - start_time
            GENERATION_DURATION.observe(duration)
            GENERATION_COUNT.labels(status='success').inc()

            return jsonify({
                'result': result,
                'prompt': prompt,
                'generation_time': round(duration, 3)
            })
        except Exception as e:
            duration = time.time() - start_time
            GENERATION_DURATION.observe(duration)
            GENERATION_COUNT.labels(status='error').inc()

            return jsonify({
                'error': str(e),
                'prompt': request.json.get('prompt', '') if request.json else ''
            }), 500

    @app.route('/health')
    def health():
        """Health check monitor"""
        try:
            # Basic health checks
            health_status = {
                'status': 'healthy' if app_healthy else 'unhealthy',
                'timestamp': time.time(),
                'version': os.environ.get('APP_VERSION', 'unknown'),
                'environment': os.environ.get('ENVIRONMENT', 'development'),
                'generator_loaded': generator is not None,
                'startup_error': startup_error if startup_error else None
            }

            # Test generator
            if generator:
                try:
                    test_result = generator.generate("health", max_length=5)
                    health_status['generator_test'] = 'passed'
                except Exception as e:
                    health_status['generator_test'] = f'failed: {str(e)}'
                    health_status['status'] = 'degraded'

            status_code = 200 if health_status['status'] == 'healthy' else 503
            return jsonify(health_status), status_code

        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }), 500

    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint"""
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

    @app.route('/status')
    def status():
        """Status information"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            status_info = {
                'service': 'jenkins-llm',
                'status': 'running',
                'healthy': app_healthy,
                'timestamp': time.time(),
                'uptime': time.time() - (getattr(app, 'start_time', time.time())),
                'version': {
                    'build': os.environ.get('BUILD_NUMBER', 'unknown'),
                    'commit': os.environ.get('GIT_COMMIT', 'unknown'),
                    'environment': os.environ.get('ENVIRONMENT', 'development')
                },
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': round(memory.available / (1024 ** 3), 2),
                    'disk_percent': disk.percent,
                    'disk_free_gb': round(disk.free / (1024 ** 3), 2)
                },
                'application': {
                    'generator_loaded': generator is not None,
                    'model_path': model_path,
                    'vocab_path': vocab_path,
                    'startup_error': startup_error
                }
            }

            return jsonify(status_info)

        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }), 500

    @app.route('/ready')
    def ready():
        """Probe ready Docker"""
        if app_healthy and generator:
            return jsonify({'status': 'ready'}), 200
        else:
            return jsonify({
                'status': 'not ready',
                'reason': startup_error or 'Generator not loaded'
            }), 503

    # Set start time
    app.start_time = time.time()

    return app


def start_demo(model_path="../models/all_models/latest.pt", vocab_path="../processed_data/vocabulary.json", port=5000):
    """Start Flask"""
    app = create_app(model_path, vocab_path)

    print(f"🚀 Starting Jenkins LLM API on port {port}")
    print(f"📊 Health endpoint: http://localhost:{port}/health")
    print(f"📈 Metrics endpoint: http://localhost:{port}/metrics")
    print(f"📋 Status endpoint: http://localhost:{port}/status")

    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    start_demo(port=port)
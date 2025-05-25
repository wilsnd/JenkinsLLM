from flask import Flask, request
from generator import TextGenerator

def start_demo(model_path="../models/all_models/latest.pt", vocab_path="../processed_data/vocabulary.json"):
    """Start simple Flask demo"""
    app = Flask(__name__)
    generator = TextGenerator(model_path, vocab_path)

    @app.route('/', methods=['GET', 'POST'])
    def demo():
        if request.method == 'POST':
            prompt = request.form['prompt']
            result = generator.generate(prompt, 30, 0.8)
            return f"<h1>Result:</h1><p>{result}</p><a href='/'>Back</a>"

        return '''
        <h1>Text Generator</h1>
        <form method="post">
            <input name="prompt" placeholder="Enter prompt..." style="width:300px;padding:10px;">
            <button type="submit">Generate</button>
        </form>
        '''

    print("Starting demo at http://localhost:5000")
    app.run(port=5000)

if __name__ == "__main__":
    start_demo()
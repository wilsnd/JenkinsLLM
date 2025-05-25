import gradio as gr
from generator import TextGenerator
import os


class GradioDemo:
    """Simple web demo using Gradio"""

    def __init__(self, model_path="../models/all_models/latest.pt", vocab_path="../processed_data/vocabulary.json"):
        self.generator = TextGenerator(model_path, vocab_path)
        print("Gradio demo initialized")

    def generate_interface(self, prompt, max_length, temperature):
        """Interface function for Gradio"""
        try:
            result = self.generator.generate(prompt, int(max_length), float(temperature))
            return result
        except Exception as e:
            return f"Error: {str(e)}"

    def create_interface(self):
        """Create Gradio interface"""

        interface = gr.Interface(
            fn=self.generate_interface,
            inputs=[
                gr.Textbox(
                    label="Prompt",
                    placeholder="Enter your text prompt here...",
                    value="hello world"
                ),
                gr.Slider(
                    minimum=5,
                    maximum=100,
                    value=30,
                    step=5,
                    label="Max Length"
                ),
                gr.Slider(
                    minimum=0.1,
                    maximum=2.0,
                    value=0.8,
                    step=0.1,
                    label="Temperature"
                )
            ],
            outputs=[
                gr.Textbox(label="Generated Text")
            ],
            title="El El M Text Generator",
            description="Generate text using your trained language model",
            examples=[
                ["hello world", 30, 0.8],
                ["the quick brown", 25, 0.7],
                ["artificial intelligence", 40, 0.9],
                ["", 20, 0.8]
            ]
        )

        return interface

    def launch(self, share=False, port=7860):
        """Launch the demo"""
        interface = self.create_interface()

        print(f"Starting Gradio demo on port {port}")
        if share:
            print("Creating shareable link...")

        interface.launch(
            share=share,
            server_port=port,
            server_name="0.0.0.0"
        )


def create_demo():
    """Create demo instance"""
    try:
        return GradioDemo()
    except Exception as e:
        print(f"Failed to create demo: {e}")
        return None


def launch_demo(share=False, port=7860):
    """Quick function to launch demo"""
    demo = create_demo()
    if demo:
        demo.launch(share=share, port=port)
    else:
        print("Demo not available")


if __name__ == "__main__":
    print("=== GRADIO DEMO ===")

    # Check if model exists
    model_path = "../models/all_models/latest.pt"
    if os.path.exists(model_path):
        demo = GradioDemo()
        demo.launch(share=False, port=7860)
    else:
        print(f"Model not found at {model_path}")
        print("Go train a model first!!!!!")
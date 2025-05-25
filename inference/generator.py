import torch
import json
from model import create_model


class TextGenerator:
    """Simple text generator"""

    def __init__(self, model_path, vocab_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Load vocabulary
        with open(vocab_path, 'r') as f:
            self.vocab = json.load(f)

        # Create reverse vocab ID to word
        self.id_to_word = {v: k for k, v in self.vocab.items()}

        # Load model
        self.model = create_model(vocab_size=len(self.vocab))
        self.model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=False))
        self.model.to(self.device)
        self.model.eval()

        print(f"Generator loaded on {self.device}")
        print(f"Vocabulary size: {len(self.vocab)}")

    def text_to_ids(self, text):
        """Convert text to token IDs"""
        words = text.lower().split()
        ids = [self.vocab['<START>']]

        for word in words:
            if word in self.vocab:
                ids.append(self.vocab[word])
            else:
                ids.append(self.vocab['<UNK>'])

        return ids

    def ids_to_text(self, ids):
        """Convert token IDs to text"""
        words = []
        for id in ids:
            if id in self.id_to_word:
                word = self.id_to_word[id]
                if word not in ['<START>', '<END>', '<PAD>']:
                    words.append(word)

        return ' '.join(words)

    def generate(self, prompt="", max_length=50, temperature=0.8):
        """Generate text from prompt"""

        if prompt:
            input_ids = self.text_to_ids(prompt)
        else:
            input_ids = [self.vocab['<START>']]

        input_tensor = torch.tensor([input_ids], dtype=torch.long).to(self.device)

        with torch.no_grad():
            for _ in range(max_length):
                # Get model output
                outputs = self.model(input_tensor)
                next_token_logits = outputs[0, -1, :] / temperature

                # Block tokens
                unk_id = self.vocab['<UNK>']
                pad_id = self.vocab['<PAD>']
                start_id = self.vocab['<START>']
                next_token_logits[unk_id] = -1e10  # Block UNK
                next_token_logits[pad_id] = -1e10  # Block PAD
                next_token_logits[start_id] = -1e10  # Block START

                # Sample next token
                probs = torch.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)

                # Stop if end token
                if next_token.item() == self.vocab['<END>']:
                    break

                # Add to sequence
                input_tensor = torch.cat([input_tensor, next_token.unsqueeze(0)], dim=1)

        # Convert back to text
        generated_ids = input_tensor[0].tolist()
        return self.ids_to_text(generated_ids)


def load_generator(model_path="../models/all_models/latest.pt", vocab_path="../processed_data/vocabulary.json"):
    """Load generator"""
    return TextGenerator(model_path, vocab_path)


def generate_text(prompt="", max_length=50, temperature=0.8):
    """Quick generation"""
    generator = load_generator()
    return generator.generate(prompt, max_length, temperature)


if __name__ == "__main__":
    # Test generation
    generator = load_generator()

    print("=== TEXT GENERATION TEST ===")

    # Test with prompt
    result = generator.generate("hello world", max_length=20)
    print(f"Prompt: 'hello world'")
    print(f"Generated: {result}")

    # Test w/o prompt
    result = generator.generate("", max_length=20)
    print(f"\nNo prompt:")
    print(f"Generated: {result}")
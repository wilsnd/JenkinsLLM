import json
import torch
from tqdm import tqdm
from generator import TextGenerator


class BatchInference:
    """Process multiple texts at once"""

    def __init__(self, model_path, vocab_path):
        self.generator = TextGenerator(model_path, vocab_path)
        print("Batch inference ready")

    def process_prompts(self, prompts, max_length=50, temperature=0.8):
        """Process list of prompts"""
        results = []

        print(f"Processing {len(prompts)} prompts...")

        for prompt in tqdm(prompts, desc="Generating"):
            try:
                generated_text = self.generator.generate(prompt, max_length, temperature)

                results.append({
                    "prompt": prompt,
                    "generated_text": generated_text,
                    "success": True
                })

            except Exception as e:
                results.append({
                    "prompt": prompt,
                    "error": str(e),
                    "success": False
                })

        return results

    def process_file(self, input_file, output_file, max_length=50, temperature=0.8):
        """Process prompts from file"""

        # Load prompts
        if input_file.endswith('.json'):
            with open(input_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    prompts = data
                else:
                    prompts = data.get('prompts', [])
        else:
            # Assume text file with one prompt per line
            with open(input_file, 'r') as f:
                prompts = [line.strip() for line in f if line.strip()]

        # Process
        results = self.process_prompts(prompts, max_length, temperature)

        # Save results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Print summary
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful

        print(f"\n=== BATCH RESULTS ===")
        print(f"Total prompts: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Results saved to: {output_file}")

        return results

    def evaluate_samples(self, test_file, num_samples=10):
        """Quick eval on test samples"""

        print(f"=== EVALUATING {num_samples} SAMPLES ===")

        # Load test data
        with open(test_file, 'r') as f:
            test_data = json.load(f)

        # Take random samples
        import random
        samples = random.sample(test_data, min(num_samples, len(test_data)))

        results = []

        for i, sample in enumerate(samples):
            print(f"\nSample {i + 1}:")

            # Convert first few tokens to prompt
            if len(sample) > 5:
                prompt_ids = sample[:3]  # First 3 tokens as prompt
                target_ids = sample[3:8]  # Next 5 as target

                prompt_text = self.generator.ids_to_text(prompt_ids)
                target_text = self.generator.ids_to_text(target_ids)

                # Generate
                generated = self.generator.generate(prompt_text, max_length=10)

                print(f"Prompt: {prompt_text}")
                print(f"Target: {target_text}")
                print(f"Generated: {generated}")

                results.append({
                    "prompt": prompt_text,
                    "target": target_text,
                    "generated": generated
                })

        return results


def run_batch_inference(input_file, output_file, model_path="../models/all_models/latest.pt",
                        vocab_path="../processed_data/vocabulary.json"):
    """Run batch inference"""
    batch = BatchInference(model_path, vocab_path)
    return batch.process_file(input_file, output_file)


if __name__ == "__main__":
    # Example usage
    batch = BatchInference("../models/all_models/latest.pt", "../processed_data/vocabulary.json")

    # Test sample
    test_prompts = [
        "hello world",
        "the quick brown",
        "machine learning is",
        "artificial intelligence",
        ""
    ]

    results = batch.process_prompts(test_prompts, max_length=20)

    print("\n=== BATCH TEST RESULTS ===")
    for result in results:
        if result['success']:
            print(f"'{result['prompt']}' → '{result['generated_text']}'")
        else:
            print(f"'{result['prompt']}' → ERROR: {result['error']}")
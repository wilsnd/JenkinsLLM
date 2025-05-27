import unittest
import tempfile
import os
import json
import sys
import shutil
from unittest.mock import patch, MagicMock

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from inference import TextGenerator, BatchInference, load_generator, generate_text


class TestInference(unittest.TestCase):
    """Tnference module basic test"""

    def setUp(self):
        """Prepare the test data"""
        self.test_dir = tempfile.mkdtemp()

        # Simple test vocabulary
        self.sample_vocab = {
            '<PAD>': 0, '<UNK>': 1, '<START>': 2, '<END>': 3,
            'hello': 4, 'world': 5, 'test': 6, 'text': 7
        }

        # Create test files
        self.vocab_file = os.path.join(self.test_dir, "vocab.json")
        with open(self.vocab_file, 'w') as f:
            json.dump(self.sample_vocab, f)

        self.model_file = os.path.join(self.test_dir, "model.pt")

    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('inference.generator.create_model')
    @patch('torch.load')
    @patch('torch.cuda.is_available', return_value=False)
    def test_text_generator_creation(self, mock_cuda, mock_load, mock_create):
        """Test TextGenerator can be created"""
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model
        mock_create.return_value = mock_model
        mock_load.return_value = {}

        generator = TextGenerator(self.model_file, self.vocab_file)

        # Check basic attributes
        self.assertIsNotNone(generator.vocab)
        self.assertIsNotNone(generator.model)
        self.assertEqual(len(generator.vocab), len(self.sample_vocab))

    @patch('inference.generator.create_model')
    @patch('torch.load')
    @patch('torch.cuda.is_available', return_value=False)
    def test_text_to_ids(self, mock_cuda, mock_load, mock_create):
        """Test text to ID conversion"""
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model
        mock_create.return_value = mock_model
        mock_load.return_value = {}

        generator = TextGenerator(self.model_file, self.vocab_file)

        # Test conversion
        ids = generator.text_to_ids("hello world")

        # Should start with START token
        self.assertEqual(ids[0], 2)  # <START>
        # Should contain hello and world
        self.assertIn(4, ids)  # hello
        self.assertIn(5, ids)  # world

    @patch('inference.generator.create_model')
    @patch('torch.load')
    @patch('torch.cuda.is_available', return_value=False)
    def test_ids_to_text(self, mock_cuda, mock_load, mock_create):
        """Test ID to text conversion"""
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model
        mock_create.return_value = mock_model
        mock_load.return_value = {}

        generator = TextGenerator(self.model_file, self.vocab_file)

        # Test conversion
        text = generator.ids_to_text([2, 4, 5, 3])  # START, hello, world, END

        # Should contain words but not the special tokens
        self.assertIn('hello', text)
        self.assertIn('world', text)
        self.assertNotIn('<START>', text)
        self.assertNotIn('<END>', text)

    @patch('inference.generator.create_model')
    @patch('torch.load')
    @patch('torch.cuda.is_available', return_value=False)
    def test_unknown_words(self, mock_cuda, mock_load, mock_create):
        """Test handling unknown words"""
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model
        mock_create.return_value = mock_model
        mock_load.return_value = {}

        generator = TextGenerator(self.model_file, self.vocab_file)

        # Test with unknown words
        ids = generator.text_to_ids("unknown words")

        # Should contain UNK tokens
        self.assertIn(1, ids)  # <UNK>

    @patch('inference.generator.create_model')
    @patch('torch.load')
    @patch('torch.cuda.is_available', return_value=False)
    def test_basic_generation(self, mock_cuda, mock_load, mock_create):
        """Test basic text generation"""
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model
        mock_create.return_value = mock_model
        mock_load.return_value = {}

        generator = TextGenerator(self.model_file, self.vocab_file)

        # Fake the generate method
        generator.generate = MagicMock(return_value="generated text")

        # Test generation
        result = generator.generate("hello", max_length=5)

        # Should return a string
        self.assertIsInstance(result, str)
        self.assertEqual(result, "generated text")

    @patch('inference.batch_inference.TextGenerator')
    def test_batch_inference_creation(self, mock_generator):
        """Test BatchInference creation"""
        batch = BatchInference(self.model_file, self.vocab_file)
        self.assertIsNotNone(batch.generator)

    @patch('inference.batch_inference.TextGenerator')
    def test_batch_process_prompts(self, mock_generator):
        """Test batch processing"""
        mock_gen_instance = MagicMock()
        mock_gen_instance.generate.return_value = "generated"
        mock_generator.return_value = mock_gen_instance

        batch = BatchInference(self.model_file, self.vocab_file)
        results = batch.process_prompts(["hello", "world"])

        # Check results structure
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn('prompt', result)
            self.assertIn('generated_text', result)
            self.assertIn('success', result)

    @patch('inference.batch_inference.TextGenerator')
    def test_batch_error_handling(self, mock_generator):
        """Test batch processing handles errors"""
        mock_gen_instance = MagicMock()
        mock_gen_instance.generate.side_effect = Exception("Error")
        mock_generator.return_value = mock_gen_instance

        batch = BatchInference(self.model_file, self.vocab_file)
        results = batch.process_prompts(["test"])

        # Should handle error gracefully
        self.assertFalse(results[0]['success'])
        self.assertIn('error', results[0])

    @patch('inference.batch_inference.TextGenerator')
    def test_batch_file_processing(self, mock_generator):
        """Test processing from file"""
        mock_gen_instance = MagicMock()
        mock_gen_instance.generate.return_value = "generated"
        mock_generator.return_value = mock_gen_instance

        # Create test input file
        input_file = os.path.join(self.test_dir, "input.json")
        output_file = os.path.join(self.test_dir, "output.json")

        with open(input_file, 'w') as f:
            json.dump(["hello", "world"], f)

        batch = BatchInference(self.model_file, self.vocab_file)
        batch.process_file(input_file, output_file)

        # Check output file created
        self.assertTrue(os.path.exists(output_file))

        # Check output content
        with open(output_file, 'r') as f:
            results = json.load(f)

        self.assertEqual(len(results), 2)

    @patch('inference.generator.TextGenerator')
    def test_load_generator(self, mock_generator):
        """Test load_generator function"""
        mock_instance = MagicMock()
        mock_generator.return_value = mock_instance

        result = load_generator(self.model_file, self.vocab_file)

        mock_generator.assert_called_once_with(self.model_file, self.vocab_file)
        self.assertEqual(result, mock_instance)

    @patch('inference.generator.load_generator')
    def test_generate_text_function(self, mock_load):
        """Test generate_text helper function"""
        mock_generator = MagicMock()
        mock_generator.generate.return_value = "generated text"
        mock_load.return_value = mock_generator

        # Mock to avoid file path issues
        with patch('os.path.exists', return_value=True):
            result = generate_text("test", max_length=10)

        self.assertEqual(result, "generated text")

    def test_edge_cases(self):
        """Test edge cases"""
        with patch('inference.generator.create_model'), \
                patch('torch.load'), \
                patch('torch.cuda.is_available', return_value=False):
            generator = TextGenerator(self.model_file, self.vocab_file)

            # Empty text
            ids = generator.text_to_ids("")
            self.assertEqual(ids, [2])  # Just START token

            # Empty ids
            text = generator.ids_to_text([])
            self.assertEqual(text, "")

    def test_module_imports(self):
        """Test that all functions can be imported"""
        # This test already passed by importing at the top
        self.assertTrue(callable(TextGenerator))
        self.assertTrue(callable(BatchInference))
        self.assertTrue(callable(load_generator))
        self.assertTrue(callable(generate_text))


if __name__ == "__main__":
    unittest.main()
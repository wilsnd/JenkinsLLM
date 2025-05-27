import unittest
import tempfile
import os
import json
import sys
import shutil
from unittest.mock import patch, mock_open

# Project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from preparation import (
    tokenize, build_vocabulary, convert_to_id, split_data,
    DataValidator, validate_all, prepare_data, get_preparation_config
)
from preparation.convert_id import words_to_ids


class TestPreparation(unittest.TestCase):
    """Test preparation module"""

    def setUp(self):
        """Set up test data"""
        # Test configuration
        self.config = get_preparation_config()

        # Sample text data for tokenization
        self.sample_text = """This is the first document. 
        It has multiple sentences and words.
        
        ---
                            
        This is the second document.
        It contains different content and vocabulary.
        
        ---
        
        A third document with more text.
        Testing tokenization and processing capabilities."""

        # Sample tokenized data
        self.sample_tokenized = [
            ["this", "is", "the", "first", "document"],
            ["it", "has", "multiple", "sentences", "and", "words"],
            ["this", "is", "the", "second", "document"],
            ["it", "contains", "different", "content", "and", "vocabulary"],
            ["a", "third", "document", "with", "more", "text"],
            ["testing", "tokenization", "and", "processing", "capabilities"]
        ]

        # Sample vocabulary
        self.sample_vocab = {
            '<PAD>': 0,
            '<UNK>': 1,
            '<START>': 2,
            '<END>': 3,
            'the': 4,
            'is': 5,
            'and': 6,
            'document': 7,
            'this': 8,
            'it': 9
        }

        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_config_loading(self):
        """Test configuration loading"""
        config = get_preparation_config()

        # Check required keys exist
        required_keys = [
            "min_vocab_frequency", "max_sequence_length", "train_split",
            "validation_split", "test_split", "special_tokens", "tokenization_method"
        ]

        for key in required_keys:
            self.assertIn(key, config)

        # Check specific values
        self.assertEqual(config["min_vocab_frequency"], 250)
        self.assertEqual(config["max_sequence_length"], 32)
        self.assertEqual(config["special_tokens"], ['<PAD>', '<UNK>', '<START>', '<END>'])

        # Check splits add up to 1.0
        total_split = config["train_split"] + config["validation_split"] + config["test_split"]
        self.assertAlmostEqual(total_split, 1.0, places=2)

    def test_tokenization(self):
        """Test text tokenization"""
        input_file = os.path.join(self.test_dir, "input.txt")
        output_file = os.path.join(self.test_dir, "tokenized.json")

        # Write test data
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(self.sample_text)

        # Test tokenization
        tokenize(input_file, output_file)

        # Check output exists
        self.assertTrue(os.path.exists(output_file))

        # Load and verify results
        with open(output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)

        # Should be a list of lists
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

        # Each document should be a list of words
        for doc in result:
            self.assertIsInstance(doc, list)
            for word in doc:
                self.assertIsInstance(word, str)
                self.assertEqual(word, word.lower())  # Should be lowercase

    def test_data_splitting(self):
        """Test data splitting into train/val/test"""
        input_file = os.path.join(self.test_dir, "tokenized.json")

        # Create test data with 100 documents
        test_data = [["word", str(i)] for i in range(100)]

        with open(input_file, 'w') as f:
            json.dump(test_data, f)

        # Test splitting
        split_data(input_file, self.test_dir)

        # Check files exist
        train_file = os.path.join(self.test_dir, "train.json")
        val_file = os.path.join(self.test_dir, "val.json")
        test_file = os.path.join(self.test_dir, "test.json")

        self.assertTrue(os.path.exists(train_file))
        self.assertTrue(os.path.exists(val_file))
        self.assertTrue(os.path.exists(test_file))

        # Load and check sizes
        with open(train_file, 'r') as f:
            train_data = json.load(f)
        with open(val_file, 'r') as f:
            val_data = json.load(f)
        with open(test_file, 'r') as f:
            test_data_loaded = json.load(f)

        # Check approximate split ratios (80/10/10)
        total = len(train_data) + len(val_data) + len(test_data_loaded)
        self.assertEqual(total, 100)
        self.assertAlmostEqual(len(train_data) / total, 0.8, delta=0.1)
        self.assertAlmostEqual(len(val_data) / total, 0.1, delta=0.1)
        self.assertAlmostEqual(len(test_data_loaded) / total, 0.1, delta=0.1)

    def test_vocabulary_building(self):
        """Test vocabulary building"""
        train_file = os.path.join(self.test_dir, "train.json")
        vocab_file = os.path.join(self.test_dir, "vocab.json")

        # Create training data with word frequencies
        train_data = [
            ["the", "cat", "sat"],
            ["the", "dog", "ran"],
            ["the", "cat", "ran"],
            ["a", "bird", "flew"]
        ]

        with open(train_file, 'w') as f:
            json.dump(train_data, f)

        # Build vocabulary with min_freq=2
        build_vocabulary(train_file, vocab_file, min_freq=2)

        # Check vocab file exists
        self.assertTrue(os.path.exists(vocab_file))

        # Load and verify vocabulary
        with open(vocab_file, 'r') as f:
            vocab = json.load(f)

        # Check special tokens
        required_tokens = ['<PAD>', '<UNK>', '<START>', '<END>']
        for token in required_tokens:
            self.assertIn(token, vocab)

        # Check frequent words are included
        self.assertIn('the', vocab)  # appears 3 times
        self.assertIn('cat', vocab)  # appears 2 times
        self.assertIn('ran', vocab)  # appears 2 times

        # Check infrequent words are excluded
        self.assertNotIn('a', vocab)  # appears 1 time
        self.assertNotIn('bird', vocab)  # appears 1 time
        self.assertNotIn('flew', vocab)  # appears 1 time

    def test_words_to_ids_conversion(self):
        """Test converting words to token IDs"""
        words = ["hello", "world", "unknown"]
        vocab = {
            '<PAD>': 0, '<UNK>': 1, '<START>': 2, '<END>': 3,
            'hello': 4, 'world': 5
        }

        doc_ids, unk_count = words_to_ids(words, vocab)

        # Check structure: [START, hello, world, UNK, END]
        expected = [2, 4, 5, 1, 3]  # START, hello, world, UNK, END
        self.assertEqual(doc_ids, expected)
        self.assertEqual(unk_count, 1)  # "unknown" becomes UNK

    def test_convert_to_id_file(self):
        """Test converting tokenized file to IDs"""
        tokenized_file = os.path.join(self.test_dir, "tokenized.json")
        vocab_file = os.path.join(self.test_dir, "vocab.json")
        output_file = os.path.join(self.test_dir, "ids.json")

        # Create test data
        tokenized_data = [["hello", "world"], ["good", "morning"]]
        vocab = {
            '<PAD>': 0, '<UNK>': 1, '<START>': 2, '<END>': 3,
            'hello': 4, 'world': 5, 'good': 6
        }

        with open(tokenized_file, 'w') as f:
            json.dump(tokenized_data, f)
        with open(vocab_file, 'w') as f:
            json.dump(vocab, f)

        # Convert to IDs
        convert_to_id(tokenized_file, vocab_file, output_file)

        # Check output
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, 'r') as f:
            result = json.load(f)

        # Should be list of ID sequences
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # Each sequence should start with START and end with END
        for seq in result:
            self.assertEqual(seq[0], 2)  # START token
            self.assertEqual(seq[-1], 3)  # END token

    def test_data_validator_class(self):
        """Test DataValidator class"""
        validator = DataValidator()

        # Test with non-existent file
        self.assertFalse(validator.validate_file("nonexistent.json"))
        self.assertFalse(validator.is_valid())

        # Reset validator
        validator = DataValidator()

        # Test with valid file
        test_file = os.path.join(self.test_dir, "test.json")
        with open(test_file, 'w') as f:
            json.dump({"test": "data"}, f)

        self.assertTrue(validator.validate_file(test_file))

        # Test vocabulary validation
        vocab_file = os.path.join(self.test_dir, "vocab.json")
        with open(vocab_file, 'w') as f:
            json.dump(self.sample_vocab, f)

        self.assertTrue(validator.validate_vocab(vocab_file))

        # Test training data validation
        train_file = os.path.join(self.test_dir, "train.json")
        with open(train_file, 'w') as f:
            json.dump(self.sample_tokenized, f)

        self.assertTrue(validator.validate_training_data(train_file))

    def test_sequence_length_handling(self):
        """Test handling of long sequences"""
        tokenized_file = os.path.join(self.test_dir, "tokenized.json")
        vocab_file = os.path.join(self.test_dir, "vocab.json")
        output_file = os.path.join(self.test_dir, "ids.json")

        # Create long sequence (> max_sequence_length)
        max_len = self.config["max_sequence_length"]
        long_sequence = ["word"] * (max_len + 10)  # Longer than max
        short_sequence = ["word"] * 5  # Shorter than max

        tokenized_data = [long_sequence, short_sequence]
        vocab = {'<PAD>': 0, '<UNK>': 1, '<START>': 2, '<END>': 3, 'word': 4}

        with open(tokenized_file, 'w') as f:
            json.dump(tokenized_data, f)
        with open(vocab_file, 'w') as f:
            json.dump(vocab, f)

        # Convert to IDs
        convert_to_id(tokenized_file, vocab_file, output_file)

        with open(output_file, 'r') as f:
            result = json.load(f)

        # Should have more sequences due to chunking
        self.assertGreater(len(result), 2)

        # All sequences should be within max length
        for seq in result:
            self.assertLessEqual(len(seq), max_len)

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test empty tokenization
        empty_file = os.path.join(self.test_dir, "empty.txt")
        output_file = os.path.join(self.test_dir, "empty_out.json")

        with open(empty_file, 'w') as f:
            f.write("")

        # Should handle empty input mindfully and demurely
        tokenize(empty_file, output_file)

        with open(output_file, 'r') as f:
            result = json.load(f)

        self.assertEqual(result, [])

    def test_integration_workflow(self):
        """Test the complete preparation workflow"""
        input_file = os.path.join(self.test_dir, "input.txt")

        # Write sample data
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(self.sample_text)

        # Fake the validate_all function to avoid file path issues
        with patch('preparation.prepare.validate_all', return_value=True):
            # Run complete pipeline
            success = prepare_data(input_file, self.test_dir, min_freq=1)

            self.assertTrue(success)

            # Check all expected files exist
            expected_files = [
                "tokenized.json", "train.json", "val.json", "test.json",
                "vocabulary.json", "train_ids.json", "val_ids.json", "test_ids.json"
            ]

            for filename in expected_files:
                filepath = os.path.join(self.test_dir, filename)
                self.assertTrue(os.path.exists(filepath), f"Missing file: {filename}")

    def test_config_consistency(self):
        """Test configuration consistency"""
        config = get_preparation_config()

        # Test that configuration is a copy
        config1 = get_preparation_config()
        config2 = get_preparation_config()

        config1["test_key"] = "test_value"
        self.assertNotIn("test_key", config2)

        # Test special tokens order
        special_tokens = config["special_tokens"]
        expected_order = ['<PAD>', '<UNK>', '<START>', '<END>']
        self.assertEqual(special_tokens, expected_order)


if __name__ == "__main__":
    unittest.main()
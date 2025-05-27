import unittest
import sys
import os
import tempfile
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from model.config import ModelConfig, DEFAULT_CONFIG
from preparation.config import get_preparation_config
from cleaning.config import get_cleaning_config


class TestConfigurationIntegration(unittest.TestCase):
    """Test configuration integration across all modules"""

    def test_model_config_consistency(self):
        """Test model configuration is consistent"""
        config = ModelConfig()

        # Test required attributes exist
        required_attrs = ['vocab_size', 'd_model', 'n_heads', 'n_layers']
        for attr in required_attrs:
            self.assertTrue(hasattr(config, attr))
            self.assertGreater(getattr(config, attr), 0)

        # Test d_model is divisible by n_heads
        self.assertEqual(config.d_model % config.n_heads, 0)

        print("✓ Model configuration is consistent")

    def test_preparation_config_integration(self):
        """Test preparation config integrates with other modules"""
        prep_config = get_preparation_config()

        # Test special tokens are correctly defined
        special_tokens = prep_config['special_tokens']
        expected_tokens = ['<PAD>', '<UNK>', '<START>', '<END>']
        self.assertEqual(special_tokens, expected_tokens)

        # Test sequence length is reasonable for model
        max_seq_len = prep_config['max_sequence_length']
        self.assertGreater(max_seq_len, 0)
        self.assertLess(max_seq_len, 1000)  # Reasonable upper bound

        print("✓ Preparation configuration integrates correctly")

    def test_cleaning_config_integration(self):
        """Test cleaning config has valid thresholds"""
        clean_config = get_cleaning_config()

        # Test thresholds are in valid ranges
        self.assertGreater(clean_config['english_threshold'], 0)
        self.assertLessEqual(clean_config['english_threshold'], 1)

        self.assertGreater(clean_config['content_ratio_threshold'], 0)
        self.assertLessEqual(clean_config['content_ratio_threshold'], 1)

        # Test text length constraints are logical
        self.assertGreater(clean_config['max_text_length'], clean_config['min_text_length'])

        print("✓ Cleaning configuration has valid parameters")

    def test_cross_module_compatibility(self):
        """Test configurations work together across modules"""
        model_config = DEFAULT_CONFIG
        prep_config = get_preparation_config()

        # Test vocab size compatibility
        # Model should be able to handle the vocabulary
        self.assertGreater(model_config.vocab_size, 100)  # Minimum reasonable vocab

        # Test sequence length compatibility
        model_seq_len = model_config.max_seq_len
        prep_seq_len = prep_config['max_sequence_length']

        # They should be compatible (within reasonable range)
        self.assertLessEqual(abs(model_seq_len - prep_seq_len), 100)

        print("✓ Cross-module configuration compatibility verified")

    def test_environment_config_integration(self):
        """Test environment-specific configuration works"""
        # Test that configs can be modified for different environments
        test_config = get_preparation_config()

        # Modify for testing (should be a copy)
        test_config['min_vocab_frequency'] = 1

        # Original should be unchanged
        original_config = get_preparation_config()
        self.assertNotEqual(test_config['min_vocab_frequency'],
                            original_config['min_vocab_frequency'])

        print("Environment configuration isolation is working")


if __name__ == "__main__":
    unittest.main()
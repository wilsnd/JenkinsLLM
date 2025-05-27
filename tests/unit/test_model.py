import unittest
import torch
import torch.nn as nn
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from model import (
    ModelConfig, DEFAULT_CONFIG, Embeddings, TokenEmbedding, PositionalEmbedding,
    MultiHeadAttention, create_causal_mask, TransformerBlock, TransformerDecoder,
    FeedForward, SimpleLLM, create_model, get_version
)


class TestModel(unittest.TestCase):
    """Test model module functionality"""

    def setUp(self):
        """Set up test data and small model config"""
        # Use small config for fast testing
        self.test_config = ModelConfig()
        self.test_config.vocab_size = 100
        self.test_config.d_model = 64
        self.test_config.n_heads = 4
        self.test_config.n_layers = 2
        self.test_config.d_ff = 128
        self.test_config.max_seq_len = 16
        self.test_config.batch_size = 4

        # Test data
        self.batch_size = 2
        self.seq_len = 8
        self.vocab_size = 100

        # Sample input IDs
        self.input_ids = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len))

        # Device for testing (prefer CPU for consistency)
        self.device = torch.device('cpu')

    def test_config_creation(self):
        """Test model configuration"""
        config = ModelConfig()

        # Check default values exist
        required_attrs = [
            'vocab_size', 'd_model', 'n_heads', 'n_layers', 'd_ff',
            'max_seq_len', 'dropout', 'learning_rate', 'batch_size',
            'pad_token', 'unk_token', 'start_token', 'end_token'
        ]

        for attr in required_attrs:
            self.assertTrue(hasattr(config, attr), f"Missing config attribute: {attr}")

        # Check reasonable default values
        self.assertGreater(config.vocab_size, 0)
        self.assertGreater(config.d_model, 0)
        self.assertGreater(config.n_heads, 0)
        self.assertGreater(config.n_layers, 0)
        self.assertEqual(config.d_model % config.n_heads, 0)  # d_model divisible by n_heads

    def test_default_config(self):
        """Test default configuration object"""
        self.assertIsInstance(DEFAULT_CONFIG, ModelConfig)

        # Check specific default values - check what the actual defaults are
        self.assertGreater(DEFAULT_CONFIG.vocab_size, 0)  # Should be positive
        self.assertEqual(DEFAULT_CONFIG.d_model, 512)
        self.assertEqual(DEFAULT_CONFIG.n_heads, 4)
        self.assertEqual(DEFAULT_CONFIG.n_layers, 3)

        # Print actual values for debugging
        print(f"Actual DEFAULT_CONFIG.vocab_size: {DEFAULT_CONFIG.vocab_size}")

    def test_token_embedding(self):
        """Test token embedding layer"""
        vocab_size = 100
        d_model = 64

        embedding = TokenEmbedding(vocab_size, d_model)

        # Test forward pass
        input_ids = torch.randint(0, vocab_size, (2, 8))
        output = embedding(input_ids)

        # Check output shape
        expected_shape = (2, 8, d_model)
        self.assertEqual(output.shape, expected_shape)

        # Check scaling (should be multiplied by sqrt(d_model))
        expected_scale = torch.sqrt(torch.tensor(d_model, dtype=torch.float32))

        # Test that output is scaled correctly
        raw_embedding = embedding.embedding(input_ids)
        expected_output = raw_embedding * expected_scale
        torch.testing.assert_close(output, expected_output)

    def test_positional_embedding(self):
        """Test positional embedding layer"""
        d_model = 64
        max_len = 100

        pos_emb = PositionalEmbedding(d_model, max_len)

        # Test forward pass
        seq_len = 10
        x = torch.randn(2, seq_len, d_model)
        output = pos_emb(x)

        # Check output shape (should be same as input)
        self.assertEqual(output.shape, x.shape)

        # Check that positional encoding is added
        pos_encoding = pos_emb.pe[:, :seq_len]
        expected_output = x + pos_encoding
        torch.testing.assert_close(output, expected_output)

    def test_embeddings_combined(self):
        """Test combined embeddings (token + positional)"""
        vocab_size = 100
        d_model = 64
        max_len = 50

        embeddings = Embeddings(vocab_size, d_model, max_len)

        # Test forward pass
        input_ids = torch.randint(0, vocab_size, (2, 8))
        output = embeddings(input_ids)

        # Check output shape
        expected_shape = (2, 8, d_model)
        self.assertEqual(output.shape, expected_shape)

        # Check that dropout is applied (output should be different on multiple calls)
        embeddings.train()  # Set to training mode for dropout
        output1 = embeddings(input_ids)
        output2 = embeddings(input_ids)

        # With dropout, outputs should be different (with high probability)
        self.assertFalse(torch.allclose(output1, output2))

    def test_causal_mask_creation(self):
        """Test causal mask creation"""
        seq_len = 5
        mask = create_causal_mask(seq_len)

        # Check shape
        expected_shape = (1, 1, seq_len, seq_len)
        self.assertEqual(mask.shape, expected_shape)

        # Check that it's lower triangular (causal)
        mask_2d = mask.squeeze()

        # Upper triangle should be 0, lower triangle should be 1
        for i in range(seq_len):
            for j in range(seq_len):
                if j <= i:
                    self.assertEqual(mask_2d[i, j].item(), 1)
                else:
                    self.assertEqual(mask_2d[i, j].item(), 0)

    def test_multi_head_attention(self):
        """Test multi-head attention mechanism"""
        d_model = 64
        n_heads = 4
        seq_len = 8
        batch_size = 2

        attention = MultiHeadAttention(d_model, n_heads)

        # Test input
        x = torch.randn(batch_size, seq_len, d_model)
        mask = create_causal_mask(seq_len)

        # Forward pass
        output = attention(x, x, x, mask)

        # Check output shape
        expected_shape = (batch_size, seq_len, d_model)
        self.assertEqual(output.shape, expected_shape)

        # Test without mask
        output_no_mask = attention(x, x, x)
        self.assertEqual(output_no_mask.shape, expected_shape)

    def test_feed_forward(self):
        """Test feed-forward network"""
        d_model = 64
        d_ff = 128
        seq_len = 8
        batch_size = 2

        ff = FeedForward(d_model, d_ff)

        # Test input
        x = torch.randn(batch_size, seq_len, d_model)

        # Forward pass
        output = ff(x)

        # Check output shape
        expected_shape = (batch_size, seq_len, d_model)
        self.assertEqual(output.shape, expected_shape)

    def test_transformer_block(self):
        """Test single transformer block"""
        d_model = 64
        n_heads = 4
        d_ff = 128
        seq_len = 8
        batch_size = 2

        block = TransformerBlock(d_model, n_heads, d_ff)

        # Test input
        x = torch.randn(batch_size, seq_len, d_model)
        mask = create_causal_mask(seq_len)

        # Forward pass
        output = block(x, mask)

        # Check output shape
        expected_shape = (batch_size, seq_len, d_model)
        self.assertEqual(output.shape, expected_shape)

    def test_transformer_decoder(self):
        """Test transformer decoder (multiple blocks)"""
        n_layers = 3
        d_model = 64
        n_heads = 4
        d_ff = 128
        seq_len = 8
        batch_size = 2

        decoder = TransformerDecoder(n_layers, d_model, n_heads, d_ff)

        # Test input
        x = torch.randn(batch_size, seq_len, d_model)
        mask = create_causal_mask(seq_len)

        # Forward pass
        output = decoder(x, mask)

        # Check output shape
        expected_shape = (batch_size, seq_len, d_model)
        self.assertEqual(output.shape, expected_shape)

    def test_simple_llm_creation(self):
        """Test SimpleLLM model creation"""
        model = SimpleLLM(self.test_config)

        # Check that model has required components
        self.assertTrue(hasattr(model, 'embeddings'))
        self.assertTrue(hasattr(model, 'decoder'))
        self.assertTrue(hasattr(model, 'norm_f'))

        # Check model config is stored
        self.assertEqual(model.config, self.test_config)

    def test_simple_llm_forward_pass(self):
        """Test SimpleLLM forward pass"""
        model = SimpleLLM(self.test_config)
        model.eval()  # Set to eval mode

        # Test input
        input_ids = torch.randint(0, self.test_config.vocab_size, (self.batch_size, self.seq_len))

        # Forward pass
        with torch.no_grad():
            logits = model(input_ids)

        # Check output shape
        expected_shape = (self.batch_size, self.seq_len, self.test_config.vocab_size)
        self.assertEqual(logits.shape, expected_shape)

    def test_model_parameter_counting(self):
        """Test parameter counting"""
        model = SimpleLLM(self.test_config)

        param_count = model.count_parameters()

        # Should be a positive integer
        self.assertIsInstance(param_count, int)
        self.assertGreater(param_count, 0)

        # Verify by manual counting
        manual_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
        self.assertEqual(param_count, manual_count)

    def test_create_model_factory(self):
        """Test model factory function"""
        vocab_size = 500
        model = create_model(vocab_size=vocab_size)

        # Check that vocab size is set correctly
        self.assertEqual(model.config.vocab_size, vocab_size)

        # Test without vocab size
        model_default = create_model()
        self.assertEqual(model_default.config.vocab_size, DEFAULT_CONFIG.vocab_size)

    def test_model_generation(self):
        """Test model text generation capability"""
        model = SimpleLLM(self.test_config)
        model.eval()

        # Test input
        input_ids = torch.randint(0, self.test_config.vocab_size, (1, 3))

        # Generate
        with torch.no_grad():
            generated = model.generate(input_ids, max_length=2, temperature=1.0)

        # Check that output is longer than input
        self.assertGreater(generated.shape[1], input_ids.shape[1])

        # Check that output contains original input
        torch.testing.assert_close(generated[:, :input_ids.shape[1]], input_ids)

    def test_tied_embeddings(self):
        """Test tied embeddings (output projection uses input embeddings)"""
        model = SimpleLLM(self.test_config)

        # Make sure that the tie_embeddings is set correctly
        self.assertTrue(model.tie_embeddings)

        # Test that model doesn't make other output projection
        self.assertFalse(hasattr(model, 'output_projection'))

    def test_model_initialization(self):
        """Test that model weights are initialized"""
        model = SimpleLLM(self.test_config)

        # Check the weights not all zeros
        total_zero_params = 0
        total_params = 0

        for param in model.parameters():
            total_params += param.numel()
            total_zero_params += (param == 0).sum().item()

        # Should have some non-zero parameters
        zero_ratio = total_zero_params / total_params
        self.assertLess(zero_ratio, 0.9)  # Less than 90% zeros

    def test_model_modes(self):
        """Test model training/eval modes"""
        model = SimpleLLM(self.test_config)

        # Test training mode
        model.train()
        self.assertTrue(model.training)

        # Test eval mode
        model.eval()
        self.assertFalse(model.training)

    def test_model_device_compatibility(self):
        """Test model device handling"""
        model = SimpleLLM(self.test_config)

        # Test CPU
        model = model.to('cpu')
        input_ids = torch.randint(0, self.test_config.vocab_size, (1, 4))

        with torch.no_grad():
            output = model(input_ids)

        self.assertEqual(output.device.type, 'cpu')

    def test_model_serialization(self):
        """Test model saving and loading"""
        model = SimpleLLM(self.test_config)
        model.eval()  # Set to eval mode to disable dropout

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
            temp_path = f.name

        try:
            # Save model
            torch.save(model.state_dict(), temp_path)

            # Create new model and load weights
            new_model = SimpleLLM(self.test_config)
            new_model.load_state_dict(torch.load(temp_path, weights_only=True))
            new_model.eval()  # Set to eval mode to disable dropout

            # Test that models produce same output
            input_ids = torch.randint(0, self.test_config.vocab_size, (1, 4))

            # Deterministic behavior
            torch.manual_seed(42)
            with torch.no_grad():
                original_output = model(input_ids)

            torch.manual_seed(42)
            with torch.no_grad():
                loaded_output = new_model(input_ids)

            torch.testing.assert_close(original_output, loaded_output)

        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_attention_mask_effects(self):
        """Test that causal mask affects attention properly"""
        d_model = 64
        n_heads = 4
        seq_len = 5

        attention = MultiHeadAttention(d_model, n_heads)
        attention.eval()  # Disable dropout for consistent results

        x = torch.randn(1, seq_len, d_model)
        mask = create_causal_mask(seq_len)

        with torch.no_grad():
            output_with_mask = attention(x, x, x, mask)
            output_without_mask = attention(x, x, x, None)

        # Outputs should be different when mask is applied
        self.assertFalse(torch.allclose(output_with_mask, output_without_mask, atol=1e-5))

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test with minimum sequence length
        model = SimpleLLM(self.test_config)
        model.eval()

        # Single token input
        input_ids = torch.randint(0, self.test_config.vocab_size, (1, 1))

        with torch.no_grad():
            output = model(input_ids)

        expected_shape = (1, 1, self.test_config.vocab_size)
        self.assertEqual(output.shape, expected_shape)

    def test_module_version(self):
        """Test module version"""
        version = get_version()
        self.assertIsInstance(version, str)
        self.assertTrue(len(version) > 0)

    def test_config_d_ff_calculation(self):
        """Test that d_ff is calculated correctly"""
        config = ModelConfig()

        # d_ff should be approximately 2.7 * d_model for SwiGLU
        expected_d_ff = int(config.d_model * 2.7)
        self.assertEqual(config.d_ff, expected_d_ff)

    def test_model_with_different_configs(self):
        """Test model with various configurations"""
        configs = [
            {'vocab_size': 50, 'd_model': 32, 'n_heads': 2, 'n_layers': 1},
            {'vocab_size': 200, 'd_model': 128, 'n_heads': 8, 'n_layers': 4},
        ]

        for config_dict in configs:
            config = ModelConfig()
            for key, value in config_dict.items():
                setattr(config, key, value)

            # Make sure that the d_model is divisible by n_heads
            if config.d_model % config.n_heads != 0:
                config.d_model = (config.d_model // config.n_heads) * config.n_heads

            model = SimpleLLM(config)

            # Test forward pass
            input_ids = torch.randint(0, config.vocab_size, (1, 3))

            with torch.no_grad():
                output = model(input_ids)

            expected_shape = (1, 3, config.vocab_size)
            self.assertEqual(output.shape, expected_shape)

    def test_gradient_flow(self):
        """Test that gradients flow through the model"""
        model = SimpleLLM(self.test_config)
        model.train()

        input_ids = torch.randint(0, self.test_config.vocab_size, (1, 4))
        target_ids = torch.randint(0, self.test_config.vocab_size, (1, 4))

        # Forward pass
        logits = model(input_ids)

        # Compute loss
        loss_fn = nn.CrossEntropyLoss()
        loss = loss_fn(logits.reshape(-1, logits.size(-1)), target_ids.reshape(-1))

        # Backward pass
        loss.backward()

        # Check that the gradients exist
        grad_exists = False
        for param in model.parameters():
            if param.grad is not None and param.grad.abs().sum() > 0:
                grad_exists = True
                break

        self.assertTrue(grad_exists, "No gradients found in model parameters")


if __name__ == "__main__":
    unittest.main()
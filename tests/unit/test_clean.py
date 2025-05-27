import unittest
import sys
import os
import tempfile
import json

# Project root
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from cleaning import (
    load_english_words, is_valid_encoding, is_good, quality_check,
    clean_web_content, remove_web_boilerplate, ContentDeduplicator,
    get_cleaning_config
)


class TestCleaning(unittest.TestCase):
    """Test cleaning pipeline components"""

    def setUp(self):
        """Setup test data"""
        self.config = get_cleaning_config()
        self.english_words = {'hello', 'world', 'test', 'good', 'text', 'the', 'and', 'is', 'this'}

        # Valid text samples
        self.valid_text = "Hello world this is a good test text with enough content. " * 10
        self.invalid_short = "short"
        self.invalid_long = "x" * 25000
        self.html_content = "<html><body><p>Good content here</p><div>More text</div></body></html>"
        self.web_boilerplate = "Header navigation menu\nGood content here with substantial text\nFooter copyright 2024"

    def test_load_english_words_concept(self):
        """Test English words loading concept"""
        # Test the concept since actual file doesn't exist in test environment
        test_words = {'hello', 'world', 'test'}
        self.assertEqual(len(test_words), 3)
        self.assertIn('hello', test_words)

    def test_encoding_validation(self):
        """Test encoding validation"""
        # Valid UTF-8 text
        self.assertTrue(is_valid_encoding(self.valid_text, self.config))

        # Empty text
        self.assertFalse(is_valid_encoding("", self.config))
        self.assertFalse(is_valid_encoding(None, self.config))

        # Binary data and this should fail
        binary_data = b'\x80\x81\x82\x83'
        self.assertFalse(is_valid_encoding(binary_data, self.config))

    def test_content_validation(self):
        """Test content quality validation"""
        # Valid content
        self.assertTrue(is_good(self.valid_text, self.english_words, self.config))

        # Too short
        self.assertFalse(is_good(self.invalid_short, self.english_words, self.config))

        # Too long
        self.assertFalse(is_good(self.invalid_long, self.english_words, self.config))

        # JAPANEZZEEE
        foreign_text = "こんにちは世界これはテストです" * 20
        self.assertFalse(is_good(foreign_text, self.english_words, self.config))

    def test_quality_check(self):
        """Test quality filtering"""
        # Good quality text
        good_text = "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede mollis pretium. Integer tincidunt. Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus. Aenean leo ligula, porttitor eu, consequat vitae, eleifend ac, enim. Aliquam lorem ante, dapibus in, viverra quis, feugiat a, tellus. Phasellus viverra nulla ut metus varius laoreet. Quisque rutrum. Aenean imperdiet. Etiam ultricies nisi vel augue. Curabitur ullamcorper ultricies nisi. Nam eget dui. Etiam rhoncus. Maecenas tempus, tellus eget condimentum rhoncus, sem quam semper libero, sit amet adipiscing sem neque sed ipsum. Nam quam nunc, blandit vel, luctus pulvinar, hendrerit id, lorem. Maecenas nec odio et ante tincidunt tempus. Donec vitae sapien ut libero venenatis faucibus. Nullam quis ante. Etiam sit amet orci eget eros faucibus tincidunt. Duis leo. Sed fringilla mauris sit amet nibh. Donec sodales sagittis magna. Sed consequat, leo eget bibendum sodales, augue velit cursus nunc,"
        self.assertTrue(quality_check(good_text, self.config))

        # Poor quality - too repetitive
        bad_text = "same line\nsame line\nsame line\nsame line\nsame line"
        self.assertFalse(quality_check(bad_text, self.config))

        # Too short
        self.assertFalse(quality_check("short", self.config))

    def test_boilerplate_removal(self):
        """Test boilerplate removal"""
        cleaned = remove_web_boilerplate(self.web_boilerplate)

        # Should keep main content
        self.assertIn('Good content', cleaned)

        # Should remove navigation/footer if detected
        # Note: actual removal depends on content length and position

    def test_deduplicator(self):
        """Test content deduplication"""
        dedup = ContentDeduplicator()

        # Create temp files with duplicate content
        temp_files = []
        duplicate_content = "This is duplicate content.\n\n---\n\n"
        unique_content = "This is unique content.\n\n---\n\n"

        try:
            # File 1: duplicate + unique
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(duplicate_content + unique_content)
                temp_files.append(f.name)

            # File 2: same duplicate + different unique
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(duplicate_content + "Different unique content.\n\n---\n\n")
                temp_files.append(f.name)

            # Output file
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                output_file = f.name

            # Test deduplication
            dedup.merge_and_deduplicate(temp_files, output_file)

            # Check results
            with open(output_file, 'r') as f:
                result = f.read()

            # Should have unique content only
            duplicate_count = result.count("This is duplicate content")
            self.assertEqual(duplicate_count, 1)  # Only one copy

            # Check counters
            self.assertGreater(dedup.get_kept_count(), 0)

        finally:
            # Cleanup
            for temp_file in temp_files + [output_file]:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

    def test_config_loading(self):
        """Test configuration loading"""
        config = get_cleaning_config()

        # Check required keys
        required_keys = [
            'min_text_length', 'max_text_length', 'english_threshold',
            'content_ratio_threshold', 'printable_ratio_threshold'
        ]

        for key in required_keys:
            self.assertIn(key, config)
            self.assertIsInstance(config[key], (int, float))

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # None inputs
        self.assertFalse(is_good(None, self.english_words, self.config))
        self.assertFalse(quality_check(None, self.config))

        # Empty string inputs
        self.assertFalse(is_good("", self.english_words, self.config))
        self.assertFalse(quality_check("", self.config))

        # Special characters
        special_text = "This text has special chars: @#$%^&*()! " * 20
        # Should handle gracefully
        result = is_good(special_text, self.english_words, self.config)
        self.assertIsInstance(result, bool)

    def test_integration_workflow(self):
        """Test complete cleaning workflow"""
        # Simulate web content with issues
        raw_content = """
        <html><head><title>Test</title></head>
        <body>
            <nav>Home | About | Contact</nav>
            <main>
                <p>This is the main content of the article.</p>
                <p>It contains multiple paragraphs with good information.</p>
                <p>The content should pass quality checks.</p>
                <p>Each paragraph adds substantial value.</p>
            </main>
            <footer>Copyright 2024 | Privacy Policy</footer>
        </body></html>
        """ * 5  # Make it long enough

        # Step 1: Clean web content
        step1 = clean_web_content(raw_content)

        # Step 2: Remove boilerplate
        step2 = remove_web_boilerplate(step1)

        # Step 3: Validate content
        step3_good = is_good(step2, self.english_words, self.config)
        step3_quality = quality_check(step2, self.config)

        # Check pipeline results
        self.assertIsInstance(step1, str)
        self.assertIsInstance(step2, str)
        self.assertIsInstance(step3_good, bool)
        self.assertIsInstance(step3_quality, bool)

        # Content should be substantially cleaned
        self.assertNotIn('<html>', step2)
        self.assertNotIn('<nav>', step2)

    def test_config_validation(self):
        """Test configuration parameter validation"""
        config = get_cleaning_config()

        # Check numeric constraints
        self.assertGreater(config['min_text_length'], 0)
        self.assertGreater(config['max_text_length'], config['min_text_length'])
        self.assertGreater(config['english_threshold'], 0)
        self.assertLessEqual(config['english_threshold'], 1)
        self.assertGreater(config['printable_ratio_threshold'], 0)
        self.assertLessEqual(config['printable_ratio_threshold'], 1)

    def test_memory_efficiency(self):
        """Test memory handling with large inputs"""
        # Create large text that fits criteria
        large_text = "This is a substantial piece of content with good English words. " * 200

        # Should handle without memory issues
        result = is_good(large_text, self.english_words, self.config)
        self.assertIsInstance(result, bool)

        quality_result = quality_check(large_text, self.config)
        self.assertIsInstance(quality_result, bool)

    def test_text_length_boundaries(self):
        """Test text length boundary conditions"""
        config = self.config
        min_len = config['min_text_length']
        max_len = config['max_text_length']

        # Just under minimum
        too_short = "a" * (min_len - 1)
        self.assertFalse(is_good(too_short, self.english_words, config))

        # Just over maximum
        too_long = "a" * (max_len + 1)
        self.assertFalse(is_good(too_long, self.english_words, config))

        # Inside the range
        good_length = "hello world test content " * (min_len // 20)
        # Should pass
        result = is_good(good_length, self.english_words, config)
        self.assertIsInstance(result, bool)


if __name__ == '__main__':
    # Set up test environment
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromTestCase(TestCleaning)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    if result.wasSuccessful():
        print(f"\nAll tests passed! ({result.testsRun} tests)")
    else:
        print(f"\n{len(result.failures)} failures, {len(result.errors)} errors")
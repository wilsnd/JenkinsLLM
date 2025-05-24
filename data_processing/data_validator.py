import json
import os


class DataValidator:
    """Data validation"""

    def __init__(self):
        self.errors = []

    def validate_file(self, filepath):
        """Check if file exists and is valid JSON"""

        if not os.path.exists(filepath):
            self.errors.append(f"File not found: {filepath}")
            return False

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return True
        except:
            self.errors.append(f"Invalid JSON: {filepath}")
            return False

    def validate_vocab(self, vocab_file):
        """Check vocabulary file"""

        if not self.validate_file(vocab_file):
            return False

        with open(vocab_file, 'r') as f:
            vocab = json.load(f)

        # Check required tokens
        required = ['<PAD>', '<UNK>', '<START>', '<END>']
        for token in required:
            if token not in vocab:
                self.errors.append(f"Missing token: {token}")
                return False

        print(f"Vocab size: {len(vocab)}")
        return True

    def validate_training_data(self, data_file):
        """Check training data"""

        if not self.validate_file(data_file):
            return False

        with open(data_file, 'r') as f:
            data = json.load(f)

        if not isinstance(data, list):
            self.errors.append("Data must be a list")
            return False

        if len(data) == 0:
            self.errors.append("Empty dataset")
            return False

        print(f"Dataset size: {len(data)}")
        return True

    def get_errors(self):
        """Return validation errors"""
        return self.errors

    def is_valid(self):
        """Check if no errors"""
        return len(self.errors) == 0


def validate_all():
    """Validate all data files"""

    validator = DataValidator()

    # Check files
    files_to_check = [
        ".processed_data/vocabulary.json",
        ".processed_data/training_data.json",
        ".processed_data/train.json",
        ".processed_data/val.json",
        ".processed_data/test.json"
    ]

    for file in files_to_check:
        validator.validate_file(file)

    # Specific validations
    validator.validate_vocab(".processed_data/vocabulary.json")
    validator.validate_training_data(".processed_data/training_data.json")

    if validator.is_valid():
        print("All validations passed!")
        return True
    else:
        print("Validation errors:")
        for error in validator.get_errors():
            print(f"  - {error}")
        return False


if __name__ == "__main__":
    validate_all()
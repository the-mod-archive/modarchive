from django.test import TestCase

from modarchive.hashers import LegacyModArchivePasswordHasher

class LegacyModArchivePasswordHasherTests(TestCase):
    algorithm = 'hmac'
    hash_without_salt = 'e53ae584fb2ac17712785143b7bd1279'
    salt = 'dfa187ec'
    cleartext_password = 'password'
    hash = f'{ hash_without_salt }{ salt }'
    encoded = f'{ algorithm }${ hash }'

    def test_decode_returns_correct_object(self):
        # Arrange
        legacy_hasher = LegacyModArchivePasswordHasher()

        # Act
        decoded = legacy_hasher.decode(self.encoded)

        # Assert
        self.assertEqual(self.algorithm, decoded['algorithm'], "Algorithm was not hmac")
        self.assertEqual(self.hash, decoded['hash'], "Hash was not expected value")
        self.assertEqual(self.salt, decoded['salt'], "Salt was not expected value")

    def test_encodes_old_password_correctly(self):
        # Arrange
        legacy_hasher = LegacyModArchivePasswordHasher()
        
        # Act
        result = legacy_hasher.encode(self.cleartext_password, self.salt)
        
        # Assert
        self.assertEqual(self.hash, result, "Resulted legacy encoding did not match the expected legacy encoding")

    def test_verify_returns_true_for_correct_password(self):
        # Arrange
        legacy_hasher = LegacyModArchivePasswordHasher()

        # Act and Assert
        self.assertTrue(legacy_hasher.verify(self.cleartext_password, self.encoded), "Expected password to pass validation but it failed")

    def test_verify_returns_false_for_incorrect_password(self):
        # Arrange
        legacy_hasher = LegacyModArchivePasswordHasher()

        # Act and Assert
        self.assertFalse(legacy_hasher.verify('incorrect password', self.encoded), "Expected password to fail validation but it passed")
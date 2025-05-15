import hmac

from typing import Any
from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.crypto import constant_time_compare

class LegacyModArchivePasswordHasher(BasePasswordHasher):
    algorithm = 'hmac'

    def decode(self, encoded):
        algorithm, encoded_2 = encoded.split('$')
        assert algorithm == self.algorithm
        return {
            'algorithm': algorithm,
            'hash': encoded_2,
            'salt': encoded_2[32:],
        }

    def encode(self, password: str, salt: str) -> Any:
        return hmac.HMAC(salt.encode('utf-8'), password.encode('utf-8'), 'md5').hexdigest() + salt

    def verify(self, password: str, encoded: str) -> bool:
        decoded = self.decode(encoded)
        encoded_2 = self.encode(password, decoded['salt'])

        return constant_time_compare(decoded['hash'], encoded_2)

    def safe_summary(self, encoded: str) -> dict:
        decoded = self.decode(encoded)
        return {
            ('Algorithm'): self.algorithm,
            ('Hash'): decoded['hash'][:6] + '...' + decoded['hash'][-6:],
            ('Salt'): decoded['salt'][:6] + '...' + decoded['salt'][-6:],
        }
"""Django database model fields."""

try:
    import encrypted_fields
except ImportError:
    pass
else:
    import json

    class TypeSafeEncryptedJSONField(encrypted_fields.EncryptedJSONField):
        """A django-fernet-encrypted-fields's EncryptedJSONField that keep data type safe.

        The current implementation of EncryptedJSONField() cast everything with `str()` so
        after decryption we get `'None'` instead of `None`, `'123'` instead of 123, etc.
        """

        def _encrypt_values(self, value):
            if isinstance(value, dict):
                return {key: self._encrypt_values(data) for key, data in value.items()}
            if isinstance(value, list):
                return [self._encrypt_values(data) for data in value]
            value = json.dumps(value, cls=self.encoder)
            return self.f.encrypt(bytes(value, "utf-8")).decode("utf-8")

        def _decrypt_values(self, value):
            if value is None:
                return value
            if isinstance(value, dict):
                return {key: self._decrypt_values(data) for key, data in value.items()}
            if isinstance(value, list):
                return [self._decrypt_values(data) for data in value]
            value = self.f.decrypt(bytes(value, "utf-8")).decode("utf-8")
            return json.loads(value, cls=self.decoder)

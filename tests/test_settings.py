import unittest

from services.settings import safe_secret_mapping


class SettingsTests(unittest.TestCase):
    def test_missing_streamlit_secrets_becomes_an_empty_mapping(self):
        def missing_secrets():
            raise RuntimeError("No secrets found")

        self.assertEqual({}, safe_secret_mapping(missing_secrets))


if __name__ == "__main__":
    unittest.main()

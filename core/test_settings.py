import os
import subprocess
import sys

from django.test import SimpleTestCase


class SecretKeySettingsTests(SimpleTestCase):
    def run_settings(self, debug, secret, code):
        environment = os.environ.copy()
        environment['DJANGO_DEBUG'] = debug
        environment.pop('DJANGO_SECRET_KEY', None)
        if secret is not None:
            environment['DJANGO_SECRET_KEY'] = secret
        return subprocess.run(
            [sys.executable, '-c', code], env=environment,
            capture_output=True, text=True,
        )

    def test_production_requires_secret(self):
        result = self.run_settings('False', None, 'import config.settings')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('RuntimeError', result.stderr)

    def test_production_uses_environment_secret(self):
        result = self.run_settings(
            'False', 'test-only-key-not-used-by-the-application',
            'from config import settings; '
            'assert settings.SECRET_KEY == "test-only-key-not-used-by-the-application"',
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_development_creates_temporary_random_secret(self):
        result = self.run_settings(
            'True', None,
            'import importlib; from config import settings; '
            'first = settings.SECRET_KEY; '
            'assert len(first) >= 50; '
            'importlib.reload(settings); '
            'assert settings.SECRET_KEY != first',
        )
        self.assertEqual(result.returncode, 0, result.stderr)

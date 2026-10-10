import unittest
from pathlib import Path
from nirupresence import __version__

class ReleaseTests(unittest.TestCase):
    def test_version_consistency(self):
        root = Path(__file__).resolve().parents[1]
        self.assertIn(__version__, (root/'README.md').read_text())
        self.assertIn('Installed NIRUPRESENCE '+__version__, (root/'install.sh').read_text())

    def test_no_private_path_or_secret_file(self):
        root = Path(__file__).resolve().parents[1]
        self.assertFalse((root/'nirupresence-config.json').exists())
        for path in root.rglob('*'):
            if path.is_file() and path.suffix in ('.py','.md','.sh'):
                text=path.read_text()
                self.assertNotIn('/home/'+'niru/',text)
                self.assertNotIn('Projects-Dev/'+'nirupresence-debian-void',text)

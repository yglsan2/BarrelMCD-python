import pytest
import sys
from PyQt5.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    """Crée une instance unique de QApplication pour tous les tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app 
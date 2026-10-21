"""Launch NamazFlow (Windows 10/11)."""
import sys
from PySide6.QtWidgets import QApplication
from namazflow.ui import NamazWidget


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NamazFlow")
    app.setOrganizationName("NamazFlow")
    app.setQuitOnLastWindowClosed(False)
    widget = NamazWidget()
    widget.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

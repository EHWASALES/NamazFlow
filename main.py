"""Launch NamazFlow (Windows 10/11)."""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLockFile, QStandardPaths, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from namazflow.ui import NamazWidget


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NamazFlow")
    app.setOrganizationName("NamazFlow")
    app.setQuitOnLastWindowClosed(False)
    if "--smoke-test" in sys.argv:
        # Exercise packaged Qt imports and both windows without network or user writes.
        class SmokeWidget(NamazWidget):
            def refresh(self):
                pass

            def load_quote(self):
                pass

        widget = SmokeWidget()
        widget._demo = True
        widget.open_panel()
        QTimer.singleShot(1500, widget.quit_app)
        return app.exec()
    # A second launch restores the existing orb instead of creating duplicates.
    server_name = "NamazFlow-desktop-v02"
    socket = QLocalSocket()
    socket.connectToServer(server_name)
    if socket.waitForConnected(400):
        socket.write(b"show")
        socket.waitForBytesWritten(400)
        return 0
    lock = QLockFile(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.TempLocation)
        + "/NamazFlow-v02.lock"
    )
    if not lock.tryLock(100):
        return 0
    QLocalServer.removeServer(server_name)
    server = QLocalServer()
    server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
    if not server.listen(server_name):
        return 1
    widget = NamazWidget()

    def restore():
        while server.hasPendingConnections():
            client = server.nextPendingConnection()
            client.disconnectFromServer()
            client.deleteLater()
        widget.show_flow()
        widget.open_panel()

    server.newConnection.connect(restore)
    widget.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

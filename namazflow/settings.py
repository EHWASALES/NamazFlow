"""Native settings dialog with explicit location presets."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QDialogButtonBox,
)
from .locations import LOCATIONS
from .prayers import METHODS


class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NamazFlow · Einstellungen")
        self.setMinimumWidth(440)
        self.setStyleSheet("""
          QDialog { background:#182127; color:#F6F1E9; }
          QLabel, QCheckBox { color:#EDE5D8; font:12px 'Segoe UI'; }
          QLineEdit, QComboBox { padding:9px; background:#26343B;
            border:1px solid #465157; border-radius:7px; color:white; }
          QPushButton { background:#267267; color:white; padding:10px;
            border-radius:7px; min-width:82px; }
        """)
        layout = QVBoxLayout(self)
        title = QLabel("Gebetszeiten & Erscheinungsbild")
        title.setStyleSheet(
            "font: 600 19px 'Segoe UI'; color:#DBAE67; margin-bottom:10px;"
        )
        layout.addWidget(title)
        form = QFormLayout()
        self.location = QComboBox()
        self.location.addItem("Eigene Stadt", "")
        for key, value in LOCATIONS.items():
            self.location.addItem(value["label"], key)
        self.location.setCurrentIndex(
            max(0, self.location.findData(config.get("location", "")))
        )
        form.addRow("Standort", self.location)
        self.city = QLineEdit(config["city"])
        self.country = QLineEdit(config["country"])
        self.time_source = QComboBox()
        self.time_source.addItem("DİTİB Deutschland / Diyanet-Kalender", "ditib")
        self.time_source.addItem("Eigene Berechnung über AlAdhan", "calculated")
        self.time_source.setCurrentIndex(
            max(0, self.time_source.findData(config["time_source"]))
        )
        self.method = QComboBox()
        for key, value in METHODS.items():
            self.method.addItem(value, key)
        self.method.setCurrentIndex(max(0, self.method.findData(config["method"])))
        self.school = QComboBox()
        self.school.addItem("Hanafi", 1)
        self.school.addItem("Shafi / Standard", 0)
        self.school.setCurrentIndex(max(0, self.school.findData(config["school"])))
        self.theme = QComboBox()
        for value, label in (
            ("midnight", "Mitternacht · Gold & Türkis"),
            ("emerald", "Smaragd"),
            ("sand", "Sand & Bronze"),
        ):
            self.theme.addItem(label, value)
        self.theme.setCurrentIndex(max(0, self.theme.findData(config["theme"])))
        self.symbol = QComboBox()
        for value, label in (
            ("crescent", "Halbmond"),
            ("mosque", "Moschee"),
            ("star", "Stern"),
            ("lantern", "Laterne"),
        ):
            self.symbol.addItem(label, value)
        self.symbol.setCurrentIndex(max(0, self.symbol.findData(config["symbol"])))
        self.location.currentIndexChanged.connect(self._location_changed)
        self._location_changed()
        form.addRow("Eigene Stadt", self.city)
        form.addRow("Land (Englisch)", self.country)
        form.addRow("Zeitquelle", self.time_source)
        form.addRow("Berechnungsmethode", self.method)
        self.time_source.currentIndexChanged.connect(self._source_changed)
        self._source_changed()
        form.addRow("İkindi-Berechnung", self.school)
        form.addRow("Design", self.theme)
        form.addRow("Schwebendes Symbol", self.symbol)
        layout.addLayout(form)
        self.calligraphy = QCheckBox("Arabische Gebetsnamen mit goldenen Ornamenten")
        self.calligraphy.setChecked(config.get("calligraphy", True))
        self.calligraphy.setToolTip("Eigene Embleme für alle Gebete; im Kreis erscheint das nächste Gebet.")
        self.symbol.setDisabled(self.calligraphy.isChecked())
        self.calligraphy.toggled.connect(self.symbol.setDisabled)
        layout.addWidget(self.calligraphy)
        self.notifications = QCheckBox("Dezente Gebetsbenachrichtigungen")
        self.notifications.setChecked(config["notifications"])
        self.autostart = QCheckBox("Mit Windows starten")
        self.autostart.setChecked(config["autostart"])
        self.quote = QCheckBox("Koranverse und Hadithe anzeigen")
        self.quote.setChecked(config["quote"])
        layout.addWidget(self.notifications)
        layout.addWidget(self.autostart)
        layout.addWidget(self.quote)
        self.quote_source = QComboBox()
        self.quote_source.addItem("Koran und Hadithe im Wechsel", "mixed")
        self.quote_source.addItem("Nur Koran", "quran")
        self.quote_source.addItem("Nur Hadithe", "hadith")
        self.quote_source.setCurrentIndex(
            max(0, self.quote_source.findData(config.get("quote_source", "mixed")))
        )
        layout.addWidget(self.quote_source)
        self.animations = QCheckBox("Sanfte Animationen und Hover-Effekte")
        self.animations.setChecked(config.get("animations", True))
        layout.addWidget(self.animations)
        note = QLabel(
            "DİTİB: veröffentlichter Diyanet-Kalender. Für Niederhöchstadt wird Eschborn verwendet."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#B0B7BB; font-size:10px; margin:10px 0;")
        layout.addWidget(note)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _source_changed(self):
        calculated = self.time_source.currentData() == "calculated"
        self.method.setEnabled(calculated)
        self.school.setEnabled(calculated)

    def _location_changed(self):
        custom = not self.location.currentData()
        self.city.setEnabled(custom)
        self.country.setEnabled(custom)
        preset = LOCATIONS.get(self.location.currentData())
        if preset:
            self.city.setText(preset["city"])
            self.country.setText(preset["country"])

    def values(self) -> dict:
        return {
            "location": self.location.currentData(),
            "time_source": self.time_source.currentData(),
            "animations": self.animations.isChecked(),
            "calligraphy": self.calligraphy.isChecked(),
            "quote_source": self.quote_source.currentData(),
            "city": self.city.text().strip(),
            "country": self.country.text().strip(),
            "method": self.method.currentData(),
            "school": self.school.currentData(),
            "theme": self.theme.currentData(),
            "symbol": self.symbol.currentData(),
            "notifications": self.notifications.isChecked(),
            "autostart": self.autostart.isChecked(),
            "quote": self.quote.isChecked(),
        }

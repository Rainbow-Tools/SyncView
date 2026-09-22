"""Remember a UI preference separately from editable video projects."""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QLibraryInfo,
    QLocale,
    QObject,
    QSettings,
    QTranslator,
    Signal,
)

from videos_multi_view.i18n import LANGUAGES, language, set_language
from videos_multi_view.media.tools import resource_root


class LanguageManager(QObject):
    changed = Signal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        settings: QSettings | None = None,
        system_language: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings if settings is not None else QSettings("SyncView", "SyncView")
        self._qt_translator = QTranslator(self)
        preferred = QLocale.system().uiLanguages()
        default = system_language or (preferred[0] if preferred else "en")
        default = "ko" if default.lower().startswith("ko") else "en"
        saved = self.settings.value("ui/language", default)
        self.select(
            saved if isinstance(saved, str) and saved in LANGUAGES else default, persist=False
        )

    @property
    def current(self) -> str:
        return language()

    def select(self, code: str, persist: bool = True) -> None:
        set_language(code)
        app = QCoreApplication.instance()
        if app is not None:
            app.removeTranslator(self._qt_translator)
            if code == "ko":
                locations = [
                    resource_root() / "PySide6/translations",
                    Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)),
                ]
                for location in locations:
                    if self._qt_translator.load(str(location / "qtbase_ko.qm")):
                        app.installTranslator(self._qt_translator)
                        break
        if persist:
            self.settings.setValue("ui/language", code)
            self.settings.sync()
        self.changed.emit(code)

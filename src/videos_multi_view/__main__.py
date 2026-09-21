"""Application entry point for SyncView."""

import argparse
import os
import sys
from importlib.resources import files
from pathlib import Path

from PySide6.QtGui import QFont, QFontInfo, QIcon
from PySide6.QtWidgets import QApplication

from videos_multi_view.ui.main_window import MainWindow
from videos_multi_view.ui.theme import apply_theme


def main() -> None:
    parser = argparse.ArgumentParser(description="SyncView")
    parser.add_argument(
        "--software-decode", action="store_true", help="미리보기에 소프트웨어 디코더 사용"
    )
    parser.add_argument("--verify-project", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--verify-output", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.software_decode:
        os.environ["QT_FFMPEG_DECODING_HW_DEVICE_TYPES"] = ","
    app = QApplication(sys.argv)
    app.setApplicationName("SyncView")
    app.setOrganizationName("SyncView")

    font = QFont("Pretendard", 9)
    if "Pretendard" not in QFontInfo(font).family():
        font = QFont("Malgun Gothic", 9)
    app.setFont(font)

    icon_path = files("videos_multi_view").joinpath("assets/logo.png")
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))

    apply_theme(app)

    window = MainWindow()
    if args.verify_project:
        from videos_multi_view.application.diagnostics import verify_application

        verify_application(
            app, window, args.verify_project, args.verify_output or Path("artifacts")
        )
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

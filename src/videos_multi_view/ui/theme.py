from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

COLOR_BG_BASE = "#090D16"
COLOR_BG_PANEL = "#111927"
COLOR_BG_CARD = "#172338"
COLOR_BG_INPUT = "#0D1524"

COLOR_PRIMARY = "#2563EB"
COLOR_PRIMARY_HOVER = "#3B82F6"
COLOR_PRIMARY_PRESSED = "#1D4ED8"

COLOR_BORDER = "#1E293B"
COLOR_BORDER_FOCUS = "#3B82F6"

COLOR_TEXT_PRIMARY = "#F8FAFC"
COLOR_TEXT_MUTED = "#94A3B8"
COLOR_TEXT_ACCENT = "#60A5FA"

BLUE_STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {COLOR_BG_BASE};
    color: {COLOR_TEXT_PRIMARY};
}}

QWidget {{
    font-family: "Pretendard Variable", "Pretendard Medium",
        "Pretendard", "Malgun Gothic", sans-serif;
    color: {COLOR_TEXT_PRIMARY};
}}

QSplitter::handle {{
    background-color: {COLOR_BORDER};
    width: 2px;
}}

QSplitter::handle:hover {{
    background-color: {COLOR_PRIMARY};
}}

QGroupBox {{
    background-color: {COLOR_BG_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    margin-top: 8px;
    padding: 34px 12px 14px 12px;
    font-weight: 600;
    font-size: 13px;
}}

QGroupBox::title {{
    subcontrol-origin: padding;
    subcontrol-position: top left;
    left: 12px;
    top: 10px;
    color: {COLOR_TEXT_ACCENT};
    font-weight: 700;
    font-size: 13px;
    background-color: transparent;
    padding: 0;
}}

QPushButton {{
    background-color: {COLOR_BG_CARD};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {COLOR_PRIMARY};
    border-color: {COLOR_PRIMARY_HOVER};
}}

QPushButton:pressed {{
    background-color: {COLOR_PRIMARY_PRESSED};
}}

QPushButton:disabled {{
    background-color: {COLOR_BG_INPUT};
    color: #475569;
    border-color: #1E293B;
}}

QPushButton#primaryButton {{
    background-color: {COLOR_PRIMARY};
    border-color: {COLOR_PRIMARY_HOVER};
    font-weight: 600;
}}

QPushButton#primaryButton:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
}}

QPushButton#primaryButton:pressed {{
    background-color: {COLOR_PRIMARY_PRESSED};
}}

QLineEdit, QSpinBox {{
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}

QLineEdit:focus, QSpinBox:focus {{
    border: 1px solid {COLOR_BORDER_FOCUS};
}}

QComboBox {{
    combobox-popup: 0;
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}

QComboBox:focus {{
    border: 1px solid {COLOR_BORDER_FOCUS};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLOR_BG_PANEL};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    selection-background-color: {COLOR_PRIMARY};
    selection-color: #ffffff;
    padding: 4px;
    outline: 0px;
}}

QListWidget {{
    background-color: {COLOR_BG_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    outline: none;
    padding: 4px;
}}

QListWidget::item {{
    border-radius: 4px;
    padding: 6px 8px;
    margin-bottom: 3px;
    color: {COLOR_TEXT_PRIMARY};
}}

QListWidget::item:hover {{
    background-color: {COLOR_BG_CARD};
}}

QListWidget::item:selected {{
    background-color: {COLOR_PRIMARY};
    color: #ffffff;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background-color: {COLOR_BORDER};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background-color: {COLOR_PRIMARY};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    background-color: {COLOR_TEXT_PRIMARY};
    border: 2px solid {COLOR_PRIMARY};
}}

QSlider::handle:horizontal:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
    border-color: #ffffff;
}}

QProgressBar {{
    background-color: {COLOR_BG_INPUT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    text-align: center;
    font-size: 11px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
    height: 16px;
}}

QProgressBar::chunk {{
    background-color: {COLOR_PRIMARY};
    border-radius: 3px;
}}

QMenuBar {{
    background-color: {COLOR_BG_BASE};
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 2px 6px;
}}

QMenuBar::item {{
    padding: 4px 10px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {COLOR_BG_CARD};
}}

QMenu {{
    background-color: {COLOR_BG_PANEL};
    border: 1px solid {COLOR_BORDER};
    padding: 4px;
    border-radius: 6px;
}}

QMenu::item {{
    padding: 6px 20px 6px 12px;
    border-radius: 4px;
    font-size: 12px;
}}

QMenu::item:selected {{
    background-color: {COLOR_PRIMARY};
    color: #ffffff;
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLOR_BORDER};
    margin: 4px 8px;
}}

QStatusBar {{
    background-color: {COLOR_BG_BASE};
    border-top: 1px solid {COLOR_BORDER};
    font-size: 11px;
    color: {COLOR_TEXT_MUTED};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLOR_PRIMARY};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
}}

QScrollBar::handle:horizontal {{
    background: {COLOR_BORDER};
    border-radius: 4px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLOR_PRIMARY};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QToolTip {{
    background-color: {COLOR_BG_CARD};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}}

#viewHeader {{
    background-color: {COLOR_BG_BASE};
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 2px 6px;
}}

#toggleButton {{
    background-color: {COLOR_BG_PANEL};
    color: {COLOR_TEXT_MUTED};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 500;
}}

#toggleButton:hover {{
    background-color: {COLOR_BG_CARD};
    color: {COLOR_TEXT_PRIMARY};
    border-color: {COLOR_PRIMARY};
}}

#toggleButton:checked {{
    background-color: {COLOR_PRIMARY};
    color: #ffffff;
    border-color: {COLOR_PRIMARY_HOVER};
}}

#viewStatusLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
    font-weight: 500;
}}
"""


def apply_theme(app: QApplication) -> None:
    """Apply the dark blue monochromatic stylesheet and palette."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLOR_BG_BASE))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLOR_TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLOR_BG_PANEL))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLOR_BG_CARD))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLOR_TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLOR_BG_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLOR_TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLOR_PRIMARY))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    # Select modern Pretendard Variable or Medium first to prevent TTF stroke-dropping
    families = QFontDatabase.families()
    preferred_font = (
        "Pretendard Variable"
        if "Pretendard Variable" in families
        else ("Pretendard Medium" if "Pretendard Medium" in families else "Pretendard")
    )
    app_font = QFont(preferred_font, 9)
    app_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(app_font)

    app.setPalette(palette)
    app.setStyleSheet(BLUE_STYLESHEET)

    # Disable OS fade/slide animations to prevent combo and menu flickering
    for effect_name in (
        "UI_AnimateCombo",
        "UI_AnimateMenu",
        "UI_FadeMenu",
        "UI_FadeTooltip",
        "UI_AnimateTooltip",
    ):
        if hasattr(Qt.UIEffect, effect_name):
            app.setEffectEnabled(getattr(Qt.UIEffect, effect_name), False)

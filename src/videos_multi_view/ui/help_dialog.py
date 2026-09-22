# ruff: noqa: E501
"""Modern help and documentation dialog for SyncView."""

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from videos_multi_view.ui.help_content import HELP_SECTIONS as HELP_SECTIONS
from videos_multi_view.ui.help_content import help_sections
from videos_multi_view.ui.translation import bind


class HelpDialog(QDialog):
    """Modern dark-themed help dialog with categorized documentation."""

    def __init__(self, initial_tab: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        bind(self, "SyncView 사용 설명서", setter="setWindowTitle")
        self.resize(860, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Topic list
        self.list_topics = QListWidget()
        self.list_topics.setFixedWidth(240)
        for title, _ in help_sections():
            self.list_topics.addItem(title)
        splitter.addWidget(self.list_topics)

        # Right: Content browser
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, stretch=1)

        # Bottom: Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_close = bind(QPushButton(), "닫기")
        self.btn_close.setFixedWidth(100)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        main_layout.addLayout(btn_layout)

        self.list_topics.currentRowChanged.connect(self._on_topic_changed)
        self.list_topics.setCurrentRow(initial_tab)

    def _on_topic_changed(self, index: int) -> None:
        if 0 <= index < len(help_sections()):
            _, content = help_sections()[index]
            html = f"""
            <html>
            <head>
            <style>
                body {{
                    font-family: 'Pretendard Variable', 'Pretendard Medium', 'Pretendard', 'Malgun Gothic', -apple-system, sans-serif;
                    color: #F8FAFC;
                    background-color: #111927;
                    line-height: 1.6;
                    padding: 8px;
                }}
                h2 {{ color: #60A5FA; margin-top: 0; border-bottom: 1px solid #1E293B; padding-bottom: 6px; }}
                h3 {{ color: #93C5FD; margin-top: 14px; margin-bottom: 6px; }}
                code {{
                    background-color: #172338;
                    color: #38BDF8;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: monospace;
                }}
                ul {{ padding-left: 20px; }}
                li {{ margin-bottom: 6px; }}
                table {{ border-color: #1E293B; font-size: 13px; }}
                th, td {{ padding: 8px; border-color: #1E293B; }}
            </style>
            </head>
            <body>
            {content}
            </body>
            </html>
            """
            self.browser.setHtml(html)

    def retranslate(self) -> None:
        index = self.list_topics.currentRow()
        with QSignalBlocker(self.list_topics):
            for row, (title, _) in enumerate(help_sections()):
                self.list_topics.item(row).setText(title)
        self._on_topic_changed(index)

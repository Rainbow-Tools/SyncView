# ruff: noqa: E501
"""Modern help and documentation dialog for SyncView."""

from PySide6.QtCore import Qt
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

HELP_SECTIONS = [
    (
        "1. 시작하기 및 영상 추가",
        """
        <h2>SyncView 시작하기</h2>
        <p><b>SyncView</b>는 여러 개의 로컬 동영상을 하나의 화면에 그리드로 배치하여
        동기 재생하고, 오프셋과 이름표(라벨)를 편집하여 하나의 <b>MP4 영상</b>으로 합성·내보내는 도구입니다.</p>

        <h3>영상 추가 방법</h3>
        <ul>
            <li><b>파일 메뉴 또는 드래그 앤 드롭:</b> 파일 탐색기에서 영상을 좌측 영상 목록 창으로 직접 드래그하여 놓거나, 하단의 <b>[+ 영상 추가]</b> 버튼을 클릭합니다.</li>
            <li><b>지원 형식:</b> MP4, MOV, MKV, AVI, WebM 등 FFmpeg/FFprobe가 지원하는 모든 표준 영상 포맷.</li>
            <li><b>다양한 해상도 및 FPS:</b> 서로 다른 해상도, 화면비, FPS를 가진 영상들도 원본 비율을 유지하며 자동으로 최적 배치됩니다.</li>
        </ul>
        """,
    ),
    (
        "2. 타임라인 및 영상 동기화",
        """
        <h2>공통 타임라인 및 동기화 (Sync)</h2>
        <p>모든 영상은 하단의 공통 타임라인을 기준으로 함께 재생되고 탐색됩니다.</p>

        <h3>시작 시점(오프셋) 맞추기</h3>
        <ul>
            <li><b>오프셋 조절:</b> 우측 <b>[영상 설정]</b> 패널에서 영상별 <code>오프셋(ms)</code>을 지정할 수 있습니다.</li>
            <li><b>양수 오프셋 (+ms):</b> 공통 타임라인 시작 후 지정한 시간만큼 늦게 재생이 시작됩니다. (시작 전에는 배경색 유지)</li>
            <li><b>음수 오프셋 (-ms):</b> 영상의 앞부분을 지정한 시간만큼 건너뛰고 시작합니다.</li>
            <li><b>시작점 지정 [M]:</b> 영상을 선택하고 <code>M</code> 키를 누르면 해당 영상의 원본 시작(0초)을 현재 공통 시각에 배치합니다. 소리나 장면을 자동 분석하는 기능은 아닙니다.</li>
        </ul>
        """,
    ),
    (
        "3. 그리드, 테두리, 이름표 설정",
        """
        <h2>그리드 및 디자인 설정</h2>
        <p>우측 상단의 <b>[그리드 설정]</b> 패널에서 합성 화면의 레이아웃과 디자인을 자유롭게 편집할 수 있습니다.</p>

        <h3>그리드 설정</h3>
        <ul>
            <li><b>해상도:</b> 최종 내보낼 캔버스의 너비 × 높이 (기본 1920×1080).</li>
            <li><b>열 수:</b> '자동' 또는 1~9개 열을 직접 지정할 수 있습니다.</li>
            <li><b>간격 및 여백:</b> 셀 사이의 간격(Gap)과 캔버스 외곽 여백(Margin)을 픽셀 단위로 설정합니다.</li>
            <li><b>배경색 및 테두리:</b> 캔버스 배경색과 셀 테두리(표시 여부, 두께, 색상)를 조절할 수 있습니다.</li>
        </ul>

        <h3>영상별 이름표 (Legend)</h3>
        <ul>
            <li><b>위치:</b> 좌측 상단, 우측 상단, 좌측 하단, 우측 하단 4개 위치 중 선택.</li>
            <li><b>글꼴:</b> <b>시스템에 설치된 모든 사용자 보유 폰트</b>(Pretendard, 나눔고딕, Roboto 등) 중 자유롭게 선택 가능합니다.</li>
            <li><b>크기 및 색상:</b> 글자 크기, 글자 색상, 배경 색상(반투명 지원).</li>
        </ul>
        """,
    ),
    (
        "4. 동적 매크로 이름표 문법",
        """
        <h2>이름표 동적 매크로 문법</h2>
        <p>이름표 텍스트에 특수 변수(매크로)를 입력하면, 영상 정보 및 현재 타임코드가 실시간으로 치환되어 화면에 표시됩니다.</p>

        <table border="1" cellpadding="6" style="border-collapse: collapse; width: 100%; border-color: #1E293B;">
            <tr style="background-color: #172338; color: #60A5FA;">
                <th>매크로 변수</th>
                <th>설명</th>
                <th>표시 예시</th>
            </tr>
            <tr>
                <td><code>{filename}</code></td>
                <td>확장자를 제외한 원본 파일명</td>
                <td><code>Front_Camera</code></td>
            </tr>
            <tr>
                <td><code>{timecode}</code></td>
                <td>해당 영상 기준 현재 재생 시각</td>
                <td><code>01:23.450</code></td>
            </tr>
            <tr>
                <td><code>{fps}</code></td>
                <td>영상의 초당 프레임 수</td>
                <td><code>30fps</code>, <code>60fps</code></td>
            </tr>
            <tr>
                <td><code>{resolution}</code></td>
                <td>영상의 원본 해상도 (너비x높이)</td>
                <td><code>1920x1080</code></td>
            </tr>
            <tr>
                <td><code>{offset}</code></td>
                <td>설정된 시작 오프셋 (ms)</td>
                <td><code>1500ms</code></td>
            </tr>
        </table>

        <h3>활용 예시</h3>
        <ul>
            <li><code>{filename} [{timecode}]</code> &rarr; <b>Front_Camera [00:12.300]</b></li>
            <li><code>{filename} ({resolution} @ {fps})</code> &rarr; <b>Front_Camera (1920x1080 @ 60fps)</b></li>
        </ul>
        """,
    ),
    (
        "5. 더블클릭 솔로 뷰 (Focus Zoom)",
        """
        <h2>솔로 뷰 (Focus Zoom)</h2>
        <p>여러 영상 중 특정 영상의 디테일을 크게 확인하고 싶을 때 사용합니다.</p>

        <ul>
            <li><b>확대:</b> 미리보기 캔버스에서 확인하고 싶은 <b>영상 셀을 마우스로 더블클릭</b>하면 해당 영상 하나만 캔버스 전체로 즉시 확대됩니다.</li>
            <li><b>복귀:</b> 솔로 뷰 상태에서 <b>다시 화면을 더블클릭</b>하면 원래의 멀티뷰 그리드 레이아웃으로 즉시 복귀합니다.</li>
        </ul>
        """,
    ),
    (
        "6. MP4 내보내기 및 GPU 가속",
        """
        <h2>MP4 내보내기 (Export)</h2>
        <p>편집한 멀티뷰 레이아웃과 오프셋, 테두리, 이름표를 그대로 반영하여 하나의 고화질 MP4 파일로 렌더링합니다.</p>

        <h3>내보내기 옵션</h3>
        <ul>
            <li><b>FPS:</b> 24, 30, 60fps 중 선택.</li>
            <li><b>인코더:</b>
                <ul>
                    <li><b>CPU (libx264):</b> 가장 표준적이고 호환성이 뛰어난 소프트웨어 인코더 (기본값).</li>
                    <li><b>NVIDIA GPU (h264_nvenc):</b> 호환 NVIDIA 그래픽카드와 드라이버가 필요하며, 처리 속도는 장비와 입력에 따라 달라집니다.</li>
                    <li><b>Intel GPU (h264_qsv):</b> Intel 내장/외장 그래픽의 QuickSync Video 가속 사용.</li>
                </ul>
            </li>
            <li><b>오디오:</b> 하단 타임라인에서 선택된 영상 1개의 오디오 트랙이 싱크에 맞추어 인코딩됩니다.</li>
        </ul>
        """,
    ),
    (
        "7. 키보드 단축키 일람",
        """
        <h2>단축키 일람</h2>

        <table border="1" cellpadding="6" style="border-collapse: collapse; width: 100%; border-color: #1E293B;">
            <tr style="background-color: #172338; color: #60A5FA;">
                <th>단축키</th>
                <th>동작</th>
            </tr>
            <tr>
                <td><code>Space</code></td>
                <td>재생 / 일시정지 토글</td>
            </tr>
            <tr>
                <td><code>Left / Right (← / →)</code></td>
                <td>100ms (약 3프레임) 단위 이전 / 이후 정밀 이동</td>
            </tr>
            <tr>
                <td><code>Shift + Left / Right</code></td>
                <td>1000ms (1초) 단위 이전 / 이후 이동</td>
            </tr>
            <tr>
                <td><code>Home</code></td>
                <td>타임라인 처음 (0ms)으로 즉시 이동</td>
            </tr>
            <tr>
                <td><code>M</code></td>
                <td>선택 영상의 원본 시작을 현재 공통 시각에 배치</td>
            </tr>
            <tr>
                <td><code>Delete</code></td>
                <td>현재 선택된 영상 목록에서 제거</td>
            </tr>
            <tr>
                <td><code>더블 클릭</code></td>
                <td>해당 영상 솔로 뷰 확대 / 그리드 복귀</td>
            </tr>
            <tr>
                <td><code>Ctrl + 1</code></td>
                <td>좌측 영상 목록 패널 접기 / 펼치기 토글</td>
            </tr>
            <tr>
                <td><code>Ctrl + 2</code></td>
                <td>우측 설정 패널 접기 / 펼치기 토글</td>
            </tr>
            <tr>
                <td><code>F11</code></td>
                <td>미리보기 최대화 (사이드바 동시 접기/펼치기)</td>
            </tr>
            <tr>
                <td><code>Ctrl + N</code></td>
                <td>새 프로젝트 생성</td>
            </tr>
            <tr>
                <td><code>Ctrl + O</code></td>
                <td>프로젝트 파일 열기</td>
            </tr>
            <tr>
                <td><code>Ctrl + S</code></td>
                <td>프로젝트 저장</td>
            </tr>
            <tr>
                <td><code>Ctrl + Shift + S</code></td>
                <td>다른 이름으로 프로젝트 저장</td>
            </tr>
            <tr>
                <td><code>F1</code></td>
                <td>사용 설명서 (도움말) 열기</td>
            </tr>
        </table>
        """,
    ),
    (
        "8. 오픈소스 라이선스 안내",
        """
        <h2>오픈소스 라이선스 고지 (Open Source Licenses)</h2>
        <p>SyncView 자체 코드와 문서는 MIT 라이선스입니다.
        외부 구성요소에는 각 라이선스가 별도로 적용됩니다.
        <a href="https://github.com/Rainbow-Tools/SyncView/blob/main/LICENSE">MIT 원문</a> ·
        <a href="https://github.com/Rainbow-Tools/SyncView/blob/main/THIRD_PARTY_NOTICES.md">외부 구성요소 고지</a></p>

        <table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border-color: #1E293B;">
            <tr style="background-color: #172338; color: #60A5FA;">
                <th>소프트웨어 / 리소스</th>
                <th>라이선스</th>
                <th>저작권자 / 웹사이트</th>
            </tr>
            <tr>
                <td><b>FFmpeg & FFprobe CLI</b></td>
                <td>GNU GPL v3.0 or later</td>
                <td>Copyright (c) 2000-2026 the FFmpeg developers<br><a href="https://ffmpeg.org" style="color: #60A5FA;">https://ffmpeg.org</a></td>
            </tr>
            <tr>
                <td><b>PySide6 (Qt for Python) / Qt 6</b></td>
                <td>GNU Lesser General Public License v3.0 (LGPLv3)</td>
                <td>Copyright (c) The Qt Company Ltd. and other contributors<br><a href="https://www.qt.io" style="color: #60A5FA;">https://www.qt.io</a></td>
            </tr>
            <tr>
                <td><b>Qt의 FFmpeg 라이브러리</b></td>
                <td>GNU LGPL v2.1 or later (검증 빌드 7.1.5)</td>
                <td>FFmpeg developers and contributors</td>
            </tr>
            <tr>
                <td><b>Python Runtime</b></td>
                <td>Python Software Foundation License (PSFL)</td>
                <td>Copyright (c) 2001-2026 Python Software Foundation<br><a href="https://www.python.org" style="color: #60A5FA;">https://www.python.org</a></td>
            </tr>
            <tr>
                <td><b>PyInstaller</b></td>
                <td>GPLv2-or-later + bootloader exception; runtime hooks: Apache-2.0</td>
                <td>PyInstaller Development Team and contributors</td>
            </tr>
        </table>

        <h3>외부 구성요소 안내</h3>
        <ul>
            <li><b>FFmpeg:</b> export용 GPL CLI와 미리보기용 LGPL 라이브러리는 다른 빌드입니다. 대응 소스 제공 등 각 라이선스의 재배포 조건을 따릅니다.</li>
            <li><b>PySide6 / Qt 6:</b> 사용하는 LGPL 모듈의 고지·소스 제공·재결합 조건을 따릅니다. 사용하지 않는 GPL 전용 Qt Virtual Keyboard는 빌드에서 제외합니다.</li>
            <li><b>글꼴:</b> Pretendard 등 사용자 PC에 설치된 글꼴을 사용하며 글꼴 파일 자체는 앱에 포함하지 않습니다.</li>
        </ul>

        <p style="color: #94A3B8; font-size: 11px; margin-top: 20px;">
        주요 라이선스 원문은 번들의 LICENSE와 licenses 폴더에 포함됩니다.
        배포 범위와 대응 소스 준비에 관한 검토는
        <a href="https://github.com/Rainbow-Tools/SyncView/blob/main/docs/LICENSING.md">라이선스 검토 문서</a>를 참고하세요.
        </p>
        """,
    ),
]


class HelpDialog(QDialog):
    """Modern dark-themed help dialog with categorized documentation."""

    def __init__(self, initial_tab: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SyncView 사용 설명서")
        self.resize(860, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Topic list
        self.list_topics = QListWidget()
        self.list_topics.setFixedWidth(240)
        for title, _ in HELP_SECTIONS:
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
        self.btn_close = QPushButton("닫기")
        self.btn_close.setFixedWidth(100)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        main_layout.addLayout(btn_layout)

        self.list_topics.currentRowChanged.connect(self._on_topic_changed)
        self.list_topics.setCurrentRow(initial_tab)

    def _on_topic_changed(self, index: int) -> None:
        if 0 <= index < len(HELP_SECTIONS):
            _, content = HELP_SECTIONS[index]
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

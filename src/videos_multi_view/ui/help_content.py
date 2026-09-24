# ruff: noqa: E501
"""Built-in user guides; macros and project values are never translated."""

from videos_multi_view.i18n import language

HELP_SECTIONS = [
    (
        "1. 시작하기 및 영상 추가",
        """
        <h2>SyncView 시작하기</h2>
        <p><b>SyncView</b>는 여러 개의 로컬 동영상을 하나의 화면에 그리드로 배치하여
        동기 재생하고, 오프셋과 이름표(라벨)를 편집하여 하나의 <b>MP4 영상</b>으로 합성·내보내는 도구입니다.</p>

        <h3>영상 추가 방법</h3>
        <ul>
            <li><b>추가 또는 드래그 앤 드롭:</b> 파일 탐색기에서 영상을 좌측 영상 목록으로 드래그하거나 <b>[추가]</b> 버튼을 클릭합니다.</li>
            <li><b>지원 형식:</b> MP4, MOV, MKV, AVI, WebM 등 FFmpeg/FFprobe가 지원하는 모든 표준 영상 포맷.</li>
            <li><b>다양한 해상도 및 FPS:</b> 서로 다른 해상도, 화면비, FPS를 가진 영상들도 원본 비율을 유지하며 자동으로 최적 배치됩니다.</li>
        </ul>
        <p><b>Language / 언어</b> 메뉴에서 한국어·English를 즉시 전환합니다. 첫 실행에서는 시스템 언어를 사용하며, 선택은 다음 실행에도 유지됩니다. 원본 경로·이름표·프로젝트 내용은 번역하지 않습니다.</p>
        <p><b>파일 → 저장</b>으로 배치와 설정을 JSON 프로젝트에 보관합니다. 영상 파일은 별도로 보관하며, 이동한 파일은 <b>원본 다시 연결</b>로 찾습니다.</p>
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
        "6. 오버레이 비교 모드 (투명도·색상·잔차 오류)",
        """
        <h2>오버레이 영상 비교 모드</h2>
        <p>두 개 이상의 영상이 등록되어 있을 때, 두 영상을 동일한 위치에 겹쳐서 재생하며 시각적 차이나 픽셀 단위 잔차를 정밀하게 분석할 수 있습니다.</p>

        <h3>비교 모드 활성화 및 단축키</h3>
        <ul>
            <li><b>상단 툴바 / 메뉴:</b> 미리보기 상단의 <b>[⧉ 오버레이]</b> 버튼을 누르거나 <code>Ctrl + 3</code> 키를 누릅니다.</li>
            <li><b>설정 패널:</b> 우측 <b>[오버레이 비교]</b> 그룹에서 <b>[오버레이 비교 모드 활성화]</b> 체크박스를 선택합니다.</li>
            <li><b>영상 선택:</b> 기준 영상 (A)과 비교 대상 영상 (B)을 드롭다운에서 각각 지정합니다.</li>
        </ul>

        <h3>3가지 비교 방식</h3>
        <ul>
            <li><b>투명도 블렌드 (Alpha Blend):</b> 기준 영상 위에 비교 영상을 반투명하게 겹쳐서 표시합니다. 슬라이더(0% ~ 100%)로 투명도를 부드럽게 조절하여 시간적·공간적 위치 차이를 확인합니다.</li>
            <li><b>색상 틴트 비교 (Color Tint):</b> 두 영상에 보색 관계인 색상(예: Red와 Cyan)을 곱하여 합성합니다. 두 영상의 픽셀이 일치하는 영역은 자연스러운 무채색(그레이)으로 나타나고, 차이가 나는 움직임이나 불일치 영역은 선명한 붉은색/청록색 윤곽선으로 즉시 드러납니다. (Red/Cyan, Green/Magenta, Blue/Yellow 배색 지원)</li>
            <li><b>잔차 오류 맵 (Difference Map):</b> 두 영상 간의 절대 픽셀 차이 |A - B|를 계산합니다. 완전히 동일한 픽셀은 검은색(0)으로 표시되며, 미세한 노이즈나 압축 아티팩트, 객체 움직임은 밝게 표시됩니다. <b>잔차 증폭 배율(1.0x ~ 50.0x)</b>로 미세 오차를 증폭할 수 있으며, <b>잔차 색상(흑백, 히트맵, 레인보우 Jet, 네온 그린, 네온 마젠타, 사용자 지정 색상)</b>을 선택하여 시각적 인지도를 극대화할 수 있습니다.</li>
        </ul>

        <h3>실시간 재생 및 내보내기 연동</h3>
        <p>오버레이 비교 모드 상태에서도 공통 타임라인 재생, 일시정지, 탐색, 오프셋 조절이 실시간으로 반영됩니다. 또한 오버레이 모드가 켜진 상태에서 <b>[내보내기]</b>를 실행하면, 선택한 비교 효과와 잔차 증폭이 적용된 비교 합성 영상을 MP4 파일로 그대로 저장할 수 있습니다.</p>
        """,
    ),
    (
        "7. MP4 내보내기 및 GPU 가속",
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
        "8. 키보드 단축키 일람",
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
                <td><code>Ctrl + 3</code></td>
                <td>오버레이 비교 모드 켜기 / 끄기 토글</td>
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
        "9. 오픈소스 라이선스 안내",
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

ENGLISH_HELP_SECTIONS = [
    (
        "1. Getting started",
        """
        <h2>Welcome to SyncView</h2>
        <p>Compare local videos together, adjust their timing and labels, and export a single MP4.</p>
        <ul>
          <li>Click <b>Add</b> in the video list, or drag files from Explorer onto it.</li>
          <li>Common inputs include MP4, MOV, MKV, AVI, and WebM. Decoding depends on the available codecs.</li>
          <li>Mixed sizes, aspect ratios, and frame rates are supported. Cells preserve source aspect ratios.</li>
        </ul>
        <p>Choose <b>Language / 언어 → English</b> or <b>한국어</b> to switch immediately. The first launch follows the system language (Korean or English fallback); your choice is remembered. Filenames, label text, and projects are not translated.</p>
        <p>Use <b>File → Save</b> to keep layout and settings in a JSON project. Keep the source videos separately; use <b>Relink source</b> when a file moves.</p>
        """,
    ),
    (
        "2. Timeline and synchronization",
        """
        <h2>One shared timeline</h2>
        <p>Play, pause, and seek all videos using the bottom playback bar.</p>
        <ul>
          <li>Select a video, then set its <b>Offset</b> in milliseconds in <b>Video settings</b>.</li>
          <li><b>Positive offsets:</b> delay the start. The cell shows the background until playback begins.</li>
          <li><b>Negative offsets:</b> skip the beginning of the source.</li>
          <li><b>M:</b> place the selected source's start at the current shared time. Alignment is manual.</li>
          <li>Shorter videos hold their last frame. The timeline ends with the latest video, including offsets.</li>
          <li>Audio is muted by default. Select one source for both playback and export.</li>
        </ul>
        <p>Source time = shared time − offset. This is intended for general visual comparison, without a frame-accurate measurement guarantee.</p>
        """,
    ),
    (
        "3. Grid, borders, and labels",
        """
        <h2>Design your comparison</h2>
        <ul>
          <li><b>Resolution:</b> output canvas width × height; default 1920×1080.</li>
          <li><b>Columns:</b> choose Auto or 1–9 columns. Rows are calculated automatically.</li>
          <li><b>Spacing / Margin:</b> cell spacing and outside margin in output pixels.</li>
          <li><b>Background / Borders:</b> set colors, border visibility, and border width.</li>
        </ul>
        <h3>Per-video labels</h3>
        <p>Select a video to edit its text, visibility, corner position, font, size, text color, and background color. Label backgrounds support transparency. Long text is shortened with an ellipsis to fit the cell.</p>
        <p>Fonts come from your computer; no font files are bundled. Another computer may use a substitute.</p>
        """,
    ),
    (
        "4. Label macros",
        """
        <h2>Use video information in labels</h2>
        <table border="1" cellpadding="6">
          <tr><th>Macro</th><th>Meaning</th><th>Example</th></tr>
          <tr><td>{filename}</td><td>Source filename without extension</td><td>Front_Camera</td></tr>
          <tr><td>{timecode}</td><td>Current time in this source</td><td>01:23.450</td></tr>
          <tr><td>{fps}</td><td>Source frame rate</td><td>30fps</td></tr>
          <tr><td>{resolution}</td><td>Source width x height</td><td>1920x1080</td></tr>
          <tr><td>{offset}</td><td>Start offset in milliseconds</td><td>1500ms</td></tr>
        </table>
        <p>Try <code>{filename} [{timecode}]</code> or <code>{filename} ({resolution} @ {fps})</code>.</p>
        <p>Timecodes update in both preview and export. They add rendering work compared with static labels.</p>
        """,
    ),
    (
        "5. Solo view",
        """
        <h2>Inspect one video</h2>
        <p>Double-click a preview cell to enlarge it to fill the canvas. Double-click again to return to the grid.</p>
        <p>Solo view and selection outlines affect the preview only. Export keeps the project grid.</p>
        <p>Use <b>F11</b> to hide or restore both side panels and make more room for the preview.</p>
        """,
    ),
    (
        "6. Overlay comparison mode",
        """
        <h2>Overlay Video Comparison Mode</h2>
        <p>When two or more videos are loaded, you can overlay two videos in the same position to inspect visual alignment and pixel-level residual differences.</p>

        <h3>Enabling Overlay Mode</h3>
        <ul>
          <li><b>Toolbar / Menu:</b> Click <b>[⧉ Overlay]</b> above the preview canvas, or press <code>Ctrl+3</code>.</li>
          <li><b>Settings Panel:</b> Check <b>Enable overlay comparison</b> under the <b>Overlay comparison</b> group.</li>
          <li><b>Source Selection:</b> Pick Base Video (A) and Overlay Video (B) from the dropdown menus.</li>
        </ul>

        <h3>Three Comparison Methods</h3>
        <ul>
          <li><b>Alpha Blend:</b> Overlays video B onto video A with adjustable opacity (0% to 100%) for temporal and spatial crossfading.</li>
          <li><b>Color Tint:</b> Tints video A and video B with complementary color palettes (such as Red and Cyan). Matching areas appear in natural neutral tones, while differences immediately stand out as vivid color fringes.</li>
          <li><b>Residual Difference Map:</b> Computes absolute pixel differences |A - B|. Identical pixels render pure black. Use <b>Residual Gain (1.0x to 50.0x)</b> to amplify subtle compression artifacts or sub-pixel differences, and choose from multiple <b>Difference Color</b> modes (Grayscale, Thermal Heatmap, Rainbow Jet, Neon Green, Neon Magenta, or Custom Color) to maximize visual contrast.</li>
        </ul>

        <h3>Playback and Export</h3>
        <p>Overlay comparison operates in real time during playback, scrubbing, and offset adjustments. Exporting while overlay mode is active renders the exact comparison effect into the output MP4 video.</p>
        """,
    ),
    (
        "7. MP4 export and GPU encoding",
        """
        <h2>Share a single MP4</h2>
        <p>Choose an output path, frame rate, and encoder, then click <b>Export</b>. The full timeline is exported with layout, offsets, borders, and labels.</p>
        <ul>
          <li><b>FPS:</b> 24, 30, or 60.</li>
          <li><b>CPU (libx264):</b> default software encoder.</li>
          <li><b>NVIDIA (h264_nvenc) / Intel (h264_qsv):</b> require compatible hardware and drivers. If encoding fails, choose CPU; fallback is not automatic.</li>
          <li><b>Audio:</b> the selected source's track is aligned with its offset; otherwise the result is silent.</li>
          <li><b>Cancel:</b> stops export and removes temporary output. Existing output is preserved on failure or cancellation.</li>
        </ul>
        <p>H.264 uses lossy compression. Compression and color conversion can cause pixel differences from the preview. The output canvas is opaque.</p>
        """,
    ),
    (
        "8. Keyboard shortcuts",
        """
        <h2>Keyboard shortcuts</h2>
        <table border="1" cellpadding="6">
          <tr><th>Key</th><th>Action</th></tr>
          <tr><td>Space</td><td>Play / pause</td></tr>
          <tr><td>Left / Right</td><td>Seek backward / forward by 100ms</td></tr>
          <tr><td>Shift + Left / Right</td><td>Seek by 1 second</td></tr>
          <tr><td>Home</td><td>Go to the beginning</td></tr>
          <tr><td>M</td><td>Align the selected source's start with the current time</td></tr>
          <tr><td>Delete</td><td>Remove the selected video</td></tr>
          <tr><td>Double-click</td><td>Toggle solo view</td></tr>
          <tr><td>Ctrl+1 / Ctrl+2</td><td>Toggle video list / settings</td></tr>
          <tr><td>Ctrl+3</td><td>Toggle overlay comparison mode</td></tr>
          <tr><td>F11</td><td>Expand / restore preview</td></tr>
          <tr><td>Ctrl+N / Ctrl+O / Ctrl+S</td><td>New project / open / save</td></tr>
          <tr><td>Ctrl+Shift+S</td><td>Save as</td></tr>
          <tr><td>F1</td><td>User guide</td></tr>
        </table>
        <p>An editing widget takes priority when it handles a key, such as during text entry.</p>
        """,
    ),
    (
        "9. Open-source licenses",
        """
        <h2>Open-source licenses</h2>
        <p>SyncView's original code and documentation use the <b>MIT License</b>. Third-party components retain their licenses.</p>
        <ul>
          <li><b>FFmpeg / FFprobe CLI:</b> GPLv3-or-later. Copyright the FFmpeg developers and contributing projects.</li>
          <li><b>PySide6 / Qt 6:</b> LGPLv3 for the modules used here. Copyright The Qt Company Ltd. and other contributors.</li>
          <li><b>Qt's FFmpeg libraries:</b> LGPLv2.1-or-later; verified version 7.1.5. A different build from the export CLI.</li>
          <li><b>Python:</b> PSF License and included notices. Copyright Python Software Foundation and other contributors.</li>
          <li><b>PyInstaller:</b> GPLv2-or-later with bootloader exception; runtime hooks use Apache-2.0.</li>
        </ul>
        <p>No font files are bundled. The unused GPL-only Qt Virtual Keyboard is excluded from builds.</p>
        <p>Preserve applicable notices, corresponding sources, and Qt replacement/recombination provisions when redistributing a binary. Principal license texts are in the bundle's LICENSE and licenses folder.</p>
        <p><a href="https://github.com/Rainbow-Tools/SyncView/blob/main/LICENSE">MIT License</a> ·
        <a href="https://github.com/Rainbow-Tools/SyncView/blob/main/THIRD_PARTY_NOTICES.md">Third-party notices</a> ·
        <a href="https://github.com/Rainbow-Tools/SyncView/blob/main/docs/LICENSING.md">Binary-release review (Korean)</a></p>
        """,
    ),
]


def help_sections() -> list[tuple[str, str]]:
    return ENGLISH_HELP_SECTIONS if language() == "en" else HELP_SECTIONS

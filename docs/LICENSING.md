# 라이선스 검토와 적용 범위

검토일: 2026-09-22. 저장소 코드, 고정 의존성, 기존 PyInstaller 분석 목록과 실제 FFmpeg 실행 파일·DLL을 확인했다. 이는 프로젝트의 기술적 라이선스 선택과 배포 준비 기록이며, 모든 국가·배포 형태에 대한 법적 적합성 인증은 아니다.

## 결정: 자체 코드는 MIT

SyncView의 독자적인 앱 코드와 문서는 [MIT](../LICENSE)를 적용한다. 다른 개발자가 작은 비교 도구를 수정·재사용하기 쉽게 하려는 선택이다. 상업적 사용과 비공개 수정도 허용하며, 저작권·라이선스 고지는 보존해야 한다. 별도 고지가 있는 외부 구성요소에는 이 MIT 허락을 적용하지 않는다.

Apache-2.0의 명시적 특허 허락이나 GPL의 파생 프로그램 재배포 조건을 추가할 필요가 현재 프로젝트 목적에서 확인되지는 않았다. 이는 사용된 코덱에 관한 제3자 특허 허락까지 부여한다는 뜻은 아니다.

## 코드 구조와 외부 구성요소

- **FFmpeg CLI:** `media/probe.py`·`media/exporter.py`에서 별도 프로세스로 실행한다. 인자, 표준 미디어 파일, rawvideo 스트림과 진행률 텍스트로 통신하며 GPL FFmpeg 라이브러리를 Python 앱에 직접 링크하지 않는다. 이 구조를 독립 프로그램의 결합으로 평가하여 앱에는 MIT를 선택했다. 단지 프로세스를 나눴다는 이유만으로 모든 결합이 독립적이라는 일반화는 하지 않는다. 링크 방식이나 통신 구조가 바뀌면 재검토한다. [GPLv3의 독립 저작물·aggregate 규정](https://opensource.org/license/gpl-3.0)
- **현재 CLI 빌드:** `ffmpeg -L`은 GPLv3-or-later를 보고한다. 이를 포함한 바이너리를 전달할 때 FFmpeg와 포함 라이브러리의 대응 소스·빌드 자료 제공 등 GPL 의무가 남는다. [FFmpeg 안내](https://ffmpeg.org/legal.html)
- **PySide6·Qt:** 실제 사용 모듈은 Qt Core/Gui/Widgets/Multimedia 중심이다. LGPLv3는 조건을 충족하면 앱에 별도 라이선스를 사용하는 것을 허용한다. 라이선스 사본·고지, 라이브러리의 대응 소스, 수정 라이브러리로 재결합·실행할 수 있는 방법 등이 필요하다. [LGPLv3 제4조](../licenses/LGPL-3.0.txt), [Qt 공식 안내](https://www.qt.io/development/open-source-lgpl-obligations)
- **Qt의 FFmpeg DLL:** `avcodec-61.dll` 등의 라이선스 함수를 호출한 결과 7.1.5 / LGPL-2.1-or-later였다. export용 GPL CLI와 다른 빌드다. LGPL 소스 제공 의무와 포함된 라이브러리의 고지를 별도로 확인한다.
- **PyInstaller:** bootloader 예외가 있으므로 이 패키징 도구를 썼다는 이유로 앱 전체를 GPL로 변경할 필요는 없다. runtime hook의 Apache-2.0 조건은 별도로 유지한다. [PyInstaller 안내](https://pyinstaller.org/en/stable/license.html)
- **Python·글꼴:** Python의 PSF 및 부속 고지는 보존한다. Pretendard·맑은 고딕은 설치된 글꼴을 사용하는 것이며 글꼴 파일을 배포하지 않는다.

## 발견한 빌드 문제와 수정

기존 `build/VideoMultiView/Analysis-00.toc`에는 사용하지 않는 `qtvirtualkeyboardplugin.dll`과 `Qt6VirtualKeyboard.dll`이 포함돼 있었다. [Qt Virtual Keyboard의 오픈소스 라이선스는 GPLv3](https://doc.qt.io/qt-6/qtvirtualkeyboard-index.html)이며 LGPL로 일괄 표기하면 부정확하다.

빌드 spec에서 두 구성요소를 제외하고, MIT·주요 외부 라이선스 원문·고지 문서를 EXE 데이터에 포함하도록 변경했다. Qt PDF 등 다른 플러그인은 Qt Virtual Keyboard와 라이선스가 같다고 추정하지 않는다. 최종 번들에서 제외 여부와 미리보기·export 동작을 확인한다.

## 소스 공개와 EXE 배포를 구분

현재 GitHub에는 앱 소스와 문서를 공개한다. 다운로드한 FFmpeg, Qt, Python 실행 파일은 Git에 포함하지 않는다. MIT 적용으로 이 소스의 재사용 조건을 명확히 한다. 이미 공개된 `v1.0.0` 태그의 이력은 다시 쓰지 않으며, MIT 고지는 이 변경이 포함된 커밋부터 저장소에 존재한다.

**외부에 제공할 EXE의 라이선스 준비가 완료됐다고 판단하지는 않는다.** 다음 항목은 바이너리 릴리스를 만들 때 확인·보관해야 한다.

1. 최종 EXE 안의 모든 DLL·플러그인·runtime hook 목록과 실제 버전·해시를 기록하고, 포함된 제3자 코드·Windows runtime의 재배포 조건까지 대조한다. 주요 라이선스 파일 몇 개만 넣는 것으로 전부 충족했다고 보지 않는다.
2. 정확한 CLI FFmpeg·Qt의 FFmpeg·Qt/PySide6 및 관련 라이브러리의 대응 소스, 적용 패치·설정·빌드 스크립트를 확보하고 해당 라이선스가 요구하는 방식으로 함께 제공한다. 버전 문자열이나 공식 홈페이지 링크만으로 충분하다고 가정하지 않는다.
3. 단일 EXE는 내부 DLL을 임시 폴더에 해제하므로 일반적인 설치 디렉터리의 DLL 교체와 다르다. LGPLv3 제4조(d)(0)의 소스·재결합 자료 제공 경로를 기준으로 수정된 Qt를 넣어 다시 빌드하고 실행하는 절차를 실제 검증한다. 필요하면 배포 형태를 폴더형으로 바꾼다.
4. EXE 옆에서도 읽을 수 있는 라이선스·고지 파일과 소스 제공 안내를 함께 배포한다. 사용자 매체의 권리와 H.264 등 코덱 특허는 앱의 MIT 라이선스로 해결되지 않는다.

이 저장소의 [외부 구성요소 고지](../THIRD_PARTY_NOTICES.md)는 주요 구성요소를 정리한 출발점이다. 아직 미완료인 대응 소스 묶음이나 법률 검토가 완료된 것처럼 표시하지 않는다.

## 포터블 ZIP 준비

`scripts/build_portable.ps1`는 단일 EXE와 별도로 폴더형 번들을 만든다. Qt DLL과 플러그인은 `_internal/PySide6/`에 있으며, Python·FFmpeg는 번들에서 사용한다. 한국어 Qt 대화상자를 위한 `qtbase_ko.qm`도 함께 포함한다.

ZIP에는 밖에서 읽을 수 있는 고지·주요 라이선스 원문, 앱 소스 스냅샷, 파일별 SHA256을 담은 `build-info.json`을 넣는다. 앱 소스 스냅샷은 외부 라이브러리의 대응 소스 제공을 대신하지 않는다. `binary_license_review_complete`는 아직 `false`이며 자동으로 GitHub Release에 게시하지 않는다. 폴더형은 DLL을 직접 교체할 수 있는 구조지만, 수정 Qt 조합의 실제 동작 확인과 위의 외부 소스·전체 고지 준비는 계속 필요하다.

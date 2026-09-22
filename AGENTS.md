# Repository Guidelines

## 프로젝트 목적과 구조

Windows x64에서 로컬 동영상을 그리드로 동기 재생하고, 테두리·이름표를 편집하여 MP4로 저장하는 사내·개인용 도구다. Python 3.12, PySide6, FFmpeg를 사용하며 단일 EXE로 빌드한다. 기능과 구현 순서는 [기획문서](docs/PLAN.md)를 따른다.

앱 소스는 `src/videos_multi_view/` 아래에 있으며 다음 책임으로 나뉜다.

- `core/`: 데이터 모델, 시간·레이아웃 계산. Qt와 입출력에 의존하지 않는다.
- `media/`: FFprobe 분석, Qt 재생, FFmpeg 합성.
- `application/`: 사용자 명령, 프로젝트 저장·열기, 작업 상태 관리.
- `ui/`: 창, 설정 패널, 미리보기, 사용자 입력.

자동화 테스트는 `tests/`, 기획·기술 문서는 `docs/`에 둔다. `test_assets/`의 영상 두 개는 로컬 검증용이며 파일명·개수·해상도를 제품 코드에 하드코딩하지 않는다.

## 개발·검증·빌드 명령

Python 3.12 가상환경에서 실행한다. 최초 설치는 `pip install -c constraints.txt -e ".[dev]"`를 사용하고, `scripts/setup_ffmpeg.ps1`로 검증된 FFmpeg·FFprobe를 준비한다. 상세 설치 절차는 [README](README.md)에 있다.

```powershell
python -m pip install -c constraints.txt -e ".[dev]"  # 개발 의존성 설치
python -m videos_multi_view               # 앱 실행
python -m pytest                          # 전체 테스트
python -m ruff check .                    # 정적 검사
python -m ruff format --check .            # 포맷 검사
python -m PyInstaller VideoMultiView.spec  # 단일 EXE 빌드
```

## 코드 스타일과 구현 원칙

들여쓰기는 4칸, 함수·변수는 `snake_case`, 클래스는 `PascalCase`를 사용한다. 공개 인터페이스에 타입 힌트를 붙이고 데이터는 dataclass로 표현한다. Ruff로 스타일을 통일한다.

UI에 시간 계산이나 FFmpeg 명령 생성 로직을 넣지 않는다. 미리보기와 export는 레이아웃 계산과 테두리·이름표 렌더러를 공유한다. 분석·export는 비동기로 처리하고 외부 프로세스는 인자 배열로 실행한다. 프레임은 영상별 최신 프레임만 유지하고 종료 시 자원을 해제한다.

앱 문구는 `i18n.tr`와 `translations.py`로 관리하고, 즉시 전환할 위젯 문구는 `ui.translation.bind`로 등록한다. 언어 설정은 프로젝트와 분리한다. 이름표·경로·저장된 enum 값은 번역하지 않으며 언어 변경으로 재생을 재설정하지 않는다.

## 테스트 지침

pytest와 pytest-qt를 사용하며 파일은 `test_*.py`, 테스트 함수는 `test_*`로 명명한다. 변경한 동작과 회귀 위험을 검증하는 테스트를 추가한다. 수치 커버리지 기준은 아직 지정하지 않는다.

기본 테스트는 임시 합성 영상을 사용한다. 개인 영상 추가 검증은 `pytest --local-assets`로 실행한다. 시간·좌표·저장·복원, 실제 출력의 오프셋·이름표·오디오, 작업 취소와 프로젝트 교체를 검증한다. 단일 EXE는 외부 Python·FFmpeg에 의존하지 않는 환경에서 확인한다.

## 커밋과 PR

커밋은 `Add synchronized playback`처럼 간결한 명령형 메시지를 사용한다. PR에는 변경 목적, 관련 이슈, 검증 결과를 기록하고 UI 변경에는 스크린샷을 첨부한다. 실행하지 못한 검증은 이유와 함께 명시한다.

## 버전과 태그

[Semantic Versioning](https://semver.org/)의 `MAJOR.MINOR.PATCH`를 따른다. 호환성 기준은 기존 프로젝트 파일을 여는 동작과 문서화된 CLI 옵션이다. 호환성을 깨면 MAJOR, 호환되는 기능 추가는 MINOR, 오류 수정은 PATCH를 올린다. 문서만 변경할 때는 버전 변경 없이 커밋한다.

릴리스 시 `pyproject.toml`과 `src/videos_multi_view/__init__.py`의 버전을 맞추고 [변경 이력](CHANGELOG.md)을 기록한다. 앱 버전과 프로젝트 JSON 스키마 버전은 별개다. 전체 테스트·Ruff 검사를 통과한 커밋에 `v1.1.0` 형태의 주석 태그를 생성하며, 공개된 태그는 이동하지 않는다. 소스 태그와 EXE·ZIP 공개는 별개이며 바이너리는 [배포 준비 조건](docs/LICENSING.md)을 충족한 뒤 게시한다.

## 파일과 리소스 관리

한글·공백 경로를 지원하고 원본 영상을 수정하지 않는다. 출력은 임시 파일에서 완료한 뒤 확정한다. 사용자 저장 위치와 번들 리소스 경로를 구분하고, EXE에 Qt 플러그인·FFmpeg·FFprobe를 포함한다. 비밀정보, 개인 영상, 생성 파일, 빌드 결과물은 커밋하지 않는다. 기존 테스트 자산은 보존한다.

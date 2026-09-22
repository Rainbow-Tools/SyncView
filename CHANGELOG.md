# Changelog

앱 버전은 [Semantic Versioning](https://semver.org/)을 따릅니다. 프로젝트 JSON의 스키마 버전은 별도로 관리합니다.

Application versions follow [Semantic Versioning](https://semver.org/). The project JSON schema is versioned separately.

## 1.1.0 — 2026-09-22

### 한국어

- 한국어·영어 UI를 즉시 전환하고 언어 선택을 기억합니다. 메뉴, 설정, 도움말, 진행 상태와 기본 대화상자를 번역했습니다. 첫 실행은 시스템 UI 언어를 따르며 그 외 언어에서는 영어를 사용합니다.
- 언어 변경 시 재생 상태, 사용자 이름표, 파일 경로와 프로젝트 설정을 유지합니다. `--language ko` 또는 `--language en`으로 이번 실행에만 언어를 지정할 수 있습니다.
- 포터블 Windows ZIP 빌드를 추가했습니다. 실행에 필요한 의존성, 빠른 시작 안내, 라이선스 고지, 앱 소스 스냅샷과 파일 해시를 포함합니다.
- 느린 첫 실행에서도 검증 모드가 영상 프레임을 기다린 뒤 MP4를 내보내도록 수정했습니다.
- 앱 소스·문서에 MIT 라이선스를 적용하고, 한국어·영어 README와 외부 구성요소 고지를 정리했습니다.

기존 프로젝트 JSON 버전 1과 CLI 사용 방식은 유지합니다. 이번 버전은 **소스 태그**이며, 일반 사용자용 EXE·ZIP의 공개는 [외부 라이선스 자료 준비](docs/LICENSING.md) 후 진행합니다.

### English

- Switch instantly between English and Korean; the app remembers your choice. Menus, settings, help, progress messages, and standard dialogs follow the selected language. First launch uses Korean on Korean-language systems and English otherwise.
- Language changes preserve playback, user labels, paths, and project settings. Use `--language ko` or `--language en` to override the language for one launch.
- Add a portable Windows ZIP build containing runtime dependencies, a quick start, license notices, an application source snapshot, and file hashes.
- Wait for video frames before exporting in verification mode, including on a slow first launch.
- License application code and documentation under MIT; update both READMEs and third-party notices.

Existing version 1 project files and CLI usage remain compatible. This is a **source tag**. Public EXE/ZIP downloads await the [third-party distribution materials](docs/LICENSING.md).

## 1.0.0

- 최초 소스 태그: 동기 멀티뷰 재생, 오프셋, 그리드·이름표 편집, 프로젝트 저장·복원, MP4 export.
- Initial source tag: synchronized multiview playback, offsets, grid and label editing, project save/load, and MP4 export.

[Compare 1.0.0 → 1.1.0](https://github.com/Rainbow-Tools/SyncView/compare/v1.0.0...v1.1.0)

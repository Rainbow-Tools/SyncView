# SyncView — 시작하기 / Getting started

## 한국어

1. 포터블 ZIP을 **모두 압축 해제**합니다.
2. `SyncView` 폴더 안의 **SyncView.exe**를 실행합니다. Python·FFmpeg를 따로 설치할 필요가 없습니다.
3. **Language / 언어 → 한국어** 또는 **English**를 선택합니다. 선택은 다음 실행에도 유지됩니다.
4. **추가**로 영상을 넣고 배치·오프셋·이름표를 조정합니다.
5. **파일 → 저장**으로 프로젝트를 보관하고, 출력 경로를 정한 뒤 **내보내기**로 MP4를 만듭니다.

`_internal` 폴더는 실행에 필요하므로 EXE와 함께 보관하세요. 언어 선택은 Windows 사용자 설정에 저장되며 프로젝트에는 들어가지 않습니다. 영상은 원래 위치에 남습니다. 프로젝트를 다른 PC로 옮길 때는 원본 영상도 함께 옮기세요.

여러 영상을 재생할 때 화면이 멈추거나 늦어지면 앱을 닫고 **Software decoding.cmd**로 실행해 보세요. GPU export가 실패하면 인코더를 **CPU**로 선택하세요. 상세 사용법은 **F1**입니다.

## English

1. **Extract the entire portable ZIP**.
2. Open the `SyncView` folder and run **SyncView.exe**. No separate Python or FFmpeg installation is needed.
3. Choose **Language / 언어 → English** or **한국어**. Your choice is remembered for the next launch.
4. Click **Add**, then adjust the grid, offsets, and labels.
5. Use **File → Save** to keep a project. Set an output path and click **Export** to create an MP4.

Keep the `_internal` folder beside the EXE. Language preferences are saved in your Windows user settings, separately from projects. Source videos stay in their original locations; transfer them too when moving a project to another computer.

If multiple previews stall or lag, close the app and launch **Software decoding.cmd**. If GPU export fails, select the **CPU** encoder. Press **F1** for the complete guide.

## 배포 상태 / Distribution status

이 문서는 포터블 패키지 사용 안내입니다. 로컬 빌드에는 공개 릴리스 준비가 끝나지 않은 후보도 포함됩니다. 외부에 재배포하기 전에는 라이선스 검토와 대응 소스 준비를 완료해야 합니다.

This guide explains how to use a portable package. A local build may be a candidate that is not ready for public release. Complete the licensing review and corresponding-source preparation before redistributing it.

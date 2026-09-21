# FFmpeg / FFprobe 준비

검증 버전은 **9.0.2 essentials, Windows x64, gyan.dev**다. 실행 파일은 Git에 포함하지 않는다.

저장소 루트에서 다음 명령으로 다운로드 및 SHA256 검증 후 설치한다.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup_ffmpeg.ps1
~~~

이미 받은 ZIP을 사용할 수도 있다.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup_ffmpeg.ps1 -Archive .tools/ffmpeg.zip
~~~

- [빌드 제공처](https://www.gyan.dev/ffmpeg/builds/)
- [고정 버전 ZIP](https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip)
- [제공처 ZIP 체크섬](https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip.sha256)
- [해당 FFmpeg 소스](https://github.com/FFmpeg/FFmpeg/commit/946fcce07b)

| 파일 | SHA256 |
|---|---|
| ZIP | 60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba |
| ffmpeg.exe | 3256173f3f8bffd7df12227c68adf68025edb1832273a9530688a7bb1ed8edec |
| ffprobe.exe | f0d36ecbbdd3bcfac3efa078c96c7271c2e68b3810595552ac3b7f17e9a65c52 |

스크립트는 이 폴더에 두 EXE와 원본 패키지의 LICENSE를 배치한다. 해당 빌드는 GPLv3이며 LICENSE는 앱 빌드에도 포함된다. Qt Multimedia 자체의 FFmpeg 라이브러리는 PySide6 패키지가 제공하며 이 CLI 실행 파일과는 별개다.

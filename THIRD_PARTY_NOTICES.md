# Third-party notices

SyncView's original application code and documentation are licensed under the
[MIT License](LICENSE). That license does not relicense third-party software,
its license texts, fonts, or user-supplied media. The Git repository excludes
downloaded media executables; a built EXE contains additional components.

Reviewed on 2026-09-22 against `constraints.txt` and the local Windows build.

| Component | Role and observed version | License / notice |
|---|---|---|
| PySide6, Shiboken6, Qt | GUI and playback, 6.11.2 | Open-source LGPL-3.0 path for the modules used here; [LGPL text](licenses/LGPL-3.0.txt), [GPL text incorporated by LGPLv3](licenses/GPL-3.0.txt). Copyright The Qt Company Ltd. and other contributors. [Upstream licensing](https://doc.qt.io/qtforpython-6/licenses.html) |
| FFmpeg / FFprobe CLI | Probing and export, gyan.dev 9.0.2 essentials | GPL-3.0-or-later, as reported by `ffmpeg -L`; copyright the FFmpeg developers and contributing projects. [Original distribution license](vendor/ffmpeg/LICENSE), [build and checksum details](vendor/ffmpeg/README.md) |
| FFmpeg libraries shipped by Qt | Preview decoding, 7.1.5 | LGPL-2.1-or-later, reported by `avcodec_license`, `avformat_license`, and `avutil_license` in the installed DLLs. These are separate from the GPL CLI. [LGPL text](licenses/LGPL-2.1.txt), [upstream source](https://github.com/FFmpeg/FFmpeg/tree/n7.1.5) |
| CPython | Runtime, 3.12.14 | PSF License and included historical/third-party notices; copyright Python Software Foundation and other contributors. [Runtime license](licenses/PYTHON.txt) |
| PyInstaller bootloader | Single-file packaging, 6.22.3 | GPL-2.0-or-later with the bootloader exception. The exception permits applications under other licenses. [Unmodified upstream notice](licenses/PYINSTALLER.txt) |
| PyInstaller runtime hooks | Frozen runtime setup | Apache-2.0; copyright PyInstaller Development Team and contributors. [License](licenses/APACHE-2.0.txt) |

Qt Virtual Keyboard is GPL-only under its open-source option. SyncView does not
use it, and the build spec excludes its plugin and library. This exclusion must
be rechecked when updating Qt or PyInstaller. Other Qt modules are not assumed
to be LGPL merely because they ship in a PySide6 wheel.

The font stack uses fonts installed on the user's computer (including Pretendard
or Malgun Gothic when available). No font files are bundled. User videos are
neither included in this repository nor covered by SyncView's MIT license.

## Binary redistribution

This is an inventory of principal components, not a complete bill of materials
or a certification that any EXE is ready for redistribution. Qt, FFmpeg, and
Python can contain additional libraries such as zlib, OpenSSL, image codecs,
and platform runtimes, each with its own conditions.

Preserve applicable copyright notices and license texts. Before distributing an
EXE, inventory its actual contents, provide the corresponding sources and build
materials required by its GPL/LGPL components, and support the Qt replacement
or relinking route required by LGPLv3. A link to an upstream homepage alone is
not a substitute for these obligations. See the [licensing review](docs/LICENSING.md)
for the selected approach and outstanding binary-release work.

# vbns
## Introduction
This is a Braille 'n Speak emulator, which sends the input from a serial port to a Windows screen reader, SAPI 5 or eSpeak-NG. It can be used with a MS-DOS emulator (like Dosbox) and a MS-DOS screen reader (such as ASAP or Habla) to hear the text sent by the screen reader in Windows itself. It was originally created by [Tyler Spivey](https://www.allinaccess.com), and modified by Sukil Etxenike. [Here is the original version](http://batsupport.com/unsupported/dosbox/vbns.zip).

This fork has been ported to Python 3 and now speaks through [Prism](https://pypi.org/project/prismatoid/) on Windows 10 and 11, falling back to `accessible_output2` on Windows 8.1 and earlier.

## Speech outputs
The emulator can speak through:

* A Windows screen reader or SAPI 5. On Windows 10/11 this is done through Prism; on older versions it falls back to `accessible_output2`. Both are installed as normal dependencies (the `accessible_output2` sources are no longer bundled in the repository).
* eSpeak-NG, built in via the `--espeak-voice` switch. (The original standalone eSpeak build lives at [vbns-espeak](https://github.com/sukiletxe/vbns-espeak).)

### Compatibility
The emulator understands both speech-box command styles, so it works whether the DOS screen reader drives it as a **BrailleMate** (letter-first commands, e.g. Window-Eyes) or as a **Braille 'n Speak** (number-first commands, e.g. JAWS). Speech rate, pitch and volume commands are applied to the chosen output; other inline control codes are consumed rather than spoken.

## Requirements
You will need Com0Com for the emulator to work properly:

* [Download for Windows XP](http://sourceforge.net/projects/com0com/files/com0com/3.0.0.0/com0com-3.0.0.0-i386-and-x64-unsigned.zip/download)
* [Download for Windows 7 and newer (x64)](http://code.google.com/p/powersdr-iq/downloads/detail?name=setup_com0com_W7_x64_signed.exe&can=2&q=)
* [Download for Windows 7 and newer (x86)](http://code.google.com/p/powersdr-iq/downloads/detail?name=setup_com0com_W7_x86_signed.exe&can=2&q=)

## Running
This project is managed with [uv](https://docs.astral.sh/uv/). With uv installed, run the emulator from the project root by specifying the port and how you want it to speak:

`uv run src/emu.py com8 --sapi`

This uses the COM8 port (the default one for ASAP in Talking Dosbox) and opens a menu to select a SAPI voice. If you omit the `--sapi` switch, the screen reader is detected automatically; if you append a number to the switch, the voice corresponding to that number in the menu is used.

To use an eSpeak voice:

`uv run src/emu.py com8 --espeak-voice=en`

This uses the COM8 port and the English eSpeak voice with the default variant. The voice is given in `language[-dialect][+variant]` format (e.g. `en`, `en-us`, `en+max`). Note that `--espeak-voice` and `--sapi` cannot be used together.

Pass `--habla` to make the emulator compatible with Habla.

### Running from source
You will need:

* Python 3.14 or newer.
* [uv](https://docs.astral.sh/uv/) to manage the virtual environment and dependencies.

Run `uv sync` to create the environment and install everything listed in `pyproject.toml` (Prism, `accessible_output2`, PySerial, PyWin32 and friends). `libloader` and `platform_utils` are still included in `src`.

### Diagnostics
To capture the raw serial byte stream for troubleshooting (for example, to identify inline synthesizer commands), set the `VBNS_RAWLOG` environment variable to a file path before running. Every byte received on the port is appended to that file. The capture is inert unless the variable is set.

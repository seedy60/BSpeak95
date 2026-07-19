# vbns

A Braille 'n Speak that never needed batteries: hear your DOS screen reader speak on modern Windows.

vbns is a Braille 'n Speak emulator for Windows. It listens on a serial port for the speech a MS-DOS screen reader would have sent to a Braille 'n Speak or BrailleMate hardware speech box, and reads that text aloud through a modern Windows screen reader, SAPI 5, or eSpeak-NG instead. Paired with a MS-DOS emulator such as [DOSBox](https://www.dosbox.com/) and a DOS screen reader such as ASAP or Habla, it lets you run vintage DOS software and hear it talk on a machine that has no real serial hardware and no real speech box attached.

It was originally created by [Tyler Spivey](https://www.allinaccess.com) and modified by Sukil Etxenike; [the original version is here](http://batsupport.com/unsupported/dosbox/vbns.zip). This fork brings it up to date: it runs on Python 3, speaks through [Prism](https://pypi.org/project/prismatoid/) on Windows 10 and 11 (falling back to `accessible_output2` on Windows 8.1 and earlier), and understands the command formats of both the Braille 'n Speak and the BrailleMate, so the same emulator works whether a DOS screen reader thinks it is driving one box or the other.

## vbns features

vbns takes a raw stream of bytes from a serial port and turns it into speech. The text a DOS screen reader sends is spoken through whichever output you choose, while the speech-box control commands buried in that stream, E.G. rate, pitch, and volume, are applied to the voice rather than read out as gibberish. Screen-position and index markers and other inline codes that older boxes understood are quietly consumed, so you hear the words and nothing else. It runs from a single command, needs no installer, and fits itself to the machine it is on, using Prism on modern Windows and `accessible_output2` where Prism cannot go.

## How vbns speaks

vbns can send the text on to any of the following:

* A Windows screen reader or SAPI 5. On Windows 10 and 11 this goes through Prism, which can drive NVDA, JAWS, System Access, Windows Narrator's engine, SAPI, and more; on Windows 8.1 and earlier it falls back to `accessible_output2`. Both are ordinary installed dependencies now, so the `accessible_output2` sources are no longer bundled in the repository.
* eSpeak-NG, built in and selected with the `--espeak-voice` switch. (The original standalone eSpeak build lives at [vbns-espeak](https://github.com/sukiletxe/vbns-espeak).)

Rate, pitch, and volume are set per output. Rate control works on any engine that supports it, E.G. SAPI 5 through Prism; screen readers that manage their own rate, E.G. NVDA, keep their own settings and the command is simply ignored.

## Compatibility with Braille 'n Speak and BrailleMate

DOS screen readers drove these Blazie speech boxes with slightly different command grammars, and vbns understands both without being told which one is in use:

* **BrailleMate**, E.G. as sent by Window-Eyes, puts the command letter first, E.G. `R` then `2` to set the rate.
* **Braille 'n Speak**, E.G. as sent by JAWS, puts the number first, E.G. `5` then `E` to set the rate.

Both share the same command-introducer byte, and vbns tells them apart by whether a digit or a letter follows it, so you can switch a DOS screen reader from one speech box to the other and keep going without restarting the emulator.

## vbns setup

### Requirements

You will need a pair of linked virtual serial ports so the DOS side and vbns can talk to each other. On Windows this is Com0Com:

* [Download for Windows XP](http://sourceforge.net/projects/com0com/files/com0com/3.0.0.0/com0com-3.0.0.0-i386-and-x64-unsigned.zip/download)
* [Download for Windows 7 and higher (x64)](http://code.google.com/p/powersdr-iq/downloads/detail?name=setup_com0com_W7_x64_signed.exe&can=2&q=)
* [Download for Windows 7 and higher (x86)](http://code.google.com/p/powersdr-iq/downloads/detail?name=setup_com0com_W7_x86_signed.exe&can=2&q=)

To run from source you will also need:

* Python 3.13 or newer.
* [uv](https://docs.astral.sh/uv/) to manage the virtual environment and dependencies.

### Building the environment

1. Press Windows + R, type cmd and press Enter.
2. Clone the repo.
    ```
    git clone https://github.com/seedy60/vbns-ao2
    ```
3. Install everything.
    ```
    cd vbns-ao2
    uv sync
    ```

`uv sync` creates the virtual environment and installs everything listed in `pyproject.toml`, E.G. Prism, `accessible_output2`, PySerial, and PyWin32. The `libloader` and `platform_utils` helpers are still included in `src`.

## Running the emulator

Run vbns from the project root, telling it which serial port to listen on and how you want it to speak:

```
uv run src/emu.py com8 --sapi
```

This listens on COM8, the default port for ASAP in Talking Dosbox, and opens a menu to pick a SAPI voice. Leave off `--sapi` and vbns detects your screen reader automatically; append a number, E.G. `--sapi 3`, and it uses that voice from the menu without asking.

To speak through an eSpeak voice instead:

```
uv run src/emu.py com8 --espeak-voice=en
```

The voice is given in `language[-dialect][+variant]` form, E.G. `en`, `en-us`, or `en+max`. `--espeak-voice` and `--sapi` cannot be used together.

Pass `--habla` to make vbns compatible with Habla.

## Adjusting rate, pitch and volume

You do not set these in vbns; the DOS screen reader does. Whenever it changes the speech box's rate, pitch, or volume, vbns receives that command on the serial line, maps the value onto the range of the output you are using, and applies it. SAPI 5 through Prism honours all three; eSpeak honours all three; a screen reader that owns its own speech, E.G. NVDA, keeps its own rate and the command is ignored rather than spoken. Change the speed in your DOS screen reader and the voice you hear speeds up or slows down to match.

## Diagnostics

To capture the raw serial byte stream for troubleshooting, E.G. to identify an inline speech-box command that is being read aloud, set the `VBNS_RAWLOG` environment variable to a file path before running:

```
set VBNS_RAWLOG=C:\temp\raw.bin
uv run src/emu.py com8 --sapi
```

Every byte received on the port is appended to that file. The capture is completely inert unless the variable is set.

## Command-line options

| Option | Meaning |
|--------|---------|
| `port` | The COM port to listen on, E.G. `com8`. Optional; defaults to `com8`. |
| `--sapi` | Speak through SAPI 5 / a Windows screen reader. Alone, opens a voice menu; with a number, E.G. `--sapi 3`, picks that voice; omitted, auto-detects your screen reader. |
| `--espeak-voice=VOICE` | Speak through eSpeak-NG with the given voice, E.G. `en`, `en-us`, `en+max`. Cannot be combined with `--sapi`. |
| `--habla` | Enable Habla compatibility. |

## Credits

vbns was created by [Tyler Spivey](https://www.allinaccess.com) and modified by Sukil Etxenike. It relies on Prism, `accessible_output2`, `libloader`, and `platform_utils` by Christopher Toth and Tyler Spivey, and on eSpeak-NG for the built-in synthesizer.

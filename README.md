# BSpeak95

A Braille 'n Speak that never needs batteries. Hear your pliocene screen reader speak on modern Windows.

BSpeak95 is a Braille 'n Speak emulator for Windows. It listens on a virtualized serial port for the speech an MS-DOS/old Windows screen reader would have sent to a Braille 'n Speak or BrailleMate hardware speech synthesizer, and reads that text aloud through a modern Windows screen reader, SAPI 5 or eSpeak-NG. Paired with an MS-DOS emulator such as [DOSBox](https://www.dosbox.com/) or a hypervisor like VMWare and an ancient screen reader such as ASAP or Habla, it lets you run vintage DOS/Windows software and hear it speak on a machine that has no real serial hardware and no real speech box attached.

BSpeak95 is a fork of Sukil Etxenike's [vbns-ao2](https://github.com/sukiletxe/vbns-ao2) project, which, in turn, is a fork of the vbns-espeak project originally created by [Tyler Spivey](https://www.allinaccess.com); [the original version is here](http://batsupport.com/unsupported/dosbox/vbns.zip). This fork brings the project up-to-date by allowing it to run on Python 3, speaking through [Prism](https://github.com/ethindp/prism) on Windows 10 and 11, falling back to `accessible_output2` on Windows 8.1 and earlier, and fixing various bugs such as the spurious announcement of 'I329' when connected to the BrailleMate synthesizer used by Window-Eyes and a bug that would cause the emulator to crash with a tuple index out of range error for receiving voice rate values that were either too low or too high.

## BSpeak95 features

BSpeak95 takes a raw stream of bytes from a serial port and turns it into speech. The text a vintage screen reader sends is spoken through whichever output backend you choose, while the speech-box control commands buried in that stream, E.G. rate, pitch and volume, are applied to the voice on the fly. It runs from a single command, needs no installer, and fits itself to the machine it is on, using Prism on modern Windows and accessible_output2 where Prism can't be used.

## How BSpeak95 speaks

BSpeak95 can  pipe text through any of the following:

* A Windows screen reader or SAPI 5. On Windows 10 and 11, this goes through Prism, which can drive NVDA, JAWS, System Access, Windows Narrator's engine, SAPI, and more; on Windows 8.1 and earlier, it falls back to accessible_output2.
* eSpeak-NG, built in and selected with the `--espeak-voice` switch. (The original standalone eSpeak build lives at [vbns-espeak](https://github.com/sukiletxe/vbns-espeak).)

Rate, pitch, and volume are set per output. Rate control works on any engine that supports it, E.G. SAPI 5 through Prism; screen readers that manage their own rate, E.G. NVDA, keep their own settings and the command is simply ignored.

## Compatibility with Braille 'n Speak and BrailleMate

DOS and very early Windows screen readers drove these speech synths with slightly different command grammars, and vbns understands both without being told which one is in use:

* BrailleMate, E.G. as sent by Window-Eyes, puts the command letter first, E.G. `R` then `2` to set the rate.
* Braille 'n Speak, E.G. as sent by JAWS, puts the number first, E.G. `5` then `E` to set the rate.

Both share the same command-introducer byte, and vbns tells them apart by whether a digit or a letter follows it, so you can switch a DOS screen reader from one speech box to the other and keep going without restarting the emulator.

## vbns setup

### Com0Com

You will need a pair of linked virtual serial ports so the screen reader and BSpeak95 can contact each other. On Windows, this is done via Com0Com:

1. [Download Com0Com](https://sourceforge.net/projects/com0com/files/latest/download).
2. Extract the zip file to a location of your choice.
3. Run the setup file relative to your system; x64 for a 64-bit system, x86 for a 32-bit system.
4. During installation, a Windows security dialog will appear asking if you trust the driver you're installing. This dialog doesn't take focus automatically, so you will have to find it with Alt Tab. Check the box to always trust software from the developer and click install.

#### The modern Windows driver signing problem

On modern versions of Windows 10 and 11, device drivers, even known safe drivers like Com0Com, will refuse to load without being signed by the omnipotent gods at Microsoft. Blind users can't disable secure boot independently because the BIOS doesn't have a screen reader and we're still arguing about which option goes where in 2026, and who wants to disable driver signature enforcement at the OS level on every damned reboot?

We can get around this not by disabling security features, but deceiving them. A convenient registry file is provided in this repo to help with this. Simply run the file called SystemUpgradeLie.reg, answer yes to the prompts and restart the PC. In simple terms, we're using a loophole where the driver signing rules don't apply if the version of Windows 10 or 11 you're using now is an upgrade from a prior version of Windows, like 7 or 8.1.

## Running from source

1. Press Windows + R, type cmd and press Enter.
2. Clone the repo.
    ```
    git clone https://github.com/seedy60/BSpeak95
    ```
3. Install UV.
    ```
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
4. Use UV to install Python if it isn't already installed.
    ```
    uv python install
    ```
5. Install required libraries.
    ```
    cd BSpeak95
    uv sync
    ```
6. Run BSpeak95, telling it which serial port to listen on and how you want it to speak:
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

Now all that's left to do is configure your DOS emulator or virtual machine to use a serial port like COM9 and the screen reader running inside that environment to use COM1.

### Running compiled

1. [Download the latest BSpeak95 release](https://github.com/seedy60/BSpeak95/releases/latest/download/BSpeak95.zip).
2. Extract the zip file to a location of your choice.
3. Run the speech.cmd file and choose a SAPI 5 voice from the menu. The included speech.cmd file will start the emulator listening on COM8.

## Adjusting rate, pitch and volume

You do not set these in BSpeak95; the screen reader does. Whenever it changes the synthesizer's rate, pitch, or volume, the emulator receives that command on the serial line, maps the value onto the range of the output you are using, and applies it. SAPI 5 through Prism honours all three; eSpeak honours all three; a screen reader that owns its own speech, E.G. NVDA, keeps its own rate and the command is ignored rather than spoken. Change the speed in your DOS screen reader and the voice you hear speeds up or slows down to suit.

## Diagnostics

To capture the raw serial byte stream for troubleshooting, E.G. to identify an inline speech-box command that is being read aloud, set the `VBNS_RAWLOG` environment variable to a file path before running:

```
set VBNS_RAWLOG=C:\temp\raw.bin
uv run src/emu.py com8 --sapi
```

Every byte received on the port is appended to that file. The capture is completely inert unless the variable is set.

## Command-line options

| Argument | Meaning |
|--------|---------|
| `port` | The COM port to listen on, E.G. `com8`. Optional; defaults to `com8`. |
| `--sapi` | Speak through SAPI 5 / a Windows screen reader. Alone, opens a voice menu; with a number, E.G. `--sapi 3`, picks that voice; omitted, auto-detects your screen reader. |
| `--espeak-voice=VOICE` | Speak through eSpeak-NG with the given voice, E.G. `en`, `en-us`, `en+max`. Cannot be combined with `--sapi`. |
| `--habla` | Enable Habla compatibility. |

## Credits

The original vbns was created by [Tyler Spivey](https://www.allinaccess.com) and modified by Sukil Etxenike to support accessible_output2 which allows it to use SAPI 5. BSpeak95 relies on Prism from Ethin Probst and accessible_output2 by Christopher Toth, and on eSpeak-NG for the built-in synthesizer.
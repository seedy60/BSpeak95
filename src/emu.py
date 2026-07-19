import serial, threading, io, cmd, time, signal
import string
import espeak
import tts
import sys, fix_win32com, os
if hasattr(sys, "frozen"):
    fix_win32com.fix()
# 16-entry maps: the device sends a 0-15 setting index; each map turns that
# index into a value on the active backend's scale.
ao2_rate_map = (-10, -8, -6, -4, -2, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
espeak_rate_map = (80, 100, 120, 140, 160, 180, 200, 240, 260, 290, 320, 350, 370, 390, 400, 450)
# SAPI pitch is -10..10; espeak pitch (espeakPITCH) is 0..99.
ao2_pitch_map = (-10, -8, -6, -4, -2, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
espeak_pitch_map = (0, 7, 13, 20, 26, 33, 40, 46, 53, 59, 66, 73, 79, 86, 92, 99)
# SAPI volume is 0..100; espeak volume (espeakVOLUME) is 0..200 (100 = normal).
ao2_volume_map = (0, 7, 13, 20, 27, 33, 40, 47, 53, 60, 67, 73, 80, 87, 93, 100)
espeak_volume_map = (0, 13, 27, 40, 53, 67, 80, 93, 107, 120, 133, 147, 160, 173, 187, 200)
if cmd.args.espeak!="":
 synth=espeak.Synth()
 synth.speak("ready")
 rate_map=espeak_rate_map
 pitch_map=espeak_pitch_map
 volume_map=espeak_volume_map
else:
 tts.set_output(cmd.args.sapi)
 tts.speak("ready", True)
 rate_map=ao2_rate_map
 pitch_map=ao2_pitch_map
 volume_map=ao2_volume_map
port = serial.serial_for_url(cmd.args.port, 9600)
cmdchar = '\x05'
buffer = io.StringIO()
in_command = False
cmd_letter = None
num=""
lst=[]
stopped=True
signal.signal(signal.SIGINT, signal.SIG_DFL)
def finish_command():
 # Apply the command accumulated since the last cmdchar, then clear the
 # command state. Values are consumed here so they never leak into the spoken
 # text. Handles both command orders (see parse): letter-first cmdchar+R+2 and
 # number-first cmdchar+5+E.
 global in_command, cmd_letter, num
 if cmd_letter in handlers and num != "" and num.isdigit():
  handlers[cmd_letter](int(num))
 in_command = False
 cmd_letter = None
 num = ""
def parse(ch):
 global in_command, cmd_letter, num, lst
 if ch == '\x18':
  reset()
  if cmd.args.espeak!="":
   synth.cancel()
  else:
   tts.silence()
 elif ch == cmdchar:
  finish_command()
  in_command = True
 elif ch == '\r' or ch == '\0':
  finish_command()
  if ch == '\0': port.write(b'\0')
  if buffer.tell() > 0: lst.append(buffer.getvalue())
  process(lst)
  reset()
 elif in_command:
  # Two command orders share the cmdchar, told apart by the first character
  # after it: a digit means number-first (Braille 'n Speak: cmdchar 5 E), a
  # letter means letter-first (BrailleMate: cmdchar R 2).
  if cmd_letter is None:
   if ch in string.digits:
    num += ch                # number-first: leading digits
   elif num != "":
    cmd_letter = ch          # number-first: this letter ends the command
    finish_command()
   else:
    cmd_letter = ch          # letter-first: command letter, value follows
  elif num != "" and num.isdigit() and ch not in string.digits:
   finish_command()          # letter-first numeric value ended; ch belongs to the text
   if ch >= ' ':
    buffer.write(ch)
  else:
   num += ch                 # value: digits, or an alpha code (e.g. T's voice letter)
 elif ch >= ' ':
  buffer.write(ch)           # printable text; drop stray control bytes (e.g. the
                             # 0x06 word separators JAWS sprinkles through its stream)
def process(lst):
 sb = io.StringIO()
 for item in lst:
  if isinstance(item, str):
   sb.write(item)
  elif isinstance(item, tuple):
   item[0](item[1])
 v = sb.getvalue()
 if v.strip() == '': return
 if cmd.args.espeak!="":
  synth.speak(v)
 else:
  tts.speak(v, False)

def speed(x):
 x = max(0, min(x, len(rate_map) - 1))
 if cmd.args.espeak != "":
  synth.set_rate(rate_map[x])
 else:
  tts.set_rate(rate_map[x])
def pitch(x):
 x = max(0, min(x, len(pitch_map) - 1))
 if cmd.args.espeak != "":
  synth.set_pitch(pitch_map[x])
 else:
  tts.set_pitch(pitch_map[x])
def volume(x):
 x = max(0, min(x, len(volume_map) - 1))
 if cmd.args.espeak != "":
  synth.set_volume(volume_map[x])
 else:
  tts.set_volume(volume_map[x])
def reset():
 global buffer, lst, in_command, num, cmd_letter
 buffer.seek(0)
 buffer.truncate()
 lst = []
 num=""
 in_command=False
 cmd_letter=None
handlers = {
'R': speed,   # rate (BrailleMate / Window-Eyes)
'E': speed,   # rate (legacy alias)
'P': pitch,   # pitch
'V': volume,  # volume
}
def stop():
 global stopped
 stopped=True
 parse('\r')
def habla():
 t=threading.Timer(0.3, stop)
 t.start()
# Set VBNS_RAWLOG=<path> to capture the raw serial byte stream for protocol
# diagnosis (e.g. identifying inline synthesizer commands that leak as speech).
_rawlog = open(os.environ["VBNS_RAWLOG"], "ab") if os.environ.get("VBNS_RAWLOG") else None
while True:
 b = port.read(1)
 if _rawlog is not None:
  _rawlog.write(b)
  _rawlog.flush()
 parse(b.decode("cp437"))
 if cmd.args.habla == True and stopped==True:
  stopped=False
  habla()

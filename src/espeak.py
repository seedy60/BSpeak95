import _espeak, cmd, string
class Synth(object):
 def __init__(self):
  _espeak.initialize()
  _espeak.setVoiceByName(cmd.args.espeak)
 def speak(self, text):
  _espeak.speak(text)
 def set_rate(self, wpm):
  _espeak.setParameter(_espeak.espeakRATE, wpm, 0)
 def set_pitch(self, value):
  _espeak.setParameter(_espeak.espeakPITCH, value, 0)
 def set_volume(self, value):
  _espeak.setParameter(_espeak.espeakVOLUME, value, 0)
 def skip(self): pass
 def cancel(self): _espeak.stop()

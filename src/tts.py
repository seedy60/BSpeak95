"""Screen-reader / SAPI output for the Braille 'n Speak emulator.

Uses Prism (the ``prismatoid`` package) on Windows 10 and 11, and falls back
to ``accessible_output2`` on Windows 8.1 and earlier, where Prism is not
supported. Both paths expose the same API so the rest of the emulator does
not need to know which library is speaking:

* ``set_output(output)`` -- 0 auto-detects a screen reader, -1 shows a SAPI
  voice menu, and any other number selects that SAPI voice.
* ``speak(text, interrupt=False)``
* ``silence()``
* ``set_rate(rate)`` -- ``rate`` is on the accessible_output2 SAPI scale
  (-10..10); it is converted to Prism's 0.0..1.0 scale as needed.
"""
import sys

# The active backend: a Prism ``Backend`` or an accessible_output2 ``Output``.
o = None


def _use_prism():
    """True on Windows 10/11, where Prism is supported; False elsewhere,
    so we fall back to accessible_output2."""
    if sys.platform != "win32":
        return False
    try:
        return sys.getwindowsversion().major >= 10
    except Exception:
        return False


_USE_PRISM = _use_prism()


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def speak(text, interrupt=False):
    if o is None:
        return
    try:
        if _USE_PRISM:
            if interrupt:
                try:
                    o.stop()
                except Exception:
                    pass
            o.speak(text)
        else:
            o.speak(text, interrupt)
    except Exception:
        pass


def silence():
    if o is None:
        return
    try:
        if _USE_PRISM:
            o.stop()
        else:
            o.silence()
    except Exception:
        pass


def set_rate(rate):
    """Set the speaking rate. ``rate`` is on the accessible_output2 SAPI
    scale of -10 (slowest) .. 10 (fastest)."""
    if o is None:
        return
    try:
        if _USE_PRISM:
            if getattr(o.features, "supports_set_rate", False):
                # Map -10..10 onto Prism's normalized 0.0..1.0 rate scale.
                o.rate = max(0.0, min(1.0, (rate + 10) / 20.0))
        else:
            o.set_rate(rate)
    except Exception:
        pass


def set_pitch(pitch):
    """Set the pitch. ``pitch`` is on the accessible_output2 SAPI scale of
    -10 (lowest) .. 10 (highest)."""
    if o is None:
        return
    try:
        if _USE_PRISM:
            if getattr(o.features, "supports_set_pitch", False):
                # Map -10..10 onto Prism's normalized 0.0..1.0 pitch scale.
                o.pitch = max(0.0, min(1.0, (pitch + 10) / 20.0))
        else:
            o.set_pitch(pitch)
    except Exception:
        pass


def set_volume(volume):
    """Set the volume. ``volume`` is on the accessible_output2 SAPI scale of
    0 (silent) .. 100 (loudest)."""
    if o is None:
        return
    try:
        if _USE_PRISM:
            if getattr(o.features, "supports_set_volume", False):
                # Map 0..100 onto Prism's normalized 0.0..1.0 volume scale.
                o.volume = max(0.0, min(1.0, volume / 100.0))
        else:
            o.set_volume(volume)
    except Exception:
        pass


def get_output():
    return o


def set_output(output):
    global o
    if _USE_PRISM:
        _set_output_prism(output)
    else:
        _set_output_ao2(output)


# ----------------------------------------------------------------------
# Prism path (Windows 10/11)
# ----------------------------------------------------------------------

def _set_output_prism(output):
    global o
    import prism
    ctx = prism.Context()
    if output == 0:
        o = ctx.create_best()
        return
    o = ctx.create(prism.BackendId.SAPI)
    voices = _prism_voice_names(o)
    if output == -1:
        _prism_menu(ctx, voices)
    else:
        _prism_set_voice(output - 1, voices)


def _prism_voice_names(backend):
    names = []
    try:
        features = backend.features
        if getattr(features, "supports_refresh_voices", False):
            backend.refresh_voices()
        if not getattr(features, "supports_count_voices", False):
            return names
        for i in range(backend.voices_count):
            name = "Voice %d" % i
            if getattr(features, "supports_get_voice_name", False):
                try:
                    name = backend.get_voice_name(i)
                except Exception:
                    pass
            names.append(name)
    except Exception:
        pass
    return names


def _prism_set_voice(index, voices):
    global o
    try:
        if getattr(o.features, "supports_set_voice", False) and 0 <= index < len(voices):
            o.voice = index
    except Exception:
        pass


def _prism_menu(ctx, voices):
    global o
    print("Select a voice from the following menu.")
    for item in range(0, len(voices)):
        print("%d: %s" % (item + 1, voices[item]))
    print("0: Use automatic output instead")
    v = int(input(">")) - 1
    if v == -1:
        o = ctx.create_best()
    elif 0 <= v < len(voices):
        _prism_set_voice(v, voices)
    else:
        print("Invalid option.")
        _prism_menu(ctx, voices)


# ----------------------------------------------------------------------
# accessible_output2 path (Windows 8.1 and earlier)
# ----------------------------------------------------------------------

def _set_output_ao2(output):
    global o
    import accessible_output2.outputs as ao2
    if output != 0:
        o = ao2.sapi5.SAPI5()
        vlist = o.list_voices()
        if output == -1:
            _ao2_menu(vlist)
        else:
            o.set_voice(vlist[output - 1])
    else:
        o = ao2.auto.Auto()
        if o.name == "Unnamed Output":
            o = o.get_first_available_output()


def _ao2_menu(vlist):
    global o
    import accessible_output2.outputs as ao2
    print("Select a voice from the following menu.")
    for item in range(0, len(vlist)):
        print("%d: %s" % (item + 1, vlist[item]))
    print("0: Use automatic output instead")
    v = int(input(">")) - 1
    if v == -1:
        o = ao2.auto.Auto()
    elif 0 <= v < len(vlist):
        o.set_voice(vlist[v])
    else:
        print("Invalid option.")
        _ao2_menu(vlist)

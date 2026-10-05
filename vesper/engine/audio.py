"""Procedural audio.

Every sound and the music loop are synthesised at runtime from pure maths, so
the project ships zero third-party audio and cannot inherit anyone else's
copyright.  If the mixer is unavailable the class degrades to silent no-ops,
which keeps headless tests and machines without a sound card working.
"""

from __future__ import annotations

import array
import math
import random
from typing import Dict, Optional, Sequence, Tuple

from .platform import Backend, SoundHandle

Segment = Tuple[float, float, str, float]  # freq, duration, wave, volume


def _osc(wave: str, phase: float) -> float:
    if wave == "sine":
        return math.sin(phase)
    if wave == "square":
        return 1.0 if math.sin(phase) >= 0 else -1.0
    if wave == "triangle":
        return 2.0 / math.pi * math.asin(math.sin(phase))
    if wave == "saw":
        t = (phase / math.tau) % 1.0
        return 2.0 * t - 1.0
    if wave == "noise":
        return random.uniform(-1.0, 1.0)
    return math.sin(phase)


class Synth:
    def __init__(self, sample_rate: int = 22050) -> None:
        self.rate = sample_rate

    def render(self, segments: Sequence[Segment], decay: float = 6.0,
               attack: float = 0.005) -> bytes:
        buf = array.array("h")
        phase = 0.0
        for freq, dur, wave, vol in segments:
            count = int(dur * self.rate)
            for i in range(count):
                t = i / self.rate
                phase += math.tau * freq / self.rate
                env = min(1.0, t / attack) if attack > 0 else 1.0
                env *= math.exp(-decay * t)
                value = _osc(wave, phase) * vol * env
                buf.append(max(-32767, min(32767, int(value * 32767))))
        return buf.tobytes()

    def music(self, notes: Sequence[Tuple[float, float]], bpm: float = 128.0,
              wave: str = "triangle", vol: float = 0.22) -> bytes:
        beat = 60.0 / bpm / 2.0  # eighth notes
        segments = []
        for freq, length in notes:
            segments.append((freq, beat * length, wave, vol))
        return self.render(segments, decay=2.2, attack=0.01)


# Note frequencies (A4 = 440).
NOTES = {
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00,
    "A3": 220.00, "B3": 246.94, "C4": 261.63, "D4": 293.66, "E4": 329.63,
    "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25,
    "D5": 587.33, "E5": 659.25, "G5": 783.99, "A5": 880.00, "C6": 1046.50,
}


class Audio:
    def __init__(self, backend: Optional[Backend] = None) -> None:
        self.backend = backend
        self.ok = False
        self.enabled = True
        self.sounds: Dict[str, SoundHandle] = {}
        self.music: Optional[SoundHandle] = None
        self._music_channel = None
        self.volume = 0.7
        self.music_volume = 0.5

    def init(self) -> None:
        if self.backend is None or not self.backend.audio_ready():
            self.ok = False
            return
        self.ok = True
        self._build()

    # -- library ----------------------------------------------------------
    def _build(self) -> None:
        synth = Synth(22050)
        library = {
            "jump": [(520, 0.10, "square", 0.22), (760, 0.08, "square", 0.16)],
            "shoot": [(900, 0.05, "square", 0.18), (500, 0.05, "saw", 0.12)],
            "charge": [(200, 0.25, "saw", 0.12), (420, 0.20, "saw", 0.18)],
            "charged_shot": [(1200, 0.10, "square", 0.25), (400, 0.16, "saw", 0.20)],
            "missile": [(300, 0.12, "saw", 0.22), (150, 0.16, "noise", 0.14)],
            "hit": [(320, 0.06, "square", 0.25), (180, 0.06, "noise", 0.18)],
            "enemy_hit": [(240, 0.05, "square", 0.20)],
            "enemy_die": [(300, 0.10, "saw", 0.22), (120, 0.20, "noise", 0.22)],
            "player_hurt": [(240, 0.14, "saw", 0.30), (120, 0.20, "square", 0.22)],
            "pickup": [(660, 0.08, "square", 0.20), (880, 0.10, "square", 0.20),
                       (1320, 0.14, "square", 0.18)],
            "upgrade": [(440, 0.12, "triangle", 0.25), (660, 0.12, "triangle", 0.25),
                        (880, 0.12, "triangle", 0.25), (1320, 0.30, "triangle", 0.28)],
            "door": [(180, 0.20, "square", 0.20), (90, 0.30, "saw", 0.16)],
            "save": [(523, 0.12, "triangle", 0.22), (659, 0.12, "triangle", 0.22),
                     (784, 0.24, "triangle", 0.22)],
            "explode": [(120, 0.30, "noise", 0.35), (60, 0.40, "saw", 0.25)],
            "land": [(160, 0.06, "noise", 0.16)],
            "dash": [(700, 0.08, "saw", 0.20), (1000, 0.06, "saw", 0.14)],
            "select": [(880, 0.04, "square", 0.16)],
            "confirm": [(660, 0.06, "square", 0.20), (990, 0.08, "square", 0.20)],
            "low_health": [(660, 0.10, "square", 0.20), (440, 0.14, "square", 0.20)],
            "splash_rise": [(330, 0.18, "triangle", 0.20), (495, 0.18, "triangle", 0.22),
                            (660, 0.30, "triangle", 0.24)],
        }
        for name, segments in library.items():
            snd = self.backend.make_sound(synth.render(segments))
            if snd is not None:
                self.sounds[name] = snd
        melody = [
            ("A4", 1), ("C5", 1), ("E5", 2), ("D5", 1), ("C5", 1), ("B4", 2),
            ("A4", 1), ("G4", 1), ("A4", 2), ("E4", 1), ("G4", 1), ("A4", 2),
            ("C5", 1), ("B4", 1), ("G4", 2), ("A4", 1), ("C5", 1), ("E5", 2),
            ("G5", 1), ("E5", 1), ("D5", 2), ("C5", 1), ("B4", 1), ("A4", 2),
        ]
        notes = [(NOTES[n], length) for n, length in melody]
        self.music = self.backend.make_sound(synth.music(notes, bpm=150))

    # -- playback ---------------------------------------------------------
    def play(self, name: str, volume: float = 1.0) -> None:
        if not (self.ok and self.enabled):
            return
        snd = self.sounds.get(name)
        if snd is not None:
            snd.set_volume(min(1.0, self.volume * volume))
            snd.play()

    def start_music(self) -> None:
        if not (self.ok and self.enabled and self.music):
            return
        self.stop_music()
        self._music_channel = self.music.play(loops=-1)
        if self._music_channel is not None:
            self._music_channel.set_volume(self.music_volume)

    def stop_music(self) -> None:
        if self.music is not None:
            self.music.stop()

    def set_enabled(self, value: bool) -> None:
        self.enabled = value
        if not value:
            self.stop_music()
        elif self.ok:
            self.start_music()

import os
import struct
import sounddevice as sd
import pvporcupine
from dotenv import load_dotenv

load_dotenv()


class HotwordDetector:
    def __init__(self, keyword="computer", on_detected=None):
        self.access_key = os.getenv("PICOVOICE_ACCESS_KEY")

        if not self.access_key:
            raise ValueError("Picovoice access key not found!")

        # Create Porcupine instance
        self.porcupine = pvporcupine.create(
            access_key=self.access_key,
            keywords=[keyword.lower()]
        )

        # Callback to trigger after wake word
        self.on_detected = on_detected

        self.sample_rate = self.porcupine.sample_rate
        self.frame_length = self.porcupine.frame_length

    def start(self):
        print("🎤 Listening for wake word: computer")

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self.frame_length,
            callback=self._audio_callback,
        ):
            while True:
                pass

    def _audio_callback(self, indata, frames, time, status):
        pcm = struct.unpack_from(
            "h" * self.frame_length,
            indata
        )

        keyword_index = self.porcupine.process(pcm)

        if keyword_index >= 0:
            print("🔥 Wake word detected")
            if self.on_detected:
                self.on_detected()

    def stop(self):
        self.porcupine.delete()

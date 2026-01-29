import threading
import time

from core.communication.hotword.porcupine_engine import HotwordDetector
from core.communication.stt.vosk_engine import VoskSTT
from core.communication.stt.cloud_stt import CloudSTT
from core.communication.llm.cloud_llm import CloudLLM
from core.communication.llm.router import SimpleLLMRouter
from core.communication.tts.cloud_tts import CloudTTS
from core.communication.tts.offline_tts import OfflineTTS
from core.communication.tts.tts_router import TTSRouter


VOSK_MODEL_PATH = "models/vosk/vosk-model-small-en-in-0.4"

stt = VoskSTT(VOSK_MODEL_PATH)
cloud_stt = CloudSTT()
llm = SimpleLLMRouter(CloudLLM())

tts = TTSRouter(
    cloud_tts=CloudTTS(),
    offline_tts=OfflineTTS()
)


# ------------------ Utility Functions ------------------

def warm_up_llm(llm):
    print("🔥 Warming up LLM...")
    try:
        llm.generate("Hello")
    except Exception:
        pass
    print("✅ LLM warm-up complete")


def stt_is_bad(text: str) -> bool:
    if not text:
        return True
    if len(text.split()) < 3:
        return True
    if "die" in text and "today" not in text:
        return True
    return False


def shorten_for_tts(text, max_words=35):
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "."
    return text


# ------------------ Thinking Cue Logic ------------------

def thinking_cue_worker(tts, stop_event):
    time.sleep(1.5)
    if not stop_event.is_set():
        tts.speak("Hmm… well.")


# ------------------ Wake Word Handler ------------------

def handle_wake_word():
    text, audio_np = stt.listen_and_transcribe()
    print(f"📝 Vosk heard: {text}")

    if stt_is_bad(text):
        print("⚠️ Low confidence STT — retrying with Whisper")
        text = cloud_stt.transcribe(audio_np, stt.sample_rate)
        print(f"📝 Whisper heard: {text}")

    if not text:
        tts.speak("Sorry, I didn't catch that.")
        return

    # Start thinking cue (cancelable)
    stop_event = threading.Event()
    thinking_thread = threading.Thread(
        target=thinking_cue_worker,
        args=(tts, stop_event),
        daemon=True
    )
    thinking_thread.start()

    response = llm.generate(text)
    stop_event.set()  # Cancel thinking cue if not spoken yet

    print(f"🤖 AURA: {response}")

    spoken_text = shorten_for_tts(response)
    tts.speak(spoken_text)


# ------------------ Main Entry ------------------

if __name__ == "__main__":
    warm_up_llm(llm)

    detector = HotwordDetector(
        keyword="computer",
        on_detected=handle_wake_word
    )
    detector.start()

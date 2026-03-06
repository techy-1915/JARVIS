"""Speech synthesis – converts text to audio using TTS."""

import logging

logger = logging.getLogger(__name__)


class SpeechSynthesizer:
    """Converts text to speech audio.

    Uses pyttsx3 offline or gTTS (online) when available.
    Degrades gracefully when no TTS library is installed.
    """

    def __init__(self, engine: str = "auto") -> None:
        """Initialise the synthesiser.

        Args:
            engine: Preferred TTS engine (``"pyttsx3"``, ``"gtts"``, ``"auto"``).
        """
        self._engine_name = engine
        self._engine = None
        self._try_load(engine)

    def _try_load(self, engine: str) -> None:
        """Attempt to load the preferred TTS engine."""
        if engine in ("auto", "pyttsx3"):
            try:
                import pyttsx3  # type: ignore[import]
                self._engine = pyttsx3.init()
                self._engine_name = "pyttsx3"
                logger.info("TTS: using pyttsx3")
                return
            except Exception:  # noqa: BLE001
                pass
        if engine in ("auto", "gtts"):
            try:
                import gtts  # type: ignore[import]  # noqa: F401
                self._engine_name = "gtts"
                logger.info("TTS: using gTTS")
                return
            except ImportError:
                pass
        logger.warning("No TTS engine available; speech synthesis disabled")
        self._engine_name = "none"

    def speak(self, text: str) -> bool:
        """Speak text aloud.

        Args:
            text: The text to speak.

        Returns:
            True if speech was produced, False otherwise.
        """
        if self._engine_name == "pyttsx3" and self._engine is not None:
            self._engine.say(text)
            self._engine.runAndWait()
            return True
        elif self._engine_name == "gtts":
            try:
                from gtts import gTTS  # type: ignore[import]
                import tempfile
                import subprocess
                tts = gTTS(text)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tts.save(tmp.name)
                    subprocess.run(["mpg123", "-q", tmp.name], check=False)
                return True
            except Exception as exc:  # noqa: BLE001
                logger.error("gTTS speak failed: %s", exc)
                return False
        logger.debug("TTS not available; would speak: %s", text[:50])
        return False

    def save_to_file(self, text: str, output_path: str) -> bool:
        """Save synthesised speech to an audio file.

        Args:
            text: The text to synthesise.
            output_path: Path to save the audio file.

        Returns:
            True if the file was saved successfully.
        """
        if self._engine_name == "pyttsx3" and self._engine is not None:
            try:
                self._engine.save_to_file(text, output_path)
                self._engine.runAndWait()
                return True
            except Exception as exc:  # noqa: BLE001
                logger.error("pyttsx3 save failed: %s", exc)
                return False
        elif self._engine_name == "gtts":
            try:
                from gtts import gTTS  # type: ignore[import]
                tts = gTTS(text)
                tts.save(output_path)
                return True
            except Exception as exc:  # noqa: BLE001
                logger.error("gTTS save failed: %s", exc)
                return False
        return False

    @property
    def is_available(self) -> bool:
        """True if a TTS engine is loaded."""
        return self._engine_name != "none"

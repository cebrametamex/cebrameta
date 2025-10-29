from pathlib import Path
import unittest

from avatar_pipeline.config import GenerationConfig, VoiceProfile


class GenerationConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(self._testMethodName)
        self.tmp_dir.mkdir(exist_ok=True)
        self.image = self.tmp_dir / "image.jpg"
        self.image.write_bytes(b"fake")
        self.voice = VoiceProfile(
            name="test",
            display_name="Test",
            locale="es-MX",
            voice_id="es-MX-TestNeural",
        )

    def tearDown(self) -> None:
        for path in sorted(self.tmp_dir.glob("**/*"), reverse=True):
            if path.is_file():
                path.unlink()
            else:
                path.rmdir()
        if self.tmp_dir.exists():
            self.tmp_dir.rmdir()

    def test_paths_and_defaults(self) -> None:
        config = GenerationConfig(
            image_path=self.image,
            script_text=" Hola ",
            output_dir=self.tmp_dir / "out",
            voice=self.voice,
        )

        self.assertEqual(config.script_text, "Hola")
        self.assertTrue(config.output_audio_path().name.endswith("_speech.wav"))
        self.assertTrue(config.output_video_path().name.endswith("_avatar.mp4"))

    def test_rejects_empty_script(self) -> None:
        with self.assertRaises(ValueError):
            GenerationConfig(
                image_path=self.image,
                script_text="   ",
                output_dir=self.tmp_dir / "out",
                voice=self.voice,
            )


if __name__ == "__main__":
    unittest.main()

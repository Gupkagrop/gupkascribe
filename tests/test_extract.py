"""Модульные тесты для проверки логики извлечения данных и сервисного слоя extract.py."""

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import ffmpeg

from src.cuda_utils import setup_cuda_dll_paths
from src.extract import (
    ExtractionError,
    FFmpegExecutionError,
    _decode_ffmpeg_error,
    check_ffmpeg_installed,
    extract_audio,
    extract_content,
)


class TestExtractModule(unittest.TestCase):
    """Сьют модульных тестов для валидации функций обработки видео."""

    def test_ffmpeg_preflight_check(self) -> None:
        """Проверка возврата булевого значения функцией проверки ffmpeg."""
        result = check_ffmpeg_installed()
        self.assertIsInstance(result, bool)

    def test_decode_ffmpeg_error_safety(self) -> None:
        """Проверка безопасного декодирования stderr даже при повреждённых байтах."""
        mock_error = MagicMock(spec=ffmpeg.Error)
        mock_error.stderr = "Тестовая ошибка ffmpeg".encode("utf-8")
        decoded = _decode_ffmpeg_error(mock_error)
        self.assertIn("Тестовая ошибка ffmpeg", decoded)

        # Проверка защиты от падений на битых байтах
        mock_error.stderr = b"\xff\xfe\xfd\x80"
        safe_decoded = _decode_ffmpeg_error(mock_error)
        self.assertIsInstance(safe_decoded, str)

    def test_nonexistent_video_raises_extraction_error(self) -> None:
        """Передача несуществующего пути обязана выбрасывать ExtractionError."""
        fake_path = "C:/non_existent_video_file_12345.mp4"
        with self.assertRaises(ExtractionError) as context:
            extract_content(fake_path)
        self.assertIn("Видеофайл не найден", str(context.exception))

    def test_cuda_dll_setup_returns_list(self) -> None:
        """Функция настройки путей CUDA возвращает список путей без исключений."""
        paths = setup_cuda_dll_paths()
        self.assertIsInstance(paths, list)

    def test_exceptions_hierarchy(self) -> None:
        """Проверка корректной иерархии исключений."""
        self.assertTrue(issubclass(FFmpegExecutionError, ExtractionError))
        self.assertTrue(issubclass(ExtractionError, Exception))

    @patch("src.extract.check_ffmpeg_installed", return_value=False)
    def test_extract_audio_requires_ffmpeg(self, mock_check: MagicMock) -> None:
        """При отсутствии ffmpeg должно выбрасываться исключение FFmpegExecutionError."""
        with self.assertRaises(FFmpegExecutionError):
            extract_audio("any_video.mp4", "any_audio.wav")


if __name__ == "__main__":
    unittest.main()

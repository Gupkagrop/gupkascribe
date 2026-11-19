"""Пакет recording — модуль автономной транскрибации лекций с аппаратным ускорением."""

from src.cuda_utils import setup_cuda_dll_paths
from src.extract import (
    ExtractionError,
    FFmpegExecutionError,
    check_ffmpeg_installed,
    extract_audio,
    extract_content,
    extract_frames,
    transcribe_audio,
)

__version__ = "0.2.0"
__all__ = [
    "__version__",
    "setup_cuda_dll_paths",
    "check_ffmpeg_installed",
    "extract_audio",
    "transcribe_audio",
    "extract_frames",
    "extract_content",
    "ExtractionError",
    "FFmpegExecutionError",
]

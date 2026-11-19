"""Модуль извлечения аудиодорожки, транскрибации речи и нарезки опорных слайдов из видеофайлов."""

import os
import shutil
import sys
from pathlib import Path
from typing import Callable, Optional

from src.cuda_utils import setup_cuda_dll_paths

setup_cuda_dll_paths()

import ffmpeg
from faster_whisper import WhisperModel

ProgressCallback = Callable[[str], None]


class ExtractionError(Exception):
    """Базовое исключение для ошибок процесса извлечения данных."""


class FFmpegExecutionError(ExtractionError):
    """Исключение при ошибках выполнения системных команд ffmpeg."""


def check_ffmpeg_installed() -> bool:
    """Проверка доступности бинарного файла ffmpeg в системном окружении."""
    return shutil.which("ffmpeg") is not None


def _decode_ffmpeg_error(error: ffmpeg.Error) -> str:
    """Безопасное декодирование stderr от ffmpeg с защитой от сбоев кодировок Windows."""
    if not error.stderr:
        return str(error)
    return error.stderr.decode("utf-8", errors="replace")


def _log(message: str, progress_cb: Optional[ProgressCallback] = None) -> None:
    """Вспомогательная функция отправки сообщения в коллбэк логов."""
    if progress_cb is not None:
        progress_cb(message)


def extract_audio(
    video_path: str,
    temp_audio_path: str,
    progress_cb: Optional[ProgressCallback] = None,
) -> None:
    """Извлечение 16-битной PCM аудиодорожки с частотой 16 кГц через ffmpeg."""
    if os.path.exists(temp_audio_path) and os.path.getsize(temp_audio_path) > 0:
        return

    if not check_ffmpeg_installed():
        raise FFmpegExecutionError("Исполняемый файл ffmpeg не найден в системном PATH.")

    _log("Извлечение аудиодорожки...", progress_cb)
    try:
        (
            ffmpeg.input(video_path)
            .output(temp_audio_path, acodec="pcm_s16le", ac=1, ar="16k")
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error as error:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        err_msg = _decode_ffmpeg_error(error)
        raise FFmpegExecutionError(f"Ошибка ffmpeg при извлечении аудио: {err_msg}") from error
    except Exception as exc:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        raise ExtractionError(f"Непредвиденный сбой при извлечении аудио: {exc}") from exc


def _create_whisper_model(model_size: str, progress_cb: Optional[ProgressCallback] = None) -> WhisperModel:
    """Инициализация модели WhisperModel с автопереключением CUDA -> CPU."""
    try:
        _log(f"Загрузка модели Whisper ({model_size}) на GPU CUDA...", progress_cb)
        return WhisperModel(model_size, device="cuda", compute_type="float16")
    except Exception:
        _log(f"CUDA недоступна. Переключение Whisper ({model_size}) на CPU (int8)...", progress_cb)
        return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe_audio(
    audio_path: str,
    transcript_file_path: str,
    model_size: str = "small",
    progress_cb: Optional[ProgressCallback] = None,
) -> None:
    """Транскрибация аудио через faster-whisper с сохранением временных меток."""
    if os.path.exists(transcript_file_path) and os.path.getsize(transcript_file_path) > 0:
        return

    _log("Транскрибация аудио в текст...", progress_cb)
    model = _create_whisper_model(model_size, progress_cb)

    try:
        segments, _ = model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
    except Exception as exc:
        _log(f"Ошибка инференса на GPU: {exc}. Перезапуск транскрибации на CPU...", progress_cb)
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

    temp_transcript = transcript_file_path + ".tmp"
    try:
        with open(temp_transcript, "w", encoding="utf-8") as file:
            for segment in segments:
                start_min = int(segment.start // 60)
                start_sec = int(segment.start % 60)
                line = f"[{start_min:02d}:{start_sec:02d}] {segment.text}"
                file.write(line + "\n")
                _log(line, progress_cb)
        if os.path.exists(transcript_file_path):
            os.remove(transcript_file_path)
        os.rename(temp_transcript, transcript_file_path)
    except Exception as exc:
        if os.path.exists(temp_transcript):
            os.remove(temp_transcript)
        raise ExtractionError(f"Сбой записи файла транскрипции: {exc}") from exc


def extract_frames(
    video_path: str,
    frames_directory: str,
    video_basename: str,
    progress_cb: Optional[ProgressCallback] = None,
) -> None:
    """Извлечение ключевых слайдов через Scene Change Detection с fallback на регулярные интервалы."""
    os.makedirs(frames_directory, exist_ok=True)
    if len(os.listdir(frames_directory)) > 0:
        return

    if not check_ffmpeg_installed():
        raise FFmpegExecutionError("Исполняемый файл ffmpeg не найден в системном PATH.")

    _log("Извлечение ключевых слайдов (умная детекция смены сцен)...", progress_cb)
    out_pattern = os.path.join(frames_directory, f"{video_basename}-frame-%04d.jpg")
    select_expr = "isnan(prev_selected_t)+gte(t-prev_selected_t,5)*(gt(scene,0.05)+gte(t-prev_selected_t,120))"

    try:
        (
            ffmpeg.input(video_path)
            .filter("select", select_expr)
            .output(out_pattern, fps_mode="vfr", qscale=2)
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error as error:
        err_msg = _decode_ffmpeg_error(error)
        _log(f"Предупреждение ffmpeg (scene detection): {err_msg}. Переход на резервный режим...", progress_cb)
        _extract_frames_fallback(video_path, out_pattern)


def _extract_frames_fallback(video_path: str, out_pattern: str) -> None:
    """Резервное извлечение кадров с фиксированной частотой 1 кадр в минуту."""
    try:
        (
            ffmpeg.input(video_path)
            .filter("fps", fps=1 / 60)
            .output(out_pattern)
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error as fallback_err:
        fallback_msg = _decode_ffmpeg_error(fallback_err)
        raise FFmpegExecutionError(f"Критическая ошибка ffmpeg при нарезке кадров: {fallback_msg}") from fallback_err


def extract_content(
    video_path: str,
    custom_save_dir: Optional[str] = None,
    progress_cb: Optional[ProgressCallback] = None,
) -> str:
    """Координатор сквозного процесса подготовки данных из видеозаписи.

    Returns:
        str: Путь к каталогу с результатами обработки (аудио, транскрипт, кадры).
    """
    if not os.path.isfile(video_path):
        raise ExtractionError(f"Видеофайл не найден: {video_path}")

    video_basename = os.path.splitext(os.path.basename(video_path))[0]
    if custom_save_dir:
        output_dir = os.path.join(custom_save_dir, video_basename)
    else:
        project_root = Path(__file__).resolve().parent.parent
        output_dir = str(project_root / "cache" / video_basename)

    os.makedirs(output_dir, exist_ok=True)
    temp_audio = os.path.join(output_dir, "audio.wav")
    transcript_file = os.path.join(output_dir, "transcript.txt")
    frames_dir = os.path.join(output_dir, "frames")

    extract_audio(video_path, temp_audio, progress_cb)
    transcribe_audio(temp_audio, transcript_file, progress_cb=progress_cb)
    extract_frames(video_path, frames_dir, video_basename, progress_cb)

    _log(f"✅ Успешно завершено! Результаты сохранены в: {output_dir}", progress_cb)
    return output_dir


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: uv run python src/extract.py <путь_к_видео>")
        sys.exit(1)

    try:
        extract_content(sys.argv[1], progress_cb=print)
    except ExtractionError as err:
        print(f"Ошибка обработки: {err}")
        sys.exit(1)

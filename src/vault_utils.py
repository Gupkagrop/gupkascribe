"""Модуль аудита базы знаний Obsidian Vault, проверки целостности связей и системной телеметрии."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, TypedDict

TARGET_SUBJECTS: Dict[str, str] = {
    "Математика Матанализ": "МатАн",
    "Дискретная математика": "ДМ",
    "Анализ данных и ИИ": "АДиИИ",
    "Алгебра, геометрия и теория дифференциальных уравнений": "АГиТДУ",
}

EXCLUDED_PREFIXES: Set[str] = {"ОРГ", "ИнЯз", "ПРОГ", "ИТиС", "ОПД", "ПФК"}

MEDIA_EXTENSIONS: Set[str] = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".pdf",
    ".mp4",
    ".wav",
    ".mp3",
}


class SubjectStats(TypedDict):
    """Статистика по конкретной учебной дисциплине."""

    notes_count: int
    terms_count: int
    has_textbook: bool
    has_canvas: bool


class VaultStats(TypedDict):
    """Сводная статистика хранилища Obsidian Vault."""

    total_notes: int
    total_terms: int
    subjects: Dict[str, SubjectStats]
    deadlines_count: int


class LinkAuditResult(TypedDict):
    """Результаты проверки целостности ссылок хранилища."""

    broken_links: List[str]
    untracked_subject_links: List[str]
    valid_links_count: int
    total_links_scanned: int


class SystemTelemetry(TypedDict):
    """Сведения об аппаратном ускорении и системных компонентах."""

    ffmpeg_available: bool
    ffmpeg_version: Optional[str]
    cuda_available: bool
    device_name: Optional[str]
    python_version: str


def clean_link_target(raw_link: str) -> str:
    """Нормализация цели wiki-ссылки с отсечением псевдонимов и якорей."""
    no_alias = raw_link.split("|")[0].strip()
    clean_target = no_alias.split("#")[0].strip()
    return clean_target


def is_media_link(target: str) -> bool:
    """Проверка, является ли цель ссылки вложением медиафайла."""
    target_lower = target.lower()
    return any(target_lower.endswith(ext) for ext in MEDIA_EXTENSIONS)


def _build_vault_index(vault_path: Path) -> Set[str]:
    """Построение множества имён всех существующих Markdown-заметок (без расширения)."""
    index: Set[str] = set()
    for root, _, files in os.walk(vault_path):
        for f in files:
            if f.endswith(".md"):
                index.add(Path(f).stem.lower())
    return index


def get_vault_stats(vault_path_str: str) -> VaultStats:
    """Сбор статистики по целевым дисциплинам в хранилище Obsidian Vault."""
    vault_path = Path(vault_path_str)
    stats: VaultStats = {
        "total_notes": 0,
        "total_terms": 0,
        "subjects": {},
        "deadlines_count": 0,
    }
    if not vault_path.is_dir():
        return stats

    for folder_name, _ in TARGET_SUBJECTS.items():
        subject_dir = vault_path / folder_name
        subj_stats = _collect_subject_stats(subject_dir)
        stats["subjects"][folder_name] = subj_stats
        stats["total_notes"] += subj_stats["notes_count"]
        stats["total_terms"] += subj_stats["terms_count"]

    stats["deadlines_count"] = _count_deadlines(vault_path / "Дедлайны и ДЗ.md")
    return stats


def _collect_subject_stats(subject_dir: Path) -> SubjectStats:
    """Подсчет конспектов, терминов, учебника и canvas для конкретной дисциплины."""
    if not subject_dir.is_dir():
        return {"notes_count": 0, "terms_count": 0, "has_textbook": False, "has_canvas": False}

    all_files = list(subject_dir.iterdir())
    terms_dir = subject_dir / "Термины"
    terms_count = len(list(terms_dir.glob("*.md"))) if terms_dir.is_dir() else 0

    root_notes = [f for f in all_files if f.is_file() and f.suffix == ".md" and not f.name.startswith("Учебник")]
    has_textbook = any(f.name.startswith("Учебник") for f in all_files)
    has_canvas = any(f.suffix == ".canvas" for f in all_files)

    return {
        "notes_count": len(root_notes),
        "terms_count": terms_count,
        "has_textbook": has_textbook,
        "has_canvas": has_canvas,
    }


def _count_deadlines(deadlines_file: Path) -> int:
    """Подсчёт количества задач в центральном файле дедлайнов."""
    if not deadlines_file.is_file():
        return 0
    try:
        content = deadlines_file.read_text(encoding="utf-8")
        return len(re.findall(r"-\s*\[[ xX]\]", content))
    except OSError:
        return 0


def verify_link_integrity(vault_path_str: str) -> LinkAuditResult:
    """Проверка всех wiki-ссылок хранилища на предмет битых и исключённых ссылок."""
    vault_path = Path(vault_path_str)
    result: LinkAuditResult = {
        "broken_links": [],
        "untracked_subject_links": [],
        "valid_links_count": 0,
        "total_links_scanned": 0,
    }
    if not vault_path.is_dir():
        return result

    known_notes = _build_vault_index(vault_path)
    pattern = re.compile(r"\[\[(.*?)\]\]")

    for root, _, files in os.walk(vault_path):
        if ".obsidian" in root or "Telegram" in root:
            continue
        for f in files:
            if not f.endswith(".md"):
                continue
            file_path = Path(root) / f
            _scan_file_links(file_path, pattern, known_notes, result)

    return result


def _strip_markdown_code(content: str) -> str:
    """Удаление блоков кода и инлайн-кода для исключения синтаксиса Pandas вида df[['col']]."""
    no_blocks = re.sub(r"```[\s\S]*?```", "", content)
    no_inline = re.sub(r"`[^`\n]+`", "", no_blocks)
    return no_inline


def _scan_file_links(
    file_path: Path,
    pattern: re.Pattern,
    known_notes: Set[str],
    result: LinkAuditResult,
) -> None:
    """Сканирование ссылок одного Markdown-файла."""
    try:
        raw_content = file_path.read_text(encoding="utf-8")
    except OSError:
        return

    content = _strip_markdown_code(raw_content)
    matches = pattern.findall(content)
    for raw in matches:
        target = clean_link_target(raw)
        if not target or is_media_link(target):
            continue

        result["total_links_scanned"] += 1
        _classify_link(target, file_path.name, known_notes, result)


def _classify_link(
    target: str,
    source_filename: str,
    known_notes: Set[str],
    result: LinkAuditResult,
) -> None:
    """Классификация ссылки: валидная, битая или ведущая на исключённую дисциплину."""
    prefix = target.split("-")[0].strip() if "-" in target else ""
    if prefix in EXCLUDED_PREFIXES:
        result["untracked_subject_links"].append(f"{source_filename} -> [[{target}]]")
        return

    target_key = target.lower()
    if target_key in known_notes:
        result["valid_links_count"] += 1
        return

    result["broken_links"].append(f"{source_filename} -> [[{target}]]")


def get_system_telemetry() -> SystemTelemetry:
    """Сбор сведений об аппаратном обеспечении, ускорении CUDA и статусе FFmpeg."""
    ffmpeg_ok, ffmpeg_ver = _detect_ffmpeg()
    cuda_ok, device_name = _detect_cuda()

    return {
        "ffmpeg_available": ffmpeg_ok,
        "ffmpeg_version": ffmpeg_ver,
        "cuda_available": cuda_ok,
        "device_name": device_name,
        "python_version": sys.version.split()[0],
    }


def _detect_ffmpeg() -> Tuple[bool, Optional[str]]:
    """Детекция исполняемого файла FFmpeg и получение строки версии."""
    if not shutil.which("ffmpeg"):
        return False, None
    try:
        proc = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if proc.returncode == 0 and proc.stdout:
            ver_line = proc.stdout.splitlines()[0]
            return True, ver_line
    except Exception:
        pass
    return True, "FFmpeg установлен"


def _detect_cuda() -> Tuple[bool, Optional[str]]:
    """Детекция доступности графического процессора с ускорением CUDA."""
    try:
        import ctranslate2

        cuda_count = ctranslate2.get_cuda_device_count()
        if cuda_count > 0:
            name = _get_nvidia_gpu_name()
            return True, name or f"NVIDIA GPU (CUDA устройств: {cuda_count})"
    except Exception:
        pass
    return False, None


def _get_nvidia_gpu_name() -> Optional[str]:
    """Получение имени видеокарты NVIDIA через nvidia-smi."""
    if not shutil.which("nvidia-smi"):
        return None
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None

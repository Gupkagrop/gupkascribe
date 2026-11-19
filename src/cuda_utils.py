"""Модуль безопасной инициализации динамических библиотек NVIDIA CUDA для среды Windows."""

import os
from pathlib import Path
from typing import List


def setup_cuda_dll_paths() -> List[str]:
    """Регистрация каталогов с бинарными библиотеками CUDA/cuDNN в системном окружении Windows.

    Returns:
        List[str]: Список успешно добавленных путей к бинарным библиотекам NVIDIA.
    """
    if os.name != "nt":
        return []

    project_root = Path(__file__).resolve().parent.parent
    site_packages = project_root / ".venv" / "Lib" / "site-packages" / "nvidia"
    if not site_packages.is_dir():
        return []

    added_paths: List[str] = []
    cuda_libs = ("cublas", "cudnn", "cuda_nvrtc")

    for lib in cuda_libs:
        bin_dir = site_packages / lib / "bin"
        if not bin_dir.is_dir():
            continue

        bin_str = str(bin_dir)
        os.environ["PATH"] = bin_str + os.pathsep + os.environ.get("PATH", "")
        try:
            os.add_dll_directory(bin_str)
            added_paths.append(bin_str)
        except (AttributeError, OSError):
            continue

    return added_paths

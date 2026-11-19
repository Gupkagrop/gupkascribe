"""Графический интерфейс автономной транскрибации видеозаписей лекций на базе CustomTkinter."""

import os
import shutil
import threading
from pathlib import Path
from tkinter import filedialog
from typing import List

import customtkinter as ctk

from src.cuda_utils import setup_cuda_dll_paths

setup_cuda_dll_paths()

from src.extract import ExtractionError, extract_content

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class TranscriberApp(ctk.CTk):
    """Главное окно приложения пакетной транскрибации лекций."""

    def __init__(self) -> None:
        super().__init__()
        self.title("🎙️ Умная Транскрибация Видео")
        self.geometry("820x720")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        self._init_paths_section()
        self._init_save_section()
        self._init_options_section()
        self._init_log_section()
        self._init_controls_section()

    def _init_paths_section(self) -> None:
        """Инициализация блока выбора видеофайлов."""
        self.frame_paths_header = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_paths_header.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")
        self.frame_paths_header.grid_columnconfigure(0, weight=1)

        self.label_paths = ctk.CTkLabel(
            self.frame_paths_header,
            text="Пути к видео:",
            font=("Segoe UI", 14, "bold"),
        )
        self.label_paths.grid(row=0, column=0, sticky="w")

        self.btn_browse_files = ctk.CTkButton(
            self.frame_paths_header,
            text="Выбрать видео...",
            width=130,
            command=self.browse_files,
        )
        self.btn_browse_files.grid(row=0, column=1, sticky="e")

        self.textbox_paths = ctk.CTkTextbox(self, height=90)
        self.textbox_paths.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

    def _init_save_section(self) -> None:
        """Инициализация блока указания целевого каталога сохранения."""
        self.label_save = ctk.CTkLabel(
            self,
            text="Папка для сохранения (txt и кадры):",
            font=("Segoe UI", 14, "bold"),
        )
        self.label_save.grid(row=2, column=0, padx=20, pady=(15, 5), sticky="w")

        self.frame_save = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_save.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.frame_save.grid_columnconfigure(0, weight=1)

        default_dir = os.path.join(os.path.expanduser("~"), "Documents", "Транскрибации")
        self.entry_save = ctk.CTkEntry(self.frame_save)
        self.entry_save.insert(0, default_dir)
        self.entry_save.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.btn_browse_folder = ctk.CTkButton(
            self.frame_save,
            text="Обзор...",
            width=130,
            command=self.browse_folder,
        )
        self.btn_browse_folder.grid(row=0, column=1)

    def _init_options_section(self) -> None:
        """Инициализация чекбоксов дополнительных опций."""
        self.checkbox_dl = ctk.CTkCheckBox(self, text="Дополнительно сохранить .txt в папку 'Загрузки'")
        self.checkbox_dl.select()
        self.checkbox_dl.grid(row=4, column=0, padx=20, pady=12, sticky="w")

    def _init_log_section(self) -> None:
        """Инициализация текстового поля для вывода логов процесса."""
        self.textbox_log = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.textbox_log.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")

    def _init_controls_section(self) -> None:
        """Инициализация кнопки запуска обработки."""
        self.btn_start = ctk.CTkButton(
            self,
            text="НАЧАТЬ ОБРАБОТКУ",
            font=("Segoe UI", 16, "bold"),
            height=42,
            command=self.start_processing,
        )
        self.btn_start.grid(row=6, column=0, padx=20, pady=20, sticky="ew")

    def browse_files(self) -> None:
        """Диалоговое окно множественного выбора видеофайлов."""
        filetypes = [
            ("Видео", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm"),
            ("Все файлы", "*.*"),
        ]
        files = filedialog.askopenfilenames(title="Выберите видеофайлы", filetypes=filetypes)
        if not files:
            return

        current_text = self.textbox_paths.get("1.0", "end-1c").strip()
        new_paths = "\n".join(files)
        text_to_set = f"{current_text}\n{new_paths}" if current_text else new_paths
        self.textbox_paths.delete("1.0", "end")
        self.textbox_paths.insert("end", text_to_set)

    def browse_folder(self) -> None:
        """Диалоговое окно выбора папки сохранения."""
        folder = filedialog.askdirectory(initialdir=self.entry_save.get())
        if not folder:
            return
        self.entry_save.delete(0, "end")
        self.entry_save.insert(0, folder)

    def _safe_log(self, message: str) -> None:
        """Потокобезопасная запись сообщения в лог-виджет главного потока."""
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

    def log_message(self, message: str) -> None:
        """Маршалинг логирования в главный цикл событий UI."""
        self.after(0, lambda: self._safe_log(message))

    def start_processing(self) -> None:
        """Валидация параметров и запуск фонового потока транскрибации."""
        raw_paths = self.textbox_paths.get("1.0", "end-1c").strip()
        save_dir = self.entry_save.get().strip()
        if not raw_paths:
            self._safe_log("❌ Ошибка: Выберите хотя бы один видеофайл!")
            return
        if not save_dir:
            self._safe_log("❌ Ошибка: Укажите папку для сохранения!")
            return

        video_paths = [p.strip().strip('"').strip("'") for p in raw_paths.split("\n") if p.strip()]
        save_to_downloads = bool(self.checkbox_dl.get() == 1)

        self._set_ui_busy_state(True)
        worker = threading.Thread(
            target=self._worker_loop,
            args=(video_paths, save_dir, save_to_downloads),
            daemon=True,
        )
        worker.start()

    def _set_ui_busy_state(self, busy: bool) -> None:
        """Управление доступностью кнопок запуска и очистки экрана."""
        if busy:
            self.btn_start.configure(state="disabled", text="ИДЕТ ОБРАБОТКА...")
            self.btn_browse_files.configure(state="disabled")
            self.textbox_log.configure(state="normal")
            self.textbox_log.delete("1.0", "end")
            self.textbox_log.configure(state="disabled")
            return

        self.btn_start.configure(state="normal", text="НАЧАТЬ ОБРАБОТКУ")
        self.btn_browse_files.configure(state="normal")

    def _worker_loop(self, video_paths: List[str], save_dir: str, save_to_downloads: bool) -> None:
        """Фоновый цикл пакетной обработки списка видеофайлов."""
        try:
            for v_path in video_paths:
                self._process_single_video(v_path, save_dir, save_to_downloads)
            self.log_message("\n🎉 Вся пакетная обработка успешно завершена!")
        except Exception as exc:
            self.log_message(f"❌ Критический сбой: {exc}")
        finally:
            self.after(0, lambda: self._set_ui_busy_state(False))

    def _process_single_video(self, video_path: str, save_dir: str, save_to_downloads: bool) -> None:
        """Обработка одной видеозаписи через единый движок extract_content."""
        if not os.path.isfile(video_path):
            self.log_message(f"Пропуск: файл не найден -> {video_path}")
            return

        basename = Path(video_path).stem
        self.log_message(f"\n--- Обработка: {basename} ---")

        try:
            out_dir = extract_content(
                video_path=video_path,
                custom_save_dir=save_dir,
                progress_cb=self.log_message,
            )
            if save_to_downloads:
                self._copy_to_downloads(out_dir, basename)
        except ExtractionError as err:
            self.log_message(f"❌ Ошибка при обработке {basename}: {err}")

    def _copy_to_downloads(self, out_dir: str, basename: str) -> None:
        """Копирование итогового текстового файла в системную папку 'Загрузки'."""
        transcript_src = os.path.join(out_dir, "transcript.txt")
        if not os.path.isfile(transcript_src):
            return

        downloads_dir = Path.home() / "Downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        target_path = downloads_dir / f"{basename}.txt"
        shutil.copy2(transcript_src, target_path)
        self.log_message(f"✅ Копия сохранена в Загрузки: {target_path}")


if __name__ == "__main__":
    app = TranscriberApp()
    app.mainloop()

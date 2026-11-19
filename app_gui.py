"""Современный графический интерфейс управления транскрибацией и мониторинга базы знаний Obsidian.

Реализован на базе CustomTkinter в соответствии с принципами эргономики UI/UX Dark Modern.
Включает пакетную транскрибацию, дашборд базы знаний и системную телеметрию.
"""

import os
import shutil
import subprocess
import threading
from pathlib import Path
from tkinter import filedialog
from typing import List, Optional

import customtkinter as ctk

from src.cuda_utils import setup_cuda_dll_paths

setup_cuda_dll_paths()

from src.extract import ExtractionError, extract_content
from src.vault_utils import (
    LinkAuditResult,
    SystemTelemetry,
    VaultStats,
    get_system_telemetry,
    get_vault_stats,
    verify_link_integrity,
)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class TranscriberApp(ctk.CTk):
    """Главное окно десктопного пульта управления транскрибацией и базой знаний."""

    def __init__(self) -> None:
        super().__init__()
        self.title("🎙️ Obsidian Lecture Studio & Knowledge Base Automator")
        self.geometry("920x780")
        self.minsize(860, 680)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_tabs()
        self._refresh_telemetry_async()

    def _build_header(self) -> None:
        """Построение верхнего информационного баннера с индикацией режима работы."""
        self.header_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.header_frame.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            self.header_frame,
            text="🎙️ Obsidian Lecture Studio (AI-First Auxiliary Console)",
            font=("Segoe UI", 16, "bold"),
            text_color="#F8FAFC",
        )
        title_lbl.grid(row=0, column=0, padx=16, pady=(10, 2), sticky="w")

        subtitle_lbl = ctk.CTkLabel(
            self.header_frame,
            text="Первичный режим: AI-агенты Antigravity | Вспомогательный режим: Интерактивный пульт пользователя",
            font=("Segoe UI", 11),
            text_color="#94A3B8",
        )
        subtitle_lbl.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

    def _build_tabs(self) -> None:
        """Инициализация модульной навигации по вкладкам."""
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, padx=16, pady=(6, 12), sticky="nsew")

        self.tab_transcribe = self.tabview.add("🎙️ Транскрибатор")
        self.tab_vault = self.tabview.add("📚 База знаний (Obsidian)")
        self.tab_telemetry = self.tabview.add("⚙️ Системная телеметрия")

        self._build_transcription_tab(self.tab_transcribe)
        self._build_vault_tab(self.tab_vault)
        self._build_telemetry_tab(self.tab_telemetry)

    # -------------------------------------------------------------------------
    # Вкладка 1: Пакетная транскрибация
    # -------------------------------------------------------------------------
    def _build_transcription_tab(self, tab: ctk.CTkFrame) -> None:
        """Построение интерфейса вкладки пакетной транскрибации."""
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(3, weight=1)

        self._build_file_queue_card(tab, row=0)
        self._build_settings_card(tab, row=1)
        self._build_action_card(tab, row=2)
        self._build_terminal_card(tab, row=3)

    def _build_file_queue_card(self, tab: ctk.CTkFrame, row: int) -> None:
        """Карточка управления очередью видеофайлов."""
        card = ctk.CTkFrame(tab, fg_color="#1E293B", corner_radius=8)
        card.grid(row=row, column=0, padx=10, pady=6, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.grid(row=0, column=0, padx=12, pady=(8, 4), sticky="ew")
        top_row.grid_columnconfigure(0, weight=1)

        self.lbl_queue_count = ctk.CTkLabel(
            top_row,
            text="Очередь видеозаписей (0 файлов):",
            font=("Segoe UI", 13, "bold"),
            text_color="#F8FAFC",
        )
        self.lbl_queue_count.grid(row=0, column=0, sticky="w")

        btn_add = ctk.CTkButton(top_row, text="➕ Выбрать видео...", width=140, command=self._browse_videos)
        btn_add.grid(row=0, column=1, padx=(6, 4), sticky="e")

        btn_clear = ctk.CTkButton(
            top_row,
            text="🧹 Очистить",
            width=90,
            fg_color="#334155",
            hover_color="#475569",
            command=self._clear_queue,
        )
        btn_clear.grid(row=0, column=2, padx=(4, 0), sticky="e")

        self.txt_queue = ctk.CTkTextbox(card, height=75, font=("Consolas", 11))
        self.txt_queue.grid(row=1, column=0, padx=12, pady=(4, 10), sticky="ew")

    def _build_settings_card(self, tab: ctk.CTkFrame, row: int) -> None:
        """Карточка настройки параметров транскрибации и каталога сохранения."""
        card = ctk.CTkFrame(tab, fg_color="#1E293B", corner_radius=8)
        card.grid(row=row, column=0, padx=10, pady=6, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        lbl_model = ctk.CTkLabel(card, text="Модель Whisper:", font=("Segoe UI", 12, "bold"))
        lbl_model.grid(row=0, column=0, padx=12, pady=6, sticky="w")

        model_opts = [
            "small (Сбалансированная / Рекомендуется)",
            "base (Быстрая / Черновая)",
            "medium (Высокая точность)",
            "large-v3 (Максимальное качество)",
        ]
        self.combo_model = ctk.CTkComboBox(card, values=model_opts, width=320)
        self.combo_model.set(model_opts[0])
        self.combo_model.grid(row=0, column=1, padx=12, pady=6, sticky="w")

        lbl_dir = ctk.CTkLabel(card, text="Папка сохранения:", font=("Segoe UI", 12, "bold"))
        lbl_dir.grid(row=1, column=0, padx=12, pady=6, sticky="w")

        dir_frame = ctk.CTkFrame(card, fg_color="transparent")
        dir_frame.grid(row=1, column=1, padx=12, pady=6, sticky="ew")
        dir_frame.grid_columnconfigure(0, weight=1)

        default_dir = str(Path.home() / "Documents" / "Транскрибации")
        self.entry_save_dir = ctk.CTkEntry(dir_frame)
        self.entry_save_dir.insert(0, default_dir)
        self.entry_save_dir.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        btn_browse_dir = ctk.CTkButton(dir_frame, text="Обзор...", width=90, command=self._browse_save_dir)
        btn_browse_dir.grid(row=0, column=1)

        opts_frame = ctk.CTkFrame(card, fg_color="transparent")
        opts_frame.grid(row=2, column=0, columnspan=2, padx=12, pady=(4, 8), sticky="w")

        self.cb_downloads = ctk.CTkCheckBox(opts_frame, text="Сохранять копию .txt в 'Загрузки'")
        self.cb_downloads.select()
        self.cb_downloads.grid(row=0, column=0, padx=(0, 20), sticky="w")

        self.cb_scene = ctk.CTkCheckBox(opts_frame, text="Scene Change Detection (Умная нарезка слайдов)")
        self.cb_scene.select()
        self.cb_scene.grid(row=0, column=1, sticky="w")

    def _build_action_card(self, tab: ctk.CTkFrame, row: int) -> None:
        """Кнопка запуска обработки и индикатор текущего прогресса."""
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.grid(row=row, column=0, padx=10, pady=4, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.btn_run = ctk.CTkButton(
            frame,
            text="🚀 НАЧАТЬ ПАКЕТНУЮ ОБРАБОТКУ",
            font=("Segoe UI", 15, "bold"),
            height=40,
            fg_color="#22C55E",
            hover_color="#16A34A",
            text_color="#0F172A",
            command=self._start_transcription_worker,
        )
        self.btn_run.grid(row=0, column=0, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(frame, height=6)
        self.progress_bar.set(0.0)
        self.progress_bar.grid(row=1, column=0, pady=(6, 0), sticky="ew")

    def _build_terminal_card(self, tab: ctk.CTkFrame, row: int) -> None:
        """Интерактивный терминал логов с быстрыми действиями."""
        card = ctk.CTkFrame(tab, fg_color="#0F172A", corner_radius=8)
        card.grid(row=row, column=0, padx=10, pady=(6, 8), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(card, fg_color="transparent")
        bar.grid(row=0, column=0, padx=8, pady=4, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(bar, text="📋 Журнал выполнения:", font=("Segoe UI", 12, "bold"), text_color="#94A3B8")
        lbl.grid(row=0, column=0, sticky="w")

        btn_copy = ctk.CTkButton(bar, text="Копировать", width=80, height=24, command=self._copy_log)
        btn_copy.grid(row=0, column=1, padx=4)

        btn_open = ctk.CTkButton(bar, text="Открыть папку", width=100, height=24, command=self._open_output_dir)
        btn_open.grid(row=0, column=2, padx=4)

        btn_clr = ctk.CTkButton(bar, text="Очистить", width=80, height=24, command=self._clear_log)
        btn_clr.grid(row=0, column=3, padx=4)

        self.txt_log = ctk.CTkTextbox(card, state="disabled", font=("Consolas", 11), text_color="#E2E8F0")
        self.txt_log.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")

    # -------------------------------------------------------------------------
    # Вкладка 2: База знаний (Obsidian Vault Dashboard)
    # -------------------------------------------------------------------------
    def _build_vault_tab(self, tab: ctk.CTkFrame) -> None:
        """Построение вкладки мониторинга и аудита базы знаний."""
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        top_card = ctk.CTkFrame(tab, fg_color="#1E293B", corner_radius=8)
        top_card.grid(row=0, column=0, padx=10, pady=8, sticky="ew")
        top_card.grid_columnconfigure(1, weight=1)

        lbl_vault = ctk.CTkLabel(top_card, text="Путь к Vault:", font=("Segoe UI", 12, "bold"))
        lbl_vault.grid(row=0, column=0, padx=12, pady=8, sticky="w")

        default_vault = str(Path.home() / "Documents" / "Obsidian Vault")
        self.entry_vault_path = ctk.CTkEntry(top_card)
        self.entry_vault_path.insert(0, default_vault)
        self.entry_vault_path.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        btn_open_vault = ctk.CTkButton(top_card, text="📂 Открыть в проводнике", width=170, command=self._open_vault_folder)
        btn_open_vault.grid(row=0, column=2, padx=10, pady=8)

        self.frame_disciplines = ctk.CTkFrame(tab, fg_color="transparent")
        self.frame_disciplines.grid(row=1, column=0, padx=10, pady=4, sticky="ew")
        for i in range(4):
            self.frame_disciplines.grid_columnconfigure(i, weight=1)

        self.discipline_cards: List[ctk.CTkFrame] = []
        self._init_discipline_cards()

        audit_card = ctk.CTkFrame(tab, fg_color="#1E293B", corner_radius=8)
        audit_card.grid(row=2, column=0, padx=10, pady=8, sticky="nsew")
        audit_card.grid_columnconfigure(0, weight=1)
        audit_card.grid_rowconfigure(1, weight=1)

        audit_bar = ctk.CTkFrame(audit_card, fg_color="transparent")
        audit_bar.grid(row=0, column=0, padx=12, pady=8, sticky="ew")
        audit_bar.grid_columnconfigure(0, weight=1)

        self.lbl_audit_status = ctk.CTkLabel(
            audit_bar,
            text="Аудит связей (Zero Broken Links Protocol): Нажмите для запуска проверки",
            font=("Segoe UI", 13, "bold"),
            text_color="#F8FAFC",
        )
        self.lbl_audit_status.grid(row=0, column=0, sticky="w")

        self.btn_run_audit = ctk.CTkButton(
            audit_bar,
            text="🔍 Запустить аудит связей",
            width=180,
            fg_color="#0288D1",
            hover_color="#0277BD",
            command=self._start_audit_async,
        )
        self.btn_run_audit.grid(row=0, column=1, sticky="e")

        self.txt_audit_log = ctk.CTkTextbox(audit_card, state="disabled", font=("Consolas", 11))
        self.txt_audit_log.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="nsew")

    def _init_discipline_cards(self) -> None:
        """Создание четырёх визуальных карточек для целевых дисциплин."""
        disciplines = [
            ("МатАнализ", "МатАн", "#0288D1"),
            ("Дискретная мат-ка", "ДМ", "#7C3AED"),
            ("Анализ данных и ИИ", "АДиИИ", "#22C55E"),
            ("АГиТДУ", "АГиТДУ", "#F59E0B"),
        ]
        self.card_labels: List[ctk.CTkLabel] = []

        for idx, (title, prefix, color) in enumerate(disciplines):
            card = ctk.CTkFrame(self.frame_disciplines, fg_color="#1E293B", corner_radius=8)
            card.grid(row=0, column=idx, padx=4, pady=4, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)

            t_lbl = ctk.CTkLabel(card, text=f"📘 {title}", font=("Segoe UI", 12, "bold"), text_color=color)
            t_lbl.grid(row=0, column=0, padx=8, pady=(8, 2), sticky="w")

            p_lbl = ctk.CTkLabel(card, text=f"Префикс: {prefix}", font=("Segoe UI", 10), text_color="#94A3B8")
            p_lbl.grid(row=1, column=0, padx=8, pady=0, sticky="w")

            stat_lbl = ctk.CTkLabel(card, text="Загрузка...", font=("Segoe UI", 11), text_color="#F8FAFC")
            stat_lbl.grid(row=2, column=0, padx=8, pady=(4, 8), sticky="w")
            self.card_labels.append(stat_lbl)

    # -------------------------------------------------------------------------
    # Вкладка 3: Телеметрия системы
    # -------------------------------------------------------------------------
    def _build_telemetry_tab(self, tab: ctk.CTkFrame) -> None:
        """Построение панели системной телеметрии и проверки аппаратного ускорения."""
        tab.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(tab, fg_color="#1E293B", corner_radius=8)
        card.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        self.lbl_telem_ffmpeg = ctk.CTkLabel(card, text="FFmpeg: Проверка...", font=("Segoe UI", 13))
        self.lbl_telem_ffmpeg.grid(row=0, column=0, columnspan=2, padx=14, pady=8, sticky="w")

        self.lbl_telem_gpu = ctk.CTkLabel(card, text="GPU Ускорение: Проверка...", font=("Segoe UI", 13))
        self.lbl_telem_gpu.grid(row=1, column=0, columnspan=2, padx=14, pady=8, sticky="w")

        self.lbl_telem_python = ctk.CTkLabel(card, text="Среда Python: Проверка...", font=("Segoe UI", 13))
        self.lbl_telem_python.grid(row=2, column=0, columnspan=2, padx=14, pady=8, sticky="w")

        self.lbl_telem_agents = ctk.CTkLabel(
            card,
            text="ИИ-агенты: Готовность подтверждена (.agents/skills/lecture-processor)",
            font=("Segoe UI", 13),
            text_color="#22C55E",
        )
        self.lbl_telem_agents.grid(row=3, column=0, columnspan=2, padx=14, pady=8, sticky="w")

        btn_refresh = ctk.CTkButton(
            card,
            text="🔄 Обновить телеметрию",
            width=160,
            command=self._refresh_telemetry_async,
        )
        btn_refresh.grid(row=4, column=0, padx=14, pady=12, sticky="w")

    # -------------------------------------------------------------------------
    # Обработчики событий и асинхронные рабочие потоки
    # -------------------------------------------------------------------------
    def _browse_videos(self) -> None:
        """Диалог множественного выбора видеофайлов с обновлением счетчика."""
        types = [("Видеофайлы", "*.mp4 *.mkv *.avi *.mov *.webm *.flv"), ("Все файлы", "*.*")]
        files = filedialog.askopenfilenames(title="Выберите видеозаписи лекций", filetypes=types)
        if not files:
            return

        current = self.txt_queue.get("1.0", "end-1c").strip()
        joined = "\n".join(files)
        updated = f"{current}\n{joined}" if current else joined
        self.txt_queue.delete("1.0", "end")
        self.txt_queue.insert("end", updated)

        lines = [line for line in updated.splitlines() if line.strip()]
        self.lbl_queue_count.configure(text=f"Очередь видеозаписей ({len(lines)} файлов):")

    def _clear_queue(self) -> None:
        """Очистка списка очереди видеофайлов."""
        self.txt_queue.delete("1.0", "end")
        self.lbl_queue_count.configure(text="Очередь видеозаписей (0 файлов):")

    def _browse_save_dir(self) -> None:
        """Выбор целевой папки сохранения."""
        fld = filedialog.askdirectory(initialdir=self.entry_save_dir.get())
        if fld:
            self.entry_save_dir.delete(0, "end")
            self.entry_save_dir.insert(0, fld)

    def _safe_append_log(self, text: str) -> None:
        """Потокобезопасный вывод логов в консоль главного потока."""
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", text + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _log_msg(self, msg: str) -> None:
        """Маршалинг сообщения в UI-поток."""
        self.after(0, lambda: self._safe_append_log(msg))

    def _clear_log(self) -> None:
        """Очистка терминального виджета."""
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")

    def _copy_log(self) -> None:
        """Копирование текста лога в буфер обмена."""
        content = self.txt_log.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)

    def _open_output_dir(self) -> None:
        """Открытие папки сохранения в Проводнике Windows."""
        d = self.entry_save_dir.get().strip()
        if os.path.isdir(d):
            os.startfile(d)

    def _open_vault_folder(self) -> None:
        """Открытие папки хранилища Obsidian в Проводнике Windows."""
        v = self.entry_vault_path.get().strip()
        if os.path.isdir(v):
            os.startfile(v)

    def _start_transcription_worker(self) -> None:
        """Запуск фонового процесса транскрибации."""
        raw = self.txt_queue.get("1.0", "end-1c").strip()
        save_dir = self.entry_save_dir.get().strip()
        paths = [p.strip().strip('"').strip("'") for p in raw.splitlines() if p.strip()]
        if not paths:
            self._safe_append_log("❌ Ошибка: Очередь видео пуста! Выберите хотя бы один файл.")
            return

        model_key = self.combo_model.get().split()[0]
        save_dl = bool(self.cb_downloads.get() == 1)

        self._set_processing_busy(True)
        worker = threading.Thread(
            target=self._run_transcription_pipeline,
            args=(paths, save_dir, model_key, save_dl),
            daemon=True,
        )
        worker.start()

    def _set_processing_busy(self, busy: bool) -> None:
        """Управление состоянием интерфейса во время обработки."""
        if busy:
            self.btn_run.configure(state="disabled", text="⏳ ИДЕТ ОБРАБОТКА...")
            self.progress_bar.set(0.1)
            return
        self.btn_run.configure(state="normal", text="🚀 НАЧАТЬ ПАКЕТНУЮ ОБРАБОТКУ")
        self.progress_bar.set(1.0)

    def _run_transcription_pipeline(
        self,
        paths: List[str],
        save_dir: str,
        model_size: str,
        save_to_dl: bool,
    ) -> None:
        """Фоновый цикл обработки видеозаписей с вызовом единого сервисного ядра."""
        try:
            total = len(paths)
            for idx, p in enumerate(paths, start=1):
                progress = idx / total
                self.after(0, lambda pr=progress: self.progress_bar.set(pr))
                self._process_single_item(p, save_dir, save_to_dl)
            self._log_msg("\n🎉 Вся очередь успешно обработана!")
        except Exception as exc:
            self._log_msg(f"❌ Критический сбой пайплайна: {exc}")
        finally:
            self.after(0, lambda: self._set_processing_busy(False))

    def _process_single_item(self, video_path: str, save_dir: str, save_to_dl: bool) -> None:
        """Обработка отдельного видеофайла."""
        if not os.path.isfile(video_path):
            self._log_msg(f"Пропуск: файл не найден -> {video_path}")
            return

        basename = Path(video_path).stem
        self._log_msg(f"\n--- Обработка: {basename} ---")
        try:
            out_dir = extract_content(
                video_path=video_path,
                custom_save_dir=save_dir,
                progress_cb=self._log_msg,
            )
            if save_to_dl:
                self._copy_txt_to_downloads(out_dir, basename)
        except ExtractionError as err:
            self._log_msg(f"❌ Ошибка при обработке {basename}: {err}")

    def _copy_txt_to_downloads(self, out_dir: str, basename: str) -> None:
        """Копирование итогового транскрипта в системную папку 'Загрузки'."""
        src = os.path.join(out_dir, "transcript.txt")
        if not os.path.isfile(src):
            return
        dl = Path.home() / "Downloads"
        dl.mkdir(parents=True, exist_ok=True)
        dst = dl / f"{basename}.txt"
        shutil.copy2(src, dst)
        self._log_msg(f"✅ Копия транскрипта сохранена в Загрузки: {dst}")

    # -------------------------------------------------------------------------
    # Асинхронный аудит хранилища и телеметрия
    # -------------------------------------------------------------------------
    def _start_audit_async(self) -> None:
        """Асинхронный запуск проверки связей базы знаний."""
        vault = self.entry_vault_path.get().strip()
        self.lbl_audit_status.configure(text="Выполняется сканирование связей хранилища...", text_color="#F59E0B")
        self.btn_run_audit.configure(state="disabled")

        def _worker() -> None:
            stats = get_vault_stats(vault)
            audit = verify_link_integrity(vault)
            self.after(0, lambda: self._apply_audit_results(stats, audit))

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_audit_results(self, stats: VaultStats, audit: LinkAuditResult) -> None:
        """Применение результатов аудита в главном потоке интерфейса."""
        self.btn_run_audit.configure(state="normal")
        broken_count = len(audit["broken_links"])
        untracked_count = len(audit["untracked_subject_links"])

        if broken_count == 0 and untracked_count == 0:
            self.lbl_audit_status.configure(
                text=f"✅ База идеальна: 0 битых ссылок из {audit['total_links_scanned']} проверенных!",
                text_color="#22C55E",
            )
        else:
            self.lbl_audit_status.configure(
                text=f"⚠️ Обнаружены дефекты: битых={broken_count}, посторонних={untracked_count}",
                text_color="#EF4444",
            )

        self._render_discipline_stats(stats)
        self._render_audit_report(stats, audit)

    def _render_discipline_stats(self, stats: VaultStats) -> None:
        """Обновление показателей на карточках активных дисциплин."""
        subjs = [
            "Математика Матанализ",
            "Дискретная математика",
            "Анализ данных и ИИ",
            "Алгебра, геометрия и теория дифференциальных уравнений",
        ]
        for idx, key in enumerate(subjs):
            if idx >= len(self.card_labels):
                break
            st = stats["subjects"].get(key, {"notes_count": 0, "terms_count": 0})
            self.card_labels[idx].configure(text=f"Конспектов: {st['notes_count']} | Терминов: {st['terms_count']}")

    def _render_audit_report(self, stats: VaultStats, audit: LinkAuditResult) -> None:
        """Отрисовка подробного текстового отчета аудита."""
        self.txt_audit_log.configure(state="normal")
        self.txt_audit_log.delete("1.0", "end")

        lines = [
            f"=== АУДИТ БАЗЫ ЗНАНИЙ OBSIDIAN VAULT ===",
            f"Всего конспектов: {stats['total_notes']} | Всего терминов: {stats['total_terms']}",
            f"Всего проверено ссылок: {audit['total_links_scanned']}",
            f"Валидных ссылок: {audit['valid_links_count']}",
            f"Битых ссылок: {len(audit['broken_links'])}",
            f"Ссылок на исключенные предметы: {len(audit['untracked_subject_links'])}",
            f"Активных задач в Дедлайны и ДЗ.md: {stats['deadlines_count']}\n",
        ]
        if audit["broken_links"]:
            lines.append("❌ Список битых ссылок:")
            lines.extend(f"  • {b}" for b in audit["broken_links"])
        else:
            lines.append("✅ Все внутренние ссылки указывают на существующие файлы.")

        self.txt_audit_log.insert("end", "\n".join(lines))
        self.txt_audit_log.configure(state="disabled")

    def _refresh_telemetry_async(self) -> None:
        """Асинхронный опрос системных ресурсов."""
        def _worker() -> None:
            data = get_system_telemetry()
            self.after(0, lambda: self._apply_telemetry(data))

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_telemetry(self, data: SystemTelemetry) -> None:
        """Отображение телеметрии в UI."""
        if data["ffmpeg_available"]:
            self.lbl_telem_ffmpeg.configure(
                text=f"✅ FFmpeg: Доступен ({data['ffmpeg_version']})",
                text_color="#22C55E",
            )
        else:
            self.lbl_telem_ffmpeg.configure(text="❌ FFmpeg: Не найден в системном PATH!", text_color="#EF4444")

        if data["cuda_available"]:
            self.lbl_telem_gpu.configure(
                text=f"⚡ GPU Ускорение: Активно ({data['device_name'] or 'NVIDIA CUDA'})",
                text_color="#22C55E",
            )
        else:
            self.lbl_telem_gpu.configure(
                text="⚠️ GPU Ускорение: Не обнаружено (Активен режим CPU int8)",
                text_color="#F59E0B",
            )

        self.lbl_telem_python.configure(
            text=f"🐍 Среда Python: {data['python_version']} (uv пакетный менеджер)",
            text_color="#F8FAFC",
        )


if __name__ == "__main__":
    app = TranscriberApp()
    app.mainloop()

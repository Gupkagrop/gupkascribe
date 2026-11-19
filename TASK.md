# Project Living State Tracker (TASK.md)

> [!NOTE]
> **Назначение файла:** Живой журнал состояния проекта для сквозной памяти между чатами ("Zero-Context-Amnesia").
> Обновляется агентом в конце каждого выполненного этапа или задачи (Stage 4 SOP).

## 1. Project Health & Stage
- **Current Phase:** Phase 3: Production Readiness & Zero-Setup Deployment
- **Status:** Ready / Production Stable
- **Last Updated:** 2026-11-19 17:55
- **Active Branch:** `master`
- **Project Name:** GupkaScribe Studio (`gupkascribe` v0.2.0)
- **Architecture:** AI-First Platform (Tier 1: ИИ-агенты Antigravity; Tier 2: Вспомогательный десктопный GUI на CustomTkinter)

## 2. Completed Milestones
- [x] **[2026-11-19] Унификация шаблонов и стандартов:** Приведение `.gitignore`, `.repomixignore`, `AGENTS.md` и `TASK.md` в 100% соответствие шаблонам `~/.gemini/config/templates`. (Commit: `46fde76`)
- [x] **[2026-11-19] Ребрендинг GupkaScribe Studio:** Переименование репозитория GitHub в `Gupkagrop/gupkascribe`, обновление удалённых связей и метаданных. (Commit: `3642d20`)
- [x] **[2026-11-19] Zero-Setup Deployment & FFmpeg Auto-Install:** Встроенный портативный FFmpeg через `imageio-ffmpeg`, адаптивный запуск `Запустить_Транскрибатор.bat` и fallback GPU CUDA ➔ CPU int8. (Commit: `dda8896`)
- [x] **[2026-11-19] Информативное логирование Whisper:** Определение наличия весов модели в кэше Hugging Face и явное оповещение при автозагрузке. (Commit: `6988b75`)
- [x] **[2026-11-19] Универсализация движка под любые курсы:** Динамическое обнаружение дисциплин в хранилище и поддержка любых лекций в воркспейс-скилах. (Commit: `0a02fed`)
- [x] **[2026-11-19] Потокобезопасный CustomTkinter GUI:** Архитектура `queue.Queue` с поллером в главном потоке для устранения падений Tkinter. (Commit: `0a02fed`)
- [x] **[2026-11-19] Воркспейс-скилы агентов:** Разработаны скилы `.agents/skills/lecture-processor` и `.agents/skills/vault-curator`. (Commit: `938acac`)
- [x] **[2026-11-19] Чистка скоупа дисциплин Obsidian:** Удаление папки `Основы российской государственности` и изоляция дедлайнов. (Commit: `9c483ab`)

## 3. Active Task (Current Focus)
- **Feature:** Полная валидация соответствия шаблонам конфигурации и финальная приёмка готовности проекта
- **Target Files:**
  - `.gitignore`
  - `.repomixignore`
  - `AGENTS.md`
  - `TASK.md`
  - `tests/test_smoke.py`
- **Verification Plan:** `uv run python -m unittest discover tests` (19+ тестов) и `npx repomix`

## 4. Next Immediate Steps (Backlog)
- [ ] Пакетная обработка новых записей университетских лекций через агентский скилл `lecture-processor` или GUI.
- [ ] Автоматический аудит графа связей хранилища Obsidian через `vault-curator` при добавлении новых конспектов.
- [ ] Генерация новых предметных холстов Canvas для дисциплин семестра.

## 5. Architectural Decisions & Blockers
- **Decisions Log:**
  - `2026-11-19`: Принято имя **GupkaScribe Studio** (`gupkascribe`), объединяющее никнейм Дениса (`gupka` — метафора «впитывать знания как губка») и `scribe` (академический писарь/стенографист).
  - `2026-11-19`: Интегрирован `imageio-ffmpeg` для поставки скомпилированного бинарника `ffmpeg.exe` «из коробки» без необходимости ручной установки пользователем.
  - `2026-11-19`: Зафиксирована очередь `queue.Queue` и поллер `self._start_queue_poller()` для 100% защиты от падений Tkinter при асинхронных вызовах из воркеров.
  - `2026-11-19`: Реализован гибридный инференс: автоматический переход на CPU `int8` при отсутствии видеокарты NVIDIA или драйвера CUDA 12.
- **Known Blockers / Warnings:**
  - None currently.

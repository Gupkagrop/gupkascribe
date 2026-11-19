# Project Operational Guidelines (AGENTS.md)

> [!NOTE]
> **Назначение файла:** Контракт правил и архитектурных стандартов для агентов в данном проекте (стандарт 2026 года).
> Агент считывает этот файл автоматически при открытии рабочей области.

## 1. Project Overview & Tech Stack
- **Project Name:** GupkaScribe Studio (`gupkascribe` v0.2.0)
- **Target Platform:** Windows Desktop / AI-First Knowledge Base Automation
- **Stack:** Python 3.12+, CustomTkinter (Dark Theme), faster-whisper (CTranslate2, NVIDIA CUDA 12, cuDNN 9), ffmpeg-python / imageio-ffmpeg, Obsidian Vault (Markdown, KaTeX LaTeX, Canvas JSON, Zettelkasten)
- **Package Manager & Runtimes:** `uv` (Astral), Python venv, Git

## 2. Standard Commands (Harness Sensors)
- **Install Dependencies:** `uv sync` (или `uv pip install -r requirements.txt`)
- **Build / Compile:** `uv run python -m py_compile app_gui.py src/*.py tests/*.py`
- **Run Development:** `uv run python app_gui.py` (или `Запустить_Транскрибатор.bat`)
- **Run Tests:** `uv run python -m unittest discover tests`
- **Linter & Typecheck:** `uv run python -m py_compile app_gui.py src/*.py`
- **AST Codebase Map:** `npx repomix`
- **CLI Media Extraction:** `uv run python src/extract.py "<video_path>"`

## 3. Session Continuity & Orientation Protocol
- **Every new chat/task MUST start with:**
  1. `git status` and `git log -n 5 --oneline` (review recent commits).
  2. Reading `TASK.md` in repository root to determine active phase, immediate backlog, and recent decisions.
  3. Reading `repomix-output.xml` if inspecting repository architecture.

## 4. Coding & Architecture Standards (Code Standards & Quality Gates)
- **Early returns:** keep nesting depth $\le 3$.
- **Functions:** $\le 30-40$ lines. Split complex workflows into clean helpers.
- **Strict typing:** zero implicit `any` or loose types; explicit typing everywhere.
- **No placeholders:** zero `// TODO` or unverified mock stubs. Complete production code only.
- **Language policy:**
  - All code identifiers (variables, functions, classes, modules) strictly in English.
  - All code comments, docstrings, and in-file technical annotations strictly in Russian.
  - All Git commit messages, PR titles/descriptions strictly in Russian (`feat: ...`, `fix: ...`, `chore: ...`).
  - Chat responses strictly in Russian.
- **Secrets safety:** zero hardcoded secrets: use `.env` files.

## 5. Pre-Commit Checklist
- [ ] Automated tests run and pass green (`uv run python -m unittest discover tests`).
- [ ] Static analyzer / syntax compiler passes with zero warnings (`py_compile`).
- [ ] `TASK.md` updated with completed milestone and commit hash.
- [ ] Conventional Commit authored in Russian (e.g. `feat: ...`).

## 6. Architecture & Pipeline Rules (AI-First Philosophy & Obsidian Vault)
Проект строится на строгой двухуровневой иерархии:
1. **Tier 1 (Core — Первичная роль):** Автономная фабрика конспектов и базы знаний под управлением ИИ-агентов (Antigravity / Gemini CLI). Все регламенты, утилиты и CLI-скрипты оптимизированы для машинного вызова, точечного анализа кадров по таймкодам, пополнения Zettelkasten, актуализации учебников и Canvas.
   - **Специализированные скилы агента:**
     * `.agents/skills/lecture-processor/SKILL.md` — сквозная обработка лекций для любых дисциплин.
     * `.agents/skills/vault-curator/SKILL.md` — аудит связей и поддержание целостности графа.
2. **Tier 2 (Auxiliary — Вторичная роль):** Премиальный десктопный GUI (`app_gui.py`) на `CustomTkinter` для ручной пакетной транскрибации и интерактивного мониторинга базы пользователем.

Конвейер обработки лекций подробно задокументирован в модульных спецификациях:
- **[Конвейер обработки лекций](file:///C:/Users/denis/Documents/antigravity/recording/docs/architecture/pipeline.md)**
- **[Спецификация Obsidian Vault](file:///C:/Users/denis/Documents/antigravity/recording/docs/architecture/obsidian_vault.md)**

### Ключевые инварианты конвейера:
1. **Строгая точность (Strict Fidelity):** фиксация только реальных тезисов преподавателя. Запрет на додумывание определений.
2. **Фильтрация "воды" (Remove Fluff):** удаление посторонних тем, оффтопа и повторов при сохранении максимальной плотности полезной теории.
3. **Исключение для математики:** для дисциплин с формулами (Алгебра, Матанализ, Дискретная математика) агент обязан добавлять понятные пояснения и примеры.
4. **Мультимодальный анализ слайдов (Multimodal Inspection):** агент ОБЯЗАН открывать и изучать кадры из `cache/<video>/frames/` через `read_file` (особенно при математических выкладках, коде, таблицах и ссылках лектора на экран).
5. **Запрет встраивания "сырых" картинок:** запрещено вставлять скриншоты в саму итоговую заметку (`![[frame.jpg]]`). Формулы и доказательства со слайдов переводятся в академический KaTeX LaTeX (`$$...$$`), схемы — в Mermaid, код — в блоки кода.
6. **Сквозная актуализация:** каждая обработанная лекция дополняет Zettelkasten-термины (`Термины/`), генерирует лекционную заметку, пополняет монолитный `Учебник - <Subject>.md`, обновляет граф `<Subject>.canvas` и фиксируется в `PROCESSED_VIDEOS.md`.
7. **Автоматическое переименование:** видеозаписи с неинформативными именами дат (например, `2026-09-14 10-37-07.mp4`) после анализа переименовываются в читаемый вид (например, `Математика (Матанализ). Лекция 1.mp4`).
8. **Аббревиатуры дисциплин в именах заметок:** все заметки лекций и практик ОБЯЗАНЫ начинаться с префикса `<АББРЕВИАТУРА> - ...` (`АДиИИ`, `АГиТДУ`, `ДМ`, `МатАн`). Подробнее в [obsidian_vault.md](file:///C:/Users/denis/Documents/antigravity/recording/docs/architecture/obsidian_vault.md).
9. **Синхронная миграция без потери связей:** при первом контакте с дисциплиной агент аккуратно приводит старые заметки к стандарту аббревиатур, каскадно обновляя ВСЕ входящие ссылки `[[...]]` в терминах, учебниках, графах Canvas и реестре без единой битой ссылки.
10. **Активное припоминание (Active Recall):** каждая лекция обязана завершаться разделом `## ❓ Вопросы для экзамена и самопроверки` с краткими тезисными ответами под сворачиваемым спойлером `> [!question]- Ответ`.
11. **Фиксация дедлайнов и ДЗ (Полная изоляция от графа):** озвученные преподавателем домашние задания и дедлайны фиксируются в централизованном файле `Дедлайны и ДЗ.md`. **Строгий запрет wiki-ссылок [[...]] в обе стороны:**
    - Запрещено ставить ссылки `[[Дедлайны и ДЗ]]` из любых заметок занятий, понятий или учебников.
    - В самом файле `Дедлайны и ДЗ.md` также **ЗАПРЕЩЕНО** использовать прямые ссылки вида `[[...]]` на пары. Занятие-источник указывается исключительно обычным текстом (например: `Источник: ПРОГ - Лекция 2. Базовый синтаксис`).
    Это полностью исключает попадание файла дедлайнов в граф связей Obsidian Graph View и защищает дисциплины от паразитного междисциплинарного связывания.
12. **Самопроверка ссылок (Self-Linting):** перед финальным отчётом агент обязан проверить все новые и затронутые заметки на отсутствие битых ссылок `[[...]]`.
13. **Изоляция скриптов (Zero-Trash Policy):** категорически запрещено создавать одноразовые скрипты (`make_*.py`, `temp_*.py`) в корне проекта. Все временные утилиты создаются строго в папке `scratch/` и удаляются после выполнения.

## 7. Prohibited Patterns & Safety
- **Запрет мусорных файлов в корне:** запрещено сохранять временные скрипты и отчеты в корневой каталог проекта. Использовать только папку `scratch/`.
- **Запрет деструктивных действий:** запрещено без прямого подтверждения пользователя удалять каталоги вне временных кэшей (`cache/`), сбрасывать Git (`git reset --hard`) или перезаписывать готовые заметки.
- **Защита секретов:** запрещено хардкодить пути к чувствительным ресурсам или токены. Все настройки хранятся в `.env`.
- **Защита системных путей:** запрещено модифицировать файлы операционной системы Windows.

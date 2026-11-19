"""Модуль базовых дымовых тестов (smoke tests) для верификации целостности репозитория."""

import importlib.util
import os
import unittest
from pathlib import Path


class TestProjectIntegrity(unittest.TestCase):
    """Набор тестов для проверки структуры проекта и валидности модулей."""

    def setUp(self) -> None:
        """Инициализация путей к ключевым артефактам проекта."""
        self.root_dir = Path(__file__).resolve().parent.parent

    def test_required_files_exist(self) -> None:
        """Проверка наличия всех обязательных файлов стандарта 2026 года."""
        required_files = [
            "AGENTS.md",
            "PROCESSED_VIDEOS.md",
            "README.md",
            "LICENSE",
            ".gitignore",
            ".repomixignore",
            ".env.example",
            "pyproject.toml",
            "requirements.txt",
            "TASK.md",
            "app_gui.py",
            "src/__init__.py",
            "src/extract.py",
            "src/cuda_utils.py",
            "src/vault_utils.py",
            ".agents/skills/lecture-processor/SKILL.md",
            ".agents/skills/vault-curator/SKILL.md",
            "docs/architecture/pipeline.md",
            "docs/architecture/obsidian_vault.md",
        ]
        for rel_path in required_files:
            file_path = self.root_dir / rel_path
            self.assertTrue(
                file_path.exists(),
                f"Обязательный файл {rel_path} отсутствует в репозитории.",
            )

    def test_agents_contract_structure(self) -> None:
        """Проверка структуры и ключевых разделов файла AGENTS.md по шаблону AGENTS.template.md."""
        agents_file = self.root_dir / "AGENTS.md"
        content = agents_file.read_text(encoding="utf-8")

        expected_sections = [
            "Project Overview & Tech Stack",
            "Standard Commands",
            "Session Continuity & Orientation Protocol",
            "Coding & Architecture Standards",
            "Pre-Commit Checklist",
            "Architecture & Pipeline Rules",
            "Prohibited Patterns & Safety",
        ]
        for section in expected_sections:
            self.assertIn(
                section,
                content,
                f"Раздел '{section}' отсутствует в файле AGENTS.md.",
            )

    def test_key_invariants_present(self) -> None:
        """Проверка ключевых инвариантов конвейера в AGENTS.md."""
        agents_file = self.root_dir / "AGENTS.md"
        content = agents_file.read_text(encoding="utf-8")

        expected_invariants = [
            "Мультимодальный анализ слайдов",
            "Аббревиатуры дисциплин",
            "Синхронная миграция без потери связей",
            "Active Recall",
            "Дедлайны и ДЗ",
            "Self-Linting",
            "scratch",
        ]
        for inv in expected_invariants:
            self.assertIn(
                inv,
                content,
                f"Ключевой инвариант '{inv}' отсутствует в AGENTS.md.",
            )

    def test_root_directory_cleanliness(self) -> None:
        """Проверка отсутствия посторонних скриптов в корневой директории."""
        allowed_root_py = {"app_gui.py"}
        root_py_files = {
            f.name for f in self.root_dir.glob("*.py") if f.is_file()
        }
        unexpected_files = root_py_files - allowed_root_py
        self.assertEqual(
            unexpected_files,
            set(),
            f"Обнаружены посторонние скрипты в корне проекта: {unexpected_files}. Используйте папку scratch/.",
        )

    def test_extract_module_syntax(self) -> None:
        """Проверка корректности синтаксиса и структуры модуля extract.py."""
        extract_path = self.root_dir / "src" / "extract.py"
        spec = importlib.util.spec_from_file_location("extract", extract_path)
        self.assertIsNotNone(spec, "Не удалось создать спецификацию для модуля extract.py")

    def test_task_tracker_structure(self) -> None:
        """Проверка соответствия структуры TASK.md шаблону TASK.template.md."""
        task_file = self.root_dir / "TASK.md"
        content = task_file.read_text(encoding="utf-8")

        expected_sections = [
            "Project Health & Stage",
            "Completed Milestones",
            "Active Task",
            "Next Immediate Steps",
            "Architectural Decisions & Blockers",
        ]
        for section in expected_sections:
            self.assertIn(
                section,
                content,
                f"Раздел '{section}' отсутствует в файле TASK.md.",
            )

    def test_templates_conformance(self) -> None:
        """Проверка соответствия ключевых файлов шаблонам из ~/.gemini/config/templates."""
        gitignore = (self.root_dir / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("repomix-output.*", gitignore)
        self.assertIn(".venv/", gitignore)
        self.assertIn("Thumbs.db", gitignore)

        repomixignore = (self.root_dir / ".repomixignore").read_text(encoding="utf-8")
        self.assertIn("node_modules/", repomixignore)
        self.assertIn("tests/", repomixignore)
        self.assertIn("*.wav", repomixignore)


if __name__ == "__main__":
    unittest.main()

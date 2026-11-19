"""Герметичные модульные тесты для модуля аудита хранилища vault_utils.py."""

import tempfile
import unittest
from pathlib import Path

from src.vault_utils import (
    clean_link_target,
    get_system_telemetry,
    get_vault_stats,
    is_media_link,
    verify_link_integrity,
)


class TestVaultUtils(unittest.TestCase):
    """Сьют проверок для верификации алгоритмов парсинга ссылок и сбора статистики."""

    def test_clean_link_target_variations(self) -> None:
        """Проверка корректной нормализации wiki-ссылок с алиасами и якорями."""
        self.assertEqual(clean_link_target("Простая заметка"), "Простая заметка")
        self.assertEqual(clean_link_target("Заметка|Отображаемый текст"), "Заметка")
        self.assertEqual(clean_link_target("Заметка#Заголовок"), "Заметка")
        self.assertEqual(clean_link_target("Заметка#^block-123|Псевдоним"), "Заметка")
        self.assertEqual(clean_link_target("  Заметка с пробелами | алиас  "), "Заметка с пробелами")

    def test_is_media_link(self) -> None:
        """Проверка классификации медиавложений."""
        self.assertTrue(is_media_link("image.png"))
        self.assertTrue(is_media_link("screenshot.JPG"))
        self.assertTrue(is_media_link("document.pdf"))
        self.assertFalse(is_media_link("Производная функции"))
        self.assertFalse(is_media_link("МатАн - Лекция 1.md"))

    def test_verify_link_integrity_hermetic(self) -> None:
        """Проверка линтера ссылок на изолированной синтетической структуре."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault = Path(tmp_dir)
            math_dir = vault / "Математика Матанализ"
            math_terms = math_dir / "Термины"
            math_terms.mkdir(parents=True, exist_ok=True)

            (math_terms / "Предел функции.md").write_text("# Предел функции", encoding="utf-8")
            (math_terms / "Непрерывность.md").write_text("# Непрерывность", encoding="utf-8")

            lecture_content = (
                "# Лекция\n"
                "Определим [[Предел функции]] и его свойства.\n"
                "Также рассмотрим [[Непрерывность|непрерывную функцию]].\n"
                "Смотри [[Предел функции#Теорема]] и рисунок [[diagram.png]].\n"
                "Ошибка связи: [[Несуществующая заметка]].\n"
                "Сторонняя дисциплина: [[ОРГ - Лекция 1]].\n"
                "Синтаксис кода: ```python\ndf[['Column']]\n```\n"
            )
            (math_dir / "МатАн - Лекция 1. Тест.md").write_text(lecture_content, encoding="utf-8")

            # Проверка с фильтром исключённых дисциплин
            res_filtered = verify_link_integrity(str(vault), excluded_prefixes={"ОРГ"})

            self.assertEqual(res_filtered["valid_links_count"], 3)
            self.assertEqual(len(res_filtered["broken_links"]), 1)
            self.assertIn("Несуществующая заметка", res_filtered["broken_links"][0])
            self.assertEqual(len(res_filtered["untracked_subject_links"]), 1)
            self.assertIn("ОРГ - Лекция 1", res_filtered["untracked_subject_links"][0])

            # Проверка в универсальном режиме (без исключений)
            res_universal = verify_link_integrity(str(vault))
            self.assertEqual(res_universal["valid_links_count"], 3)
            self.assertEqual(len(res_universal["broken_links"]), 2)
            self.assertEqual(len(res_universal["untracked_subject_links"]), 0)

    def test_get_vault_stats_hermetic(self) -> None:
        """Проверка агрегации показателей хранилища в синтетической структуре."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault = Path(tmp_dir)
            dm_dir = vault / "Дискретная математика"
            dm_terms = dm_dir / "Термины"
            dm_terms.mkdir(parents=True, exist_ok=True)

            (dm_dir / "ДМ - Лекция 1.md").write_text("Конспект 1", encoding="utf-8")
            (dm_dir / "ДМ - Практика 1.md").write_text("Практика 1", encoding="utf-8")
            (dm_dir / "Учебник - Дискретная математика.md").write_text("Учебник", encoding="utf-8")
            (dm_dir / "Дискретная математика.canvas").write_text("{}", encoding="utf-8")
            (dm_terms / "Множество.md").write_text("Определение", encoding="utf-8")

            deadlines_file = vault / "Дедлайны и ДЗ.md"
            deadlines_file.write_text("- [ ] Задание 1\n- [x] Задание 2\n", encoding="utf-8")

            stats = get_vault_stats(str(vault))

            self.assertEqual(stats["total_notes"], 2)
            self.assertEqual(stats["total_terms"], 1)
            self.assertEqual(stats["deadlines_count"], 2)
            dm_stat = stats["subjects"]["Дискретная математика"]
            self.assertTrue(dm_stat["has_textbook"])
            self.assertTrue(dm_stat["has_canvas"])

    def test_get_system_telemetry(self) -> None:
        """Проверка возврата словаря телеметрии с ожидаемыми полями."""
        telem = get_system_telemetry()
        self.assertIn("ffmpeg_available", telem)
        self.assertIn("cuda_available", telem)
        self.assertIn("python_version", telem)


if __name__ == "__main__":
    unittest.main()

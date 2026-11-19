"""Модульные тесты для проверки корректности инициализации и потокобезопасности GUI."""

import unittest

from app_gui import TranscriberApp


class TestTranscriberGUI(unittest.TestCase):
    """Сьют проверок для вспомогательного интерфейса CustomTkinter."""

    def test_gui_initialization_and_queue(self) -> None:
        """Проверка безопасной инициализации окна и механизма очередей."""
        app = TranscriberApp()
        executed = []

        # Тест доставки задачи через потокобезопасную очередь
        app.post_to_ui(lambda: executed.append("OK"))
        app.update()

        self.assertEqual(executed, ["OK"])
        self.assertIn("GupkaScribe", app.title())

        # Закрытие приложения
        app.destroy()


if __name__ == "__main__":
    unittest.main()

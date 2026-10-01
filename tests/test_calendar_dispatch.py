from unittest.mock import MagicMock
from gui_app import LooneyF1GUI


def test_calendar_uses_main_export_and_selected_output_folder():
    gui = MagicMock()
    gui.export_button = {'state': 'normal'}
    LooneyF1GUI.export_from_calendar(gui, 2026, 6, 'ALL')
    gui.season_var.set.assert_called_once_with('2026')
    gui.round_var.set.assert_called_once_with('6')
    gui.session_var.set.assert_called_once_with('All Sessions')
    gui.start_export.assert_called_once_with()
    gui.output_dir_var.set.assert_not_called()


def test_calendar_cannot_start_a_second_export():
    gui = MagicMock()
    gui.export_button = {'state': 'disabled'}
    LooneyF1GUI.export_from_calendar(gui, 2026, 6, 'R')
    gui.start_export.assert_not_called()

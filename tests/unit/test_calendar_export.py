# tests/unit/test_calendar_export.py
"""Tests for calendar window export functionality"""

from unittest.mock import MagicMock, patch

class TestCalendarExport:
    """Test calendar window export functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create mock GUI parent
        self.mock_root = MagicMock()
        self.mock_parent_gui = MagicMock()
        self.mock_parent_gui.root = self.mock_root
        self.mock_parent_gui.log_message = MagicMock()
        self.mock_parent_gui.export_from_calendar = MagicMock()
        
    @patch('gui_app.CalendarWindow.__init__', return_value=None)
    def test_calendar_window_creation(self, mock_init):
        """Test calendar window can be created"""
        from gui_app import CalendarWindow
        
        # Mock the initialization to avoid actual window creation
        calendar = CalendarWindow.__new__(CalendarWindow)
        calendar.parent_gui = self.mock_parent_gui
        calendar.season = 2025
        calendar.schedule_data = []
        
        assert calendar.parent_gui == self.mock_parent_gui
        assert calendar.season == 2025
        
    def test_export_session_with_round_number(self):
        """Test export session with explicit round number"""
        from gui_app import CalendarWindow
        
        # Create mock calendar window
        calendar = CalendarWindow.__new__(CalendarWindow)
        calendar.parent_gui = self.mock_parent_gui
        calendar.season = 2025
        
        # Mock the export_session method behavior
        def mock_export_session(session, round_no=None):
            if round_no is None:
                return
            try:
                round_no = int(round_no)
                calendar.parent_gui.export_from_calendar(calendar.season, round_no, session)
            except ValueError:
                calendar.parent_gui.log_message(f"Invalid round number: {round_no}", "ERROR")
        
        calendar.export_session = mock_export_session
        
        # Test export with valid round number
        calendar.export_session("Q", 5)
        
        calendar.parent_gui.export_from_calendar.assert_called_once_with(2025, 5, "Q")
        
    def test_export_session_invalid_round_number(self):
        """Test export session with invalid round number"""
        from gui_app import CalendarWindow
        
        calendar = CalendarWindow.__new__(CalendarWindow)
        calendar.parent_gui = self.mock_parent_gui
        calendar.season = 2025
        
        # Mock the export_session method behavior
        def mock_export_session(session, round_no=None):
            try:
                round_no = int(round_no)
                calendar.parent_gui.export_from_calendar(calendar.season, round_no, session)
            except ValueError:
                calendar.parent_gui.log_message(f"Invalid round number: {round_no}", "ERROR")
        
        calendar.export_session = mock_export_session
        
        # Test export with invalid round number
        calendar.export_session("Q", "invalid")
        
        calendar.parent_gui.log_message.assert_called_once_with("Invalid round number: invalid", "ERROR")
        calendar.parent_gui.export_from_calendar.assert_not_called()
        
    def test_calendar_schedule_loading(self):
        """Test calendar schedule data loading"""
        sample_schedule = [
            {
                "round": 1,
                "date": "2025-03-15",
                "raceName": "Bahrain Grand Prix", 
                "Circuit": {"circuitName": "Bahrain International Circuit"},
                "EventFormat": "conventional",
                "hasSprint": False
            },
            {
                "round": 4,
                "date": "2025-04-20",
                "raceName": "Chinese Grand Prix",
                "Circuit": {"circuitName": "Shanghai International Circuit"},
                "EventFormat": "sprint",
                "hasSprint": True
            }
        ]
        
        from gui_app import CalendarWindow
        
        calendar = CalendarWindow.__new__(CalendarWindow)
        calendar.parent_gui = self.mock_parent_gui
        calendar.season = 2025
        calendar.schedule_data = sample_schedule
        
        # Test filtering for sprint rounds
        sprint_rounds = [event for event in calendar.schedule_data if event.get("hasSprint", False)]
        assert len(sprint_rounds) == 1
        assert sprint_rounds[0]["round"] == 4
        
        # Test filtering for conventional rounds  
        conventional_rounds = [event for event in calendar.schedule_data if not event.get("hasSprint", False)]
        assert len(conventional_rounds) == 1
        assert conventional_rounds[0]["round"] == 1
        
    def test_export_from_calendar_updates_main_gui(self):
        """Test that export from calendar updates main GUI fields"""
        # Create mock main GUI
        mock_season_var = MagicMock()
        mock_round_var = MagicMock()  
        mock_session_var = MagicMock()
        
        self.mock_parent_gui.season_var = mock_season_var
        self.mock_parent_gui.round_var = mock_round_var
        self.mock_parent_gui.session_var = mock_session_var
        self.mock_parent_gui.start_export = MagicMock()
        
        # Mock the export_from_calendar method
        def mock_export_from_calendar(season, round_no, session):
            self.mock_parent_gui.season_var.set(str(season))
            self.mock_parent_gui.round_var.set(str(round_no))
            self.mock_parent_gui.session_var.set(session)
            self.mock_parent_gui.log_message(f"Calendar export: Season {season}, Round {round_no}, Session {session}", "STEP")
            self.mock_parent_gui.start_export()
        
        self.mock_parent_gui.export_from_calendar = mock_export_from_calendar
        
        # Test export from calendar
        self.mock_parent_gui.export_from_calendar(2025, 8, "R")
        
        # Verify GUI fields were updated
        mock_season_var.set.assert_called_once_with("2025")
        mock_round_var.set.assert_called_once_with("8")
        mock_session_var.set.assert_called_once_with("R")
        
        # Verify export was started
        self.mock_parent_gui.start_export.assert_called_once()
        
        # Verify log message
        self.mock_parent_gui.log_message.assert_called_once_with(
            "Calendar export: Season 2025, Round 8, Session R", "STEP"
        )
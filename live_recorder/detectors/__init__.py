"""
Detector-Module für Live Recording
"""

__all__ = ["LapCompletionDetector", "PitstopDetector", "RaceControlParser"]

from .lap_completion import LapCompletionDetector
from .pitstop import PitstopDetector
from .race_control import RaceControlParser

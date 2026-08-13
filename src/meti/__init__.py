"""
Middle-East Tension Indicator (METI)
A real-time market-based geopolitical tension gauge.
"""

__version__ = "1.0.0"
__author__ = "Kiarash Shayegani"

from .config import get_settings
from .indicators.tension import calculate_tension_index

__all__ = ["get_settings", "calculate_tension_index", "__version__"]

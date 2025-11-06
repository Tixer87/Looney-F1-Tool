"""Version information for Looney F1 Tool"""

__version__ = "1.7.0"
__version_info__ = (1, 7, 0)

# Release metadata
RELEASE_NAME = "Looney F1 Tool"
RELEASE_STAGE = "stable"  # stable, beta, alpha
BUILD_DATE = "2025-11-01"

def get_version_string():
    """Return full version string"""
    return f"{RELEASE_NAME} v{__version__}"

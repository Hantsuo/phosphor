"""
Simple test to ensure main module imports correctly.
"""

def test_main_import() -> None:
    """Main module should import without error."""
    from app import main
    assert main.app is not None
    assert main.app.title == "PHOSPHOR BBS"
    assert main.app.version == "0.1.0"
"""
Qt Diagnostics and System Information Utility
Provides diagnostic functions for Qt-related issues and system compatibility checks.
"""

import os
import sys
import platform
from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
from PyQt5.QtWidgets import QApplication


def get_qt_system_info():
    """Get comprehensive Qt and system information for diagnostics"""
    info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'architecture': platform.architecture(),
        'qt_version': QT_VERSION_STR,
        'pyqt_version': PYQT_VERSION_STR,
        'qt_platform': os.environ.get('QT_QPA_PLATFORM', 'default'),
        'qt_opengl': os.environ.get('QT_OPENGL', 'default'),
        'qt_auto_scale': os.environ.get('QT_AUTO_SCREEN_SCALE_FACTOR', 'default'),
        'qt_scale_factor': os.environ.get('QT_SCALE_FACTOR', 'default'),
        'qt_highdpi': os.environ.get('QT_ENABLE_HIGHDPI_SCALING', 'default'),
    }

    # Check for graphics drivers
    try:
        import subprocess
        if platform.system() == 'Windows':
            result = subprocess.run(['wmic', 'path', 'win32_videocontroller', 'get', 'name'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                info['graphics_drivers'] = [line.strip() for line in result.stdout.split('\n') if line.strip() and 'Name' not in line]
            else:
                info['graphics_drivers'] = ['Unable to detect']
        else:
            info['graphics_drivers'] = ['Non-Windows system']
    except Exception as e:
        info['graphics_drivers'] = [f'Error detecting graphics drivers: {str(e)}']

    return info


def print_qt_diagnostics():
    """Print Qt diagnostics information"""
    print("=== Qt Diagnostics ===")
    info = get_qt_system_info()

    for key, value in info.items():
        if isinstance(value, list):
            print(f"{key}:")
            for item in value:
                print(f"  - {item}")
        else:
            print(f"{key}: {value}")
    print("=" * 50)


def check_qt_compatibility():
    """Check for common Qt compatibility issues"""
    issues = []

    # Check Qt version
    qt_major, qt_minor = map(int, QT_VERSION_STR.split('.')[:2])
    if qt_major < 5 or (qt_major == 5 and qt_minor < 12):
        issues.append(f"Qt version {QT_VERSION_STR} may have compatibility issues. Consider upgrading to 5.12+")

    # Check PyQt version
    pyqt_major, pyqt_minor = map(int, PYQT_VERSION_STR.split('.')[:2])
    if pyqt_major < 5 or (pyqt_major == 5 and pyqt_minor < 12):
        issues.append(f"PyQt version {PYQT_VERSION_STR} may have compatibility issues. Consider upgrading to 5.12+")

    # Check environment variables
    if 'QT_QPA_PLATFORM' not in os.environ:
        issues.append("QT_QPA_PLATFORM not set - may cause display issues")

    if os.environ.get('QT_OPENGL') != 'software':
        issues.append("Consider setting QT_OPENGL=software for better stability")

    # Check for high DPI issues
    if os.environ.get('QT_ENABLE_HIGHDPI_SCALING') == '1':
        issues.append("High DPI scaling enabled - may cause rendering issues")

    return issues


def apply_qt_fixes():
    """Apply common Qt fixes for stability"""
    print("Applying Qt stability fixes...")

    # Force software rendering
    os.environ['QT_OPENGL'] = 'software'
    print("[OK] Forced software OpenGL rendering")

    # Disable problematic features
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0'
    os.environ['QT_SCALE_FACTOR'] = '1'
    print("[OK] Disabled auto-scaling and high DPI features")

    # Set platform if not set
    if 'QT_QPA_PLATFORM' not in os.environ:
        os.environ['QT_QPA_PLATFORM'] = 'windows'
        print("[OK] Set Windows platform plugin")

    # Reduce logging
    os.environ['QT_LOGGING_RULES'] = 'qt.qpa.plugin=false'
    print("[OK] Reduced Qt logging")

    print("Qt fixes applied successfully")


def test_qt_initialization():
    """Test Qt initialization with current settings"""
    try:
        print("Testing Qt initialization...")
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # Set stability attributes
        from PyQt5.QtCore import Qt
        app.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
        app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, False)

        print("[OK] Qt initialization successful")
        return True

    except Exception as e:
        print(f"[FAIL] Qt initialization failed: {e}")
        return False


if __name__ == "__main__":
    print_qt_diagnostics()
    issues = check_qt_compatibility()
    if issues:
        print("\nCompatibility Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nNo compatibility issues detected")

    print("\nTesting Qt initialization...")
    test_qt_initialization()
"""
Application Configuration Management

Centralized configuration management using environment variables with sensible defaults.
Follows the 12-factor app principles for configuration.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    path: Path
    max_connections: int = 10
    enable_foreign_keys: bool = True
    enable_wal: bool = True
    synchronous_mode: str = "NORMAL"
    cache_size_mb: int = 64
    temp_store: str = "MEMORY"
    journal_mode: str = "WAL"
    busy_timeout_ms: int = 30000

    @property
    def cache_size_pages(self) -> int:
        """Convert MB to SQLite page cache size."""
        return -(self.cache_size_mb * 1024 * 1024) // 4096  # Negative for KB


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    max_file_size_mb: int = 10
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True


@dataclass
class UIConfig:
    """UI configuration settings."""

    theme: str = "professional"
    window_width: int = 1400
    window_height: int = 900
    enable_high_dpi: bool = True
    icon_path: Optional[str] = None


@dataclass
class SecurityConfig:
    """Security configuration settings."""

    session_timeout_minutes: int = 480  # 8 hours
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    password_min_length: int = 8
    enable_audit_logging: bool = True


@dataclass
class PerformanceConfig:
    """Performance configuration settings."""

    max_table_rows: int = 10000
    pagination_size: int = 100
    search_timeout_seconds: int = 30
    export_timeout_seconds: int = 300
    enable_caching: bool = True
    cache_ttl_seconds: int = 300


@dataclass
class FileConfig:
    """File handling configuration settings."""

    max_upload_size_mb: int = 50
    allowed_extensions: list = field(
        default_factory=lambda: [".pdf", ".xlsx", ".xls", ".csv", ".txt"]
    )
    temp_dir: Optional[Path] = None
    cleanup_temp_files: bool = True
    temp_file_ttl_hours: int = 24


@dataclass
class AppConfig:
    """Main application configuration."""

    # Core paths
    base_dir: Path
    data_dir: Path
    logs_dir: Path
    temp_dir: Path

    # Component configs
    database: DatabaseConfig
    logging: LoggingConfig
    ui: UIConfig
    security: SecurityConfig
    performance: PerformanceConfig
    files: FileConfig

    # Application metadata
    name: str = "FWMIS"
    version: str = "2.0.0"
    environment: str = "development"
    debug: bool = False

    # Feature flags
    enable_audit_trail: bool = True
    enable_export_features: bool = True
    enable_bulk_operations: bool = True
    enable_advanced_search: bool = True


class ConfigManager:
    """Configuration manager with environment variable support."""

    @staticmethod
    def _get_path_env(key: str, default: str, base_dir: Optional[Path] = None) -> Path:
        """Get a path from environment variable or return default."""
        path_str = os.getenv(key, default)
        if base_dir and not Path(path_str).is_absolute():
            return base_dir / path_str
        return Path(path_str)

    @staticmethod
    def _get_env(key: str, default: str, type_converter=str):
        """Get environment variable with type conversion."""
        value = os.getenv(key, default)
        try:
            return type_converter(value)
        except (ValueError, TypeError):
            return type_converter(default)

    @staticmethod
    def _get_bool_env(key: str, default: bool) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    @classmethod
    def load_from_env(cls) -> AppConfig:
        """
        Load configuration from environment variables with defaults.

        Environment variables follow the pattern FWMIS_{SECTION}_{SETTING}
        """
        # Base directory detection
        # From FWMIS/scripts/config/settings.py, we want to go up to FWMIS/
        base_dir = Path(__file__).parent.parent.parent  # This gives us FWMIS/
        data_dir = base_dir / "data"

        # Database configuration
        db_config = DatabaseConfig(
            path=cls._get_path_env(
                "FWMIS_DATABASE_PATH", "data/fruitless.db", base_dir
            ),
            max_connections=cls._get_env("FWMIS_DATABASE_MAX_CONNECTIONS", "10", int),
            enable_foreign_keys=cls._get_bool_env("FWMIS_DATABASE_FOREIGN_KEYS", True),
            enable_wal=cls._get_bool_env("FWMIS_DATABASE_WAL", True),
            synchronous_mode=os.getenv("FWMIS_DATABASE_SYNC_MODE", "NORMAL"),
            cache_size_mb=cls._get_env("FWMIS_DATABASE_CACHE_MB", "64", int),
            temp_store=os.getenv("FWMIS_DATABASE_TEMP_STORE", "MEMORY"),
            journal_mode=os.getenv("FWMIS_DATABASE_JOURNAL_MODE", "WAL"),
            busy_timeout_ms=cls._get_env("FWMIS_DATABASE_BUSY_TIMEOUT", "30000", int),
        )

        # Logging configuration
        logging_config = LoggingConfig(
            level=os.getenv("FWMIS_LOG_LEVEL", "INFO"),
            format=os.getenv(
                "FWMIS_LOG_FORMAT",
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            ),
            max_file_size_mb=cls._get_env("FWMIS_LOG_MAX_SIZE_MB", "10", int),
            backup_count=cls._get_env("FWMIS_LOG_BACKUP_COUNT", "5", int),
            enable_console=cls._get_bool_env("FWMIS_LOG_CONSOLE", True),
            enable_file=cls._get_bool_env("FWMIS_LOG_FILE", True),
        )

        # UI configuration
        ui_config = UIConfig(
            theme=os.getenv("FWMIS_UI_THEME", "professional"),
            window_width=cls._get_env("FWMIS_UI_WINDOW_WIDTH", "1400", int),
            window_height=cls._get_env("FWMIS_UI_WINDOW_HEIGHT", "900", int),
            enable_high_dpi=cls._get_bool_env("FWMIS_UI_HIGH_DPI", True),
            icon_path=os.getenv("FWMIS_UI_ICON_PATH"),
        )

        # Security configuration
        security_config = SecurityConfig(
            session_timeout_minutes=cls._get_env(
                "FWMIS_SECURITY_SESSION_TIMEOUT", "480", int
            ),
            max_login_attempts=cls._get_env("FWMIS_SECURITY_MAX_ATTEMPTS", "5", int),
            lockout_duration_minutes=cls._get_env(
                "FWMIS_SECURITY_LOCKOUT_MINUTES", "15", int
            ),
            password_min_length=cls._get_env(
                "FWMIS_SECURITY_PASSWORD_MIN_LENGTH", "8", int
            ),
            enable_audit_logging=cls._get_bool_env(
                "FWMIS_SECURITY_AUDIT_LOGGING", True
            ),
        )

        # Performance configuration
        performance_config = PerformanceConfig(
            max_table_rows=cls._get_env("FWMIS_PERFORMANCE_MAX_ROWS", "10000", int),
            pagination_size=cls._get_env("FWMIS_PERFORMANCE_PAGE_SIZE", "100", int),
            search_timeout_seconds=cls._get_env(
                "FWMIS_PERFORMANCE_SEARCH_TIMEOUT", "30", int
            ),
            export_timeout_seconds=cls._get_env(
                "FWMIS_PERFORMANCE_EXPORT_TIMEOUT", "300", int
            ),
            enable_caching=cls._get_bool_env("FWMIS_PERFORMANCE_CACHING", True),
            cache_ttl_seconds=cls._get_env("FWMIS_PERFORMANCE_CACHE_TTL", "300", int),
        )

        # File configuration
        file_config = FileConfig(
            max_upload_size_mb=cls._get_env("FWMIS_FILES_MAX_SIZE_MB", "50", int),
            allowed_extensions=os.getenv(
                "FWMIS_FILES_EXTENSIONS", ".pdf,.xlsx,.xls,.csv,.txt"
            ).split(","),
            temp_dir=cls._get_path_env("FWMIS_FILES_TEMP_DIR", "temp", base_dir),
            cleanup_temp_files=cls._get_bool_env("FWMIS_FILES_CLEANUP_TEMP", True),
            temp_file_ttl_hours=cls._get_env("FWMIS_FILES_TEMP_TTL_HOURS", "24", int),
        )

        # Create main config
        config = AppConfig(
            base_dir=base_dir,
            data_dir=data_dir,
            logs_dir=data_dir / "logs",
            temp_dir=base_dir / "temp",
            database=db_config,
            logging=logging_config,
            ui=ui_config,
            security=security_config,
            performance=performance_config,
            files=file_config,
            name=os.getenv("FWMIS_APP_NAME", "FWMIS"),
            version=os.getenv("FWMIS_APP_VERSION", "2.0.0"),
            environment=os.getenv("FWMIS_ENVIRONMENT", "development"),
            debug=cls._get_bool_env("FWMIS_DEBUG", False),
            enable_audit_trail=cls._get_bool_env("FWMIS_AUDIT_TRAIL", True),
            enable_export_features=cls._get_bool_env("FWMIS_EXPORT_FEATURES", True),
            enable_bulk_operations=cls._get_bool_env("FWMIS_BULK_OPERATIONS", True),
            enable_advanced_search=cls._get_bool_env("FWMIS_ADVANCED_SEARCH", True),
        )

        return config

    @staticmethod
    def validate_config(config: AppConfig) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Check database path
        if not config.database.path.parent.exists():
            issues.append(
                f"Database directory does not exist: {config.database.path.parent}"
            )

        # Check temp directory
        if not config.temp_dir.exists():
            try:
                config.temp_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create temp directory: {e}")

        # Check log directory
        if not config.logs_dir.exists():
            try:
                config.logs_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create logs directory: {e}")

        # Validate numeric ranges
        if config.database.max_connections < 1:
            issues.append("Database max_connections must be >= 1")

        if config.performance.pagination_size < 1:
            issues.append("Performance pagination_size must be >= 1")

        if config.files.max_upload_size_mb < 1:
            issues.append("Files max_upload_size_mb must be >= 1")

        return issues

    @staticmethod
    def print_config_summary(config: AppConfig) -> None:
        """Print a summary of the current configuration."""
        print("=== FWMIS Configuration Summary ===")
        print(f"Environment: {config.environment}")
        print(f"Debug Mode: {config.debug}")
        print(f"Version: {config.version}")
        print()
        print("Database:")
        print(f"  Path: {config.database.path}")
        print(f"  Max Connections: {config.database.max_connections}")
        print(f"  WAL Mode: {config.database.enable_wal}")
        print()
        print("Logging:")
        print(f"  Level: {config.logging.level}")
        print(f"  File Logging: {config.logging.enable_file}")
        print(f"  Console Logging: {config.logging.enable_console}")
        print()
        print("Performance:")
        print(f"  Max Table Rows: {config.performance.max_table_rows}")
        print(f"  Pagination Size: {config.performance.pagination_size}")
        print(f"  Caching: {config.performance.enable_caching}")
        print()
        print("Security:")
        print(f"  Session Timeout: {config.security.session_timeout_minutes} minutes")
        print(f"  Audit Logging: {config.security.enable_audit_logging}")


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global application configuration (singleton)."""
    global _config

    if _config is None:
        _config = ConfigManager.load_from_env()

        # Validate configuration
        issues = ConfigManager.validate_config(_config)
        if issues:
            print("Configuration Issues:")
            for issue in issues:
                print(f"  - {issue}")
            print()

        # Print config summary in debug mode
        if _config.debug:
            ConfigManager.print_config_summary(_config)

    return _config


def reload_config() -> AppConfig:
    """Reload configuration from environment variables."""
    global _config
    _config = ConfigManager.load_from_env()
    return _config

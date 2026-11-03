"""Application logging setup with sensitive data redaction."""

import re
import logging
import sys
from pathlib import Path
from typing import Optional
from config.settings import settings

# Sensitive token/key patterns for redaction
SENSITIVE_PATTERNS = [
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-_.]+"), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(client_secret=)[^&\s]+"), r"\1[REDACTED_SECRET]"),
    (re.compile(r"('access_token':\s*')[^']+(')"), r"\g<1>[REDACTED_TOKEN]\2"),
    (re.compile(r'("access_token":\s*")[^"]+(")'), r"\g<1>[REDACTED_TOKEN]\2"),
    (re.compile(r"('client_secret':\s*')[^']+(')"), r"\g<1>[REDACTED_SECRET]\2"),
    (re.compile(r'("client_secret":\s*")[^"]+(")'), r"\g<1>[REDACTED_SECRET]\2"),
]


def redact_sensitive(text: str) -> str:
    """Redact tokens, client secrets, and sensitive credentials from log strings."""
    if not isinstance(text, str):
        text = str(text)
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class SensitiveFilter(logging.Filter):
    """Logging filter that redacts sensitive information from messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact_sensitive(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_sensitive(str(v)) for v in record.args)
        return True


def setup_logger(
    name: str = "sailpoint_ad_automation",
    log_file: Optional[str] = "execution.log",
    level: int = logging.INFO,
) -> logging.Logger:
    """Configure and return a standardized logger with console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if already configured
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    sensitive_filter = SensitiveFilter()

    # Console Handler (clean output for tester)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sensitive_filter)
    logger.addHandler(console_handler)

    # File Handler
    if log_file:
        log_path = Path(settings.logs_dir) / log_file
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(sensitive_filter)
        logger.addHandler(file_handler)

    return logger


def get_logger(module_name: str) -> logging.Logger:
    """Convenience function to get a module-specific logger."""
    return logging.getLogger(f"sailpoint_ad_automation.{module_name}")


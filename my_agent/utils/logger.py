"""Structured logging utilities."""
import logging
import json
from typing import Any, Dict
from datetime import datetime


class StructuredLogger:
    """Logger that outputs structured JSON logs for observability."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Only add handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            self.logger.addHandler(handler)

    def log_event(self, event_type: str, data: Dict[str, Any], level: str = "info"):
        """
        Log a structured event.

        Args:
            event_type: Type of event (e.g., "search_query", "fetch_url", "decision")
            data: Event data as a dictionary
            level: Log level ("info", "warning", "error")
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            **data
        }

        message = json.dumps(log_entry, default=str)

        if level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)

    def log_search_query(self, query: str, num_results: int, latency_ms: float):
        """Log a search query execution."""
        self.log_event("search_query", {
            "query": query,
            "num_results": num_results,
            "latency_ms": latency_ms
        })

    def log_url_fetch(self, url: str, success: bool, status_code: int, latency_ms: float, error: str = ""):
        """Log a URL fetch attempt."""
        self.log_event("fetch_url", {
            "url": url,
            "success": success,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "error": error
        })

    def log_decision(self, decision_type: str, reason: str, data: Dict[str, Any] = None):
        """Log an orchestration decision."""
        log_data = {
            "decision_type": decision_type,
            "reason": reason
        }
        if data:
            log_data.update(data)
        self.log_event("decision", log_data)

    def log_performance(self, operation: str, latency_ms: float, success: bool):
        """Log performance metrics."""
        self.log_event("performance", {
            "operation": operation,
            "latency_ms": latency_ms,
            "success": success
        })


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def get_logger(name: str) -> logging.Logger:
    """Get a standard Python logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

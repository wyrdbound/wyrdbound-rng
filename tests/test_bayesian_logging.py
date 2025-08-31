"""
Test bayesian model logging behavior.
"""
import io
import logging
import sys
from contextlib import redirect_stdout

from wyrdbound_rng.generator import Generator
from wyrdbound_rng.segmenters.fantasy_name_segmenter import FantasyNameSegmenter


class TestBayesianLogging:
    """Test suite for BayesianModel logging behavior."""

    def test_no_output_by_default(self, fantasy_names_yaml_path):
        """Test that no output is printed by default when using bayesian algorithm."""
        # Capture stdout to ensure nothing is printed
        stdout_capture = io.StringIO()
        
        with redirect_stdout(stdout_capture):
            generator = Generator(fantasy_names_yaml_path)
            names = generator.generate(1, max_chars=15, algorithm="bayesian")
            
        # Verify name was generated
        assert len(names) == 1
        assert names[0] is not None
        
        # Verify no output was printed to stdout
        captured_output = stdout_capture.getvalue()
        assert captured_output == ""

    def test_injected_logger_captures_logs(self, fantasy_names_yaml_path):
        """Test that consumers can inject their own logger to capture logs to a string."""
        # Create a string buffer to capture log messages
        log_capture = io.StringIO()
        
        # Create a custom handler that writes to our string buffer
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
        
        # Get the library's logger and save its original configuration
        library_logger = logging.getLogger('wyrdbound_rng')
        original_level = library_logger.level
        original_handlers = library_logger.handlers[:]
        
        # Configure the logger with our custom handler
        library_logger.addHandler(handler)
        library_logger.setLevel(logging.DEBUG)
        
        try:
            # Generate names - this should trigger log messages
            generator = Generator(fantasy_names_yaml_path)
            names = generator.generate(1, max_chars=15, algorithm="bayesian")
            
            # Verify name was generated
            assert len(names) == 1
            assert names[0] is not None
            
            # Verify our custom handler captured the debug messages
            captured_logs = log_capture.getvalue()
            assert captured_logs != ""
            
            # Check for expected debug messages in our captured logs
            assert "DEBUG:wyrdbound_rng.bayesian_model:" in captured_logs
            
            # Should have either "Computing" or "Loaded" message depending on cache state
            has_computing_message = "Computing Bayesian probabilities" in captured_logs
            has_loaded_message = "Loaded Bayesian probabilities from cache" in captured_logs
            has_computed_message = "Computed probabilities for" in captured_logs
            
            # Should have at least one of these messages
            assert has_computing_message or has_loaded_message
            
            # If we computed (no cache), we should also see the "computed" message
            if has_computing_message:
                assert has_computed_message
                
        finally:
            # Clean up: restore original logger configuration
            library_logger.removeHandler(handler)
            library_logger.setLevel(original_level)
            # Clear all handlers and restore original ones
            library_logger.handlers.clear()
            library_logger.handlers.extend(original_handlers)

    def test_debug_messages_when_debug_enabled(self, fantasy_names_yaml_path, caplog):
        """Test that debug messages appear when DEBUG logging is enabled."""
        with caplog.at_level(logging.DEBUG):
            generator = Generator(fantasy_names_yaml_path)
            names = generator.generate(1, max_chars=15, algorithm="bayesian")
            
        # Verify name was generated
        assert len(names) == 1
        assert names[0] is not None
        
        # Verify debug messages were logged
        debug_messages = [record for record in caplog.records if record.levelno == logging.DEBUG]
        assert len(debug_messages) > 0
        
        # Check for expected debug messages
        debug_texts = [record.message for record in debug_messages]
        
        # Should have either "Computing" or "Loaded" message depending on cache state
        has_computing_message = any("Computing Bayesian probabilities" in msg for msg in debug_texts)
        has_loaded_message = any("Loaded Bayesian probabilities from cache" in msg for msg in debug_texts)
        has_computed_message = any("Computed probabilities for" in msg for msg in debug_texts)
        
        # Should have at least one of these messages
        assert has_computing_message or has_loaded_message
        
        # If we computed (no cache), we should also see the "computed" message
        if has_computing_message:
            assert has_computed_message

    def test_info_level_shows_no_debug_messages(self, fantasy_names_yaml_path, caplog):
        """Test that debug messages don't appear at INFO level."""
        with caplog.at_level(logging.INFO):
            generator = Generator(fantasy_names_yaml_path)
            names = generator.generate(1, max_chars=15, algorithm="bayesian")
            
        # Verify name was generated
        assert len(names) == 1
        assert names[0] is not None
        
        # Verify no debug messages from bayesian_model were logged
        bayesian_debug_messages = [
            record for record in caplog.records 
            if record.levelno == logging.DEBUG and "bayesian_model" in record.name
        ]
        assert len(bayesian_debug_messages) == 0
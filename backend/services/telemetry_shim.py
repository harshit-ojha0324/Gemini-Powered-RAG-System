"""
Telemetry compatibility shim to handle posthog/chromadb signature issues.

Chromadb v0.4.22 uses an older interface for posthog that may have incompatibilities
with certain posthog versions. This shim patches the posthog.Posthog.capture() method
to accept variable arguments gracefully.
"""

import os
from typing import Any, Optional


def enable_telemetry_with_shim():
    """
    Enable chromadb telemetry with a compatibility shim for posthog.
    
    This function attempts to patch the posthog.Posthog.capture() method
    to handle signature mismatches between chromadb and posthog versions.
    """
    try:
        import posthog
        
        # Store the original capture method
        original_capture = posthog.Posthog.capture
        
        def patched_capture(self, *args, **kwargs):
            """
            Patched capture method that accepts variable arguments.
            Forwards to the original method with correct signature.
            """
            try:
                # Try calling with the original signature first (args are the parameters, not including self)
                if len(args) == 1 and not kwargs:
                    # Classic signature: event
                    return original_capture(self, args[0])  # type: ignore
                elif len(args) == 2 and not kwargs:
                    # Extended signature: distinct_id, event
                    return original_capture(self, args[0], args[1])  # type: ignore
                elif len(args) == 3 and not kwargs:
                    # Extended signature: distinct_id, event, properties
                    return original_capture(self, args[0], args[1], args[2])  # type: ignore
                else:
                    # Fallback: try with all provided arguments
                    return original_capture(self, *args, **kwargs)  # type: ignore
            except TypeError:
                # If original fails, attempt with kwargs
                try:
                    return original_capture(self, *args, **kwargs)  # type: ignore
                except Exception:
                    # Silently ignore telemetry errors
                    pass
        
        # Replace the capture method
        posthog.Posthog.capture = patched_capture
        
        # Enable telemetry for chromadb
        os.environ["CHROMA_TELEMETRY"] = "true"
        
        return True
        
    except Exception as _e:
        # If patching fails, fall back to disabling telemetry
        os.environ["CHROMA_TELEMETRY"] = "false"
        return False


def disable_telemetry():
    """Disable chromadb telemetry."""
    os.environ["CHROMA_TELEMETRY"] = "false"


def is_telemetry_enabled() -> bool:
    """Check if telemetry is enabled."""
    return os.environ.get("CHROMA_TELEMETRY", "false").lower() == "true"

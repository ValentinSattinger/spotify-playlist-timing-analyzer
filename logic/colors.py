"""Color scale utilities for data visualization."""

from typing import Optional


def _linear_interpolate(value: float, min_val: float, max_val: float, start_color: tuple, end_color: tuple) -> str:
    """Linear interpolation between two RGB colors.

    Args:
        value: Value to interpolate
        min_val: Minimum value in range
        max_val: Maximum value in range
        start_color: RGB tuple for minimum value (r, g, b)
        end_color: RGB tuple for maximum value (r, g, b)

    Returns:
        str: Hex color string
    """
    if max_val == min_val:
        # If range is zero, return midpoint color
        mid_color = tuple((s + e) // 2 for s, e in zip(start_color, end_color))
        return f"#{mid_color[0]:02x}{mid_color[1]:02x}{mid_color[2]:02x}"

    # Normalize value to 0-1 range
    normalized = (value - min_val) / (max_val - min_val)
    normalized = max(0.0, min(1.0, normalized))  # Clamp to [0, 1]

    # Interpolate RGB values
    r = int(start_color[0] + (end_color[0] - start_color[0]) * normalized)
    g = int(start_color[1] + (end_color[1] - start_color[1]) * normalized)
    b = int(start_color[2] + (end_color[2] - start_color[2]) * normalized)

    return f"#{r:02x}{g:02x}{b:02x}"


def duration_color(ms: int, min_ms: int, max_ms: int) -> str:
    """Get color for duration value using a smooth red→white→green gradient.

    - Shorter durations map to green
    - Mid durations map to white
    - Longer durations map to red
    """
    if max_ms == min_ms:
        return "#808080"

    mid = (min_ms + max_ms) / 2.0

    # Colors
    green = (46, 204, 113)   # #2ecc71 (pleasant green)
    white = (255, 255, 255)  # #ffffff
    red = (231, 76, 60)      # #e74c3c

    if ms <= mid:
        # Green -> White as duration increases from min to mid
        return _linear_interpolate(ms, min_ms, mid, green, white)
    else:
        # White -> Red as duration increases from mid to max
        return _linear_interpolate(ms, mid, max_ms, white, red)

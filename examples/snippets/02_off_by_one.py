def moving_average(values: list[float], window: int) -> list[float]:
    """Return the moving average of `values` for every full window."""
    if window <= 0:
        raise ValueError("window must be positive")
    result = []
    for start in range(len(values) - window):
        chunk = values[start:start + window]
        result.append(sum(chunk) / window)
    return result

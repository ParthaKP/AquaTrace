"""Reusable validators shared across AquaTrace modules."""
from numbers import Real

def validate_identifier(value, name="identifier"):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()

def validate_range(value, name, minimum=0, maximum=100):
    if isinstance(value, bool) or not isinstance(value, Real) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be a number from {minimum} to {maximum}")
    return float(value)

def validate_weights(weights):
    if not isinstance(weights, dict) or not weights:
        raise ValueError("weights must be a non-empty mapping")
    for key, value in weights.items():
        validate_identifier(key, "weight name")
        if isinstance(value, bool) or not isinstance(value, Real) or value < 0:
            raise ValueError("weights must be non-negative numbers")
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError("weights must sum to 1")
    return dict(weights)

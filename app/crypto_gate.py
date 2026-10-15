"""Cryptographic Action-Binding (HA == HB) enforcement.

Binds the terms an agent was authorized for (HA, derived from the
signed proof-of-intent token) to the terms it actually attempts to
execute (HB, derived from the live execution request). A mismatch
means the action has drifted from what was authorized - regardless of
whether the JWT signature itself still verifies - and must be vetoed.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


class CryptographicActionBinder:
    """Computes and verifies the HA == HB action-binding footprint."""

    @staticmethod
    def generate_action_hash(payload: Dict[str, Any]) -> str:
        """Normalize a dict's keys and return its SHA-256 hex digest."""
        normalized = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @classmethod
    def verify_action_binding(cls, token_payload: Dict[str, Any], requested_payload: Dict[str, Any]) -> bool:
        """Return True iff HA (intent-time hash) == HB (execution-time hash)."""
        h_a = cls.generate_action_hash(token_payload)
        h_b = cls.generate_action_hash(requested_payload)
        return h_a == h_b

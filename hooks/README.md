# Deterministic Hooks

Hooks exist for rules that must not be optional.

## Included

### validate_contracts.py
Validates the JSON contracts themselves and can validate payload fixtures.

### forbid_secrets.py
Rejects likely committed API keys, tokens, and private keys.

### enforce_coordinate_provenance.py
Checks exported fixture/project payloads for coordinate source/provenance requirements.

### pre_export.py
Server-side export boundary guard. The runtime API must call equivalent logic before artifact generation.

The `.claude/settings.json` file wires lightweight repository hooks where practical. Runtime safety must never rely only on Claude Code hooks.

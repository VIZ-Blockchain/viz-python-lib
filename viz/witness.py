"""
Deprecated module: use viz.validator instead.

This shim re-exports Validator/Validators under their old witness names
to preserve backward compatibility during the witness -> validator
terminology migration. Remove during Phase C cleanup.
"""

import warnings

from .validator import Validator, Validators

warnings.warn(
    "viz.witness is deprecated; import from viz.validator instead",
    DeprecationWarning,
    stacklevel=2,
)

Witness = Validator
Witnesses = Validators

__all__ = ["Witness", "Witnesses"]

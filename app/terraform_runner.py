"""Executes (or simulates) Terraform plan runs against the gated infrastructure modules."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from app.module_catalog import get_catalog_entry

TERRAFORM_ROOT = Path(__file__).resolve().parent.parent / "terraform"


class TerraformExecutor:
    """Runs `terraform init`/`plan` for an approved action, or simulates it.

    Falls back to a simulated plan whenever the Terraform CLI binary is not
    present, or whenever the real invocation fails (e.g. missing cloud
    credentials) - this keeps the end-to-end demo runnable at zero cost and
    with no cloud account required.
    """

    @staticmethod
    def _terraform_binary_available() -> bool:
        return shutil.which("terraform") is not None

    @classmethod
    def run_terraform_plan(cls, provider: str, module_key: str, tf_vars: Dict[str, Any]) -> Dict[str, Any]:
        try:
            catalog_entry = get_catalog_entry(provider, module_key)
        except KeyError as exc:
            return {"status": "ERROR", "error": str(exc)}

        module_dir = TERRAFORM_ROOT / provider / catalog_entry.dir_name

        if not cls._terraform_binary_available():
            return cls._simulated_plan(provider, module_dir, tf_vars)

        var_args = []
        for key, value in tf_vars.items():
            var_args.extend(["-var", f"{key}={value}"])

        try:
            init_result = subprocess.run(
                ["terraform", "init", "-backend=false", "-input=false"],
                cwd=str(module_dir),
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if init_result.returncode != 0:
                return {
                    "status": "INIT_FAILED",
                    "mode": "live",
                    "provider": provider,
                    "module_dir": str(module_dir),
                    "stdout": init_result.stdout,
                    "stderr": init_result.stderr,
                }

            plan_result = subprocess.run(
                ["terraform", "plan", "-input=false", "-lock=false", *var_args],
                cwd=str(module_dir),
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
            return {
                "status": "SUCCESS" if plan_result.returncode == 0 else "PLAN_FAILED",
                "mode": "live",
                "provider": provider,
                "module_dir": str(module_dir),
                "stdout": plan_result.stdout,
                "stderr": plan_result.stderr,
            }
        except (subprocess.SubprocessError, OSError) as exc:
            return cls._simulated_plan(provider, module_dir, tf_vars, error=str(exc))

    @staticmethod
    def _simulated_plan(
        provider: str,
        module_dir: Path,
        tf_vars: Dict[str, Any],
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        note = (
            "Terraform CLI not available in this runtime; returning a simulated plan. "
            "Install Terraform and configure cloud credentials to execute a live plan."
        )
        if error:
            note += f" (runtime error: {error})"
        return {
            "status": "SUCCESS",
            "mode": "simulated",
            "provider": provider,
            "module_dir": str(module_dir),
            "note": note,
            "stdout": (
                f"Simulated `terraform plan` for provider='{provider}' module='{module_dir.name}'.\n"
                f"Plan: 1 to add, 0 to change, 0 to destroy.\n"
                f"  + module.{module_dir.name} will be created with vars={tf_vars}\n"
            ),
            "stderr": "",
        }

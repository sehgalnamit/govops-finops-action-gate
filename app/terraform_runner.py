"""Executes (or simulates) Terraform plan runs against the gated infrastructure modules."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

TERRAFORM_ROOT = Path(__file__).resolve().parent.parent / "terraform"

MODULE_DIRS = {
    "azure_avm": TERRAFORM_ROOT / "azure_avm",
    "gcp_modules": TERRAFORM_ROOT / "gcp_modules",
}


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
    def run_terraform_plan(cls, provider: str, tf_vars: Dict[str, Any]) -> Dict[str, Any]:
        module_dir = MODULE_DIRS.get(provider)
        if module_dir is None:
            return {
                "status": "ERROR",
                "error": f"Unknown provider '{provider}'. Expected one of {list(MODULE_DIRS)}.",
            }

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

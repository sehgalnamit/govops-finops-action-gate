# GovOps FinOps Action Gate (Azure AVM & GCP Modules)

Enterprise Agentic Infrastructure Governance microservice implementing the
**American Express Intent Intelligence Framework** paired with
**Cryptographic Action-Binding (`H_A == H_B`)** to govern automated Terraform
deployments across **Azure Verified Modules (AVM)** and **GCP Cloud Modules**.

## 🏛️ Architectural Flow

1. **Agent Intent Capture** — an agent captures its cloud deployment
   requirements and constraints (`POST /api/v1/intent/create`).
2. **Intent Proof Token (`H_A`)** — the service issues a cryptographically
   signed JWT binding the target provider (`azure_avm` / `gcp_modules`),
   action, resource, budget ceiling, and allowed region.
3. **Inline GovOps Gate Verification (`H_A == H_B`)** — at execution time
   (`POST /api/v1/action/execute`), the service decodes the proof token,
   recomputes the execution footprint, and verifies the two hashes match
   before anything else runs. A mismatch (e.g. a `deploy` intent being
   used to request a `destroy`) is vetoed with `HTTP 403` regardless of
   whether the JWT signature itself is valid.
4. **Deterministic FinOps/GovOps Policy Gate** — budget ceiling, region
   allow-list, and destructive-action authorization are evaluated next.
5. **Terraform Execution** — on zero-variance approval, `terraform plan`
   is executed (or simulated) against the Azure AVM or GCP module.

## 🔐 What "Cryptographic Action-Binding" means here

`H_A` and `H_B` are SHA-256 digests of the normalized intent/execution
footprints (not a new cryptographic primitive on top of the JWT). The JWT
signature guarantees the token wasn't tampered with; the `H_A == H_B` check
guarantees the *live execution request* hasn't drifted from what the agent
was actually authorized to do — catching prompt-injection-style
intent-swap attacks that a signature check alone would miss.

## 📦 Module Catalog (real Azure AVM + GCP CFT modules)

This is no longer a single hardcoded module per cloud. `app/module_catalog.py`
maps a `module_key` to a real, independently-plannable Terraform root under
`terraform/<provider>/<dir_name>/`:

| Provider | `module_key` | Real module source |
|---|---|---|
| `azure_avm` | `resource_group` *(default)* | `Azure/avm-res-resources-resourcegroup/azurerm` |
| `azure_avm` | `virtual_network` | `Azure/avm-res-network-virtualnetwork/azurerm` |
| `azure_avm` | `storage_account` | `Azure/avm-res-storage-storageaccount/azurerm` |
| `azure_avm` | `key_vault` | `Azure/avm-res-keyvault-vault/azurerm` |
| `gcp_modules` | `cloud_storage` *(default)* | `terraform-google-modules/cloud-storage/google` |
| `gcp_modules` | `vpc_network` | `terraform-google-modules/network/google` |
| `gcp_modules` | `cloud_sql_postgresql` | `terraform-google-modules/sql-db/google//modules/postgresql` |

`GET /api/v1/catalog` returns this list at runtime. `IntentCaptureRequest`
and `ActionExecutionPayload` both accept an optional `module_key` - if
omitted, the provider's default module is used (keeping the simplest
single-resource demo flow unchanged). `module_key` is part of the
`H_A`/`H_B` footprint, so an intent authorized for `resource_group` cannot
be used to execute against `key_vault` - that mismatch is vetoed with
`HTTP 403` exactly like an action/resource mismatch.

Adding another catalog module (e.g. an AKS/GKE cluster) is a two-step,
code-free-elsewhere change: add an entry to `MODULE_CATALOG` and a new
`terraform/<provider>/<dir_name>/main.tf`.

## 🚀 Quick Start (free, no cloud account required)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run API Server
uvicorn app.main:app --reload

# 3. Run Test Suite
pytest tests/
```

By default, `app/terraform_runner.py` detects whether the `terraform` CLI
binary is on `PATH`. If it isn't (or a real invocation fails, e.g. due to
missing cloud credentials), it transparently falls back to a **simulated**
`terraform plan` response — so the full intent → crypto-binding →
policy-gate → Terraform flow is demoable end-to-end at **zero cost and with
no Azure/GCP account**.

## ☁️ Wiring up a real Terraform plan (optional, still free-tier)

`terraform plan` is read-only (it never provisions anything), so this can
be done at `$0` as long as you stay within your cloud's always-free limits.
Authenticate locally — **never paste credentials into chat/source control**.

### 1. Install the CLIs

```powershell
# Windows (winget)
winget install Hashicorp.Terraform
winget install Microsoft.AzureCLI
winget install Google.CloudSDK
```

```bash
# macOS (Homebrew)
brew install terraform azure-cli google-cloud-sdk
```

### 2. Authenticate interactively (recommended for local demos)

```bash
# Azure — opens a browser login
az login
az account set --subscription <SUBSCRIPTION_ID>   # optional, if you have more than one

# GCP — opens a browser login
gcloud auth application-default login
gcloud config set project <PROJECT_ID>
```

### 3. (Alternative) Authenticate via environment variables (CI-style, no browser)

Set these in your own shell session — never commit them:

```bash
# Azure service principal
export ARM_CLIENT_ID=<app-id>
export ARM_CLIENT_SECRET=<app-secret>
export ARM_SUBSCRIPTION_ID=<subscription-id>
export ARM_TENANT_ID=<tenant-id>

# GCP service account
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export GOOGLE_PROJECT=<project-id>
```

### 4. Verify, then run the gate

```bash
terraform -version
az account show        # confirms Azure auth
gcloud config list     # confirms GCP auth

uvicorn app.main:app --reload
```

Once authenticated and `terraform` is on `PATH`, `TerraformExecutor.run_terraform_plan`
automatically switches from the simulated path to running
`terraform init -backend=false` + `terraform plan` for real against
the resolved catalog module's directory (e.g. `terraform/azure_avm/virtual_network`)
— no code changes needed.

## 🧪 Demo Scenarios

- **Scenario A** — Authorized Azure AVM Resource Group & VNet plan execution.
- **Scenario B** — Authorized GCP Cloud Storage module plan execution.
- **Scenario C** — Prompt-injection / destroy-attack veto (`H_A != H_B`
  triggers `HTTP 403`).
- **Scenario D** — `module_key` drift veto: an intent authorized for
  `resource_group` is replayed against `key_vault` and is vetoed
  (`H_A != H_B`), even though the action/resource strings alone would
  look identical.

## ⚠️ Demo vs. production

- The JWT signing secret (`enterprise-secure-intent-key-2026`) is
  hardcoded for demo purposes — in production, source it from Azure Key
  Vault / GCP Secret Manager, never from source control.
- The intent store is in-memory (`_INTENT_STORE`) — use a durable store
  (Redis/Postgres) for real deployments.
- Destructive-action detection is a simple keyword match
  (`destroy`/`delete`) — a production policy engine should use an
  explicit action allow/deny list.

## Framework reference

- [Intent Intelligence: Building Trust in Agentic Commerce — American Express Technology](https://americanexpress.io/intent-intelligence-building-trust-in-agentic-commerce/)
- [American Express Publishes Intent Intelligence Framework for Trusted Agentic Commerce](https://www.americanexpress.com/en-us/newsroom/articles/innovation/intent-intelligence-framework-agentic-commerce.html)

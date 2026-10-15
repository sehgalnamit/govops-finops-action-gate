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
Authenticate locally — **never paste credentials into chat/source**:

```bash
# Terraform CLI
# https://developer.hashicorp.com/terraform/install

# Azure
az login
# optional: az account set --subscription <SUBSCRIPTION_ID>

# GCP
gcloud auth application-default login
gcloud config set project <PROJECT_ID>
```

Once authenticated, `TerraformExecutor.run_terraform_plan` will run
`terraform init -backend=false` + `terraform plan` for real against
`terraform/azure_avm` or `terraform/gcp_modules`.

## 🧪 Demo Scenarios

- **Scenario A** — Authorized Azure AVM Resource Group & VNet plan execution.
- **Scenario B** — Authorized GCP Cloud Storage module plan execution.
- **Scenario C** — Prompt-injection / destroy-attack veto (`H_A != H_B`
  triggers `HTTP 403`).

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

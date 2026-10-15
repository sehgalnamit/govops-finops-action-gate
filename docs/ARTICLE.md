# Intent Intelligence: Adapting Amex's Agentic Commerce Framework for Enterprise FinOps and Multi-Cloud Governance

> This is the architecture write-up behind [govops-finops-action-gate](https://github.com/sehgalnamit/govops-finops-action-gate).
> For install/run instructions, see the main [README](../README.md).

As AI agents transition from passive conversational advisors to autonomous
enterprise actors, the software ecosystem faces a critical paradigm shift:
how do we grant AI systems execution authority without exposing core
infrastructure to runaway agentic loops, hallucinated state changes, or
prompt injection attacks?

The industry's initial response — relying on post-execution logging or
hoping probabilistic LLMs "behave themselves" — is fundamentally
insufficient for regulated enterprise environments.

American Express highlighted this exact challenge in its Intent
Intelligence Framework for Trusted Agentic Commerce, one of five core
services in the Amex Agentic Commerce Experiences (ACE) Developer Kit.
Amex's core architectural insight is simple yet profound: shift user
intent verification upstream, capturing and cryptographically scoping
authorized constraints before an agent executes a transaction.

By combining Amex's Intent Intelligence model with Cryptographic
Action-Binding (`H_A == H_B`) and deterministic policy execution gates,
this project adapts the framework to secure enterprise cloud
infrastructure, FinOps, and automated provisioning pipelines.

## 🧭 Framework Highlights

The concepts map directly from agentic commerce to agentic infrastructure:

| Intent Intelligence (Amex, payments) | GovOps FinOps Action Gate (this repo, infra) |
|---|---|
| User confirms intent: merchant, max spend, time limits | Agent declares intent: provider, target action/resource, `max_budget_usd`, `allowed_region`, expiry |
| Issuer authenticates the user and issues an **Intent ID** + **Proof of Intent Token** (JWT) | `POST /api/v1/intent/create` issues an `intent_id` + signed `proof_of_intent_token` (JWT) |
| Proof of Intent Token scopes a payment credential and expires on a set date | Proof-of-intent token scopes a Terraform action and expires via the JWT `exp` claim |
| Durable guardrails constrain agent action at execution, to limit disputes/fraud | `POST /api/v1/action/execute` re-verifies the token, enforces `H_A == H_B` action-binding, then applies budget/region/destructive-action policy guardrails before touching infrastructure |

## 1. The Core Problem: The Autonomous Execution Gap

Standard agentic workflows suffer from an architectural flaw: the
probabilistic reasoning layer is directly coupled to the execution runtime.

```mermaid
flowchart LR
    A[User Prompt] --> B[LLM / Agent Loop]
    B -- Direct Mutation, Unvetted --> C[Cloud API / Database / Payment]

    style A fill:#1e293b,color:#fff,stroke:#64748b
    style B fill:#334155,color:#fff,stroke:#94a3b8
    style C fill:#991b1b,color:#fff,stroke:#f87171
```

When an agent is allowed to reason, construct payloads, and directly invoke
tools or cloud endpoints (e.g., Terraform, GCP APIs, Azure Resource
Manager), any prompt drift, model failure, or injection attack leads to
immediate, unvetted state mutations. In consumer commerce, this manifests
as unauthorized purchases. In enterprise FinOps, it manifests as
unauthorized infrastructure scaling, deleted production databases, or
regional compliance breaches.

## 2. Amex Intent Intelligence: The 4-Stage Control Pattern

American Express addresses this by introducing a mandatory Intent Phase
that precedes the Execution Phase:

```mermaid
sequenceDiagram
    autonumber
    actor User as Card Member / Enterprise Operator
    participant Agent as AI Agent Runtime
    participant ACE as Amex ACE / Intent Service
    participant Merchant as Merchant / Cloud API
    participant Issuer as Card Issuer / GovOps Gate

    rect rgb(240, 249, 255)
    note over User, ACE: Stage 1 & 2: Intent Creation & Proof Token Generation
    User->>Agent: Instructs task with explicit bounds (Budget, Region, Target)
    Agent->>ACE: Calls Create Intent API (Merchant, Max Budget, Preferences)
    User->>ACE: Authenticates identity & signs off on intent constraints
    ACE->>ACE: Generates unique Intent ID & signed Proof of Intent Token
    ACE-->>Agent: Returns Intent ID & Proof of Intent Token
    end

    rect rgb(254, 243, 199)
    note over Agent, Issuer: Stage 3 & 4: Scoped Credentials & Execution Verification
    Agent->>ACE: Presents Proof Token to obtain scoped payment/execution credential
    ACE-->>Agent: Issues Scoped Digital Payment Credential
    Agent->>Merchant: Submits Checkout / Infrastructure Execution Payload
    Merchant->>Issuer: Requests Authorization + Passes Intent ID & Proof Token
    Issuer->>Issuer: Validates Payload against Proof Token Constraints (HA == HB)
    alt Constraints Satisfied
        Issuer-->>Merchant: Approved (Transaction Executed)
    else Policy Breach / HA != HB
        Issuer-->>Merchant: Veto / Declined (HTTP 403)
    end
    end
```

1. **Create & Confirm Intent (Create Intent API):** Captures explicit user
   instructions and boundary constraints — maximum budget ceiling, allowed
   merchant/provider, and target action — before any transaction starts.
2. **Establish Proof of Intent:** Generates a unique Intent ID and a
   cryptographically signed Proof of Intent Token representing the user's
   explicit authorization payload (`H_A`).
3. **Scope Execution Credentials:** The token scopes the operational
   credentials used during checkout or execution, ensuring downstream
   systems refuse actions that breach authorized parameters.
4. **Apply Intent Throughout Lifecycle:** The Intent ID and Proof Token act
   as inline controls across every subsequent hop, verifying that requested
   actions (`H_B`) match authorized intent (`H_A`) prior to state mutation.

## 3. Translating Amex Intent Intelligence to Multi-Cloud FinOps Governance

Applied to cloud orchestration — provisioning Azure Verified Modules (AVM)
or GCP Cloud Foundation Toolkit (CFT) modules — the Amex pattern becomes an
inline GovOps Action Gate sitting between an agent's probabilistic
reasoning (System 2) and deterministic infrastructure execution (System 1):

```mermaid
flowchart TD
    subgraph Probabilistic_Perception["SYSTEM 2: Probabilistic Perception Layer"]
        User([Operator / User]) -->|1. Define Intent & Constraints| AgentRuntime[AI Agent / LLM Router]
        AgentRuntime -->|2. Create Intent Request| IntentAPI[Intent API Gateway]
        IntentAPI -->|3. Issue Signed Token| TokenGen[Proof of Intent Generator]
        TokenGen -->|4. Return JWT Proof Token| AgentRuntime
    end

    subgraph Deterministic_Control["SYSTEM 1: Deterministic GovOps Control Plane"]
        AgentRuntime -->|5. Submit Action Payload HB + Token| Interceptor[GovOps Action Gate Interceptor]

        Interceptor --> Decrypt[Decode & Verify JWT Token]
        Decrypt --> HashCheck{Cryptographic Binding<br/>Assert HA == HB}

        HashCheck -- Mismatch HA != HB --> SecurityVeto[HTTP 403: Security Veto<br/>Injection / Drift Alert]

        HashCheck -- Match HA == HB --> PolicyEngine[Deterministic Policy Engine]

        PolicyEngine --> BudgetCheck{Requested Budget <= Max Budget?}
        BudgetCheck -- Exceeded --> BudgetVeto[HTTP 403: FinOps Budget Veto]

        BudgetCheck -- Passed --> ActionCheck{Action Permitted?<br/>No unauthorized Destroy}
        ActionCheck -- Forbidden --> ActionVeto[HTTP 403: Policy Veto]

        ActionCheck -- Passed --> TFExecutor[Terraform Plan Runner]
    end

    subgraph Infrastructure_Execution["CLOUD RUNTIME EXECUTION"]
        TFExecutor -->|Resolve module_key in catalog| Azure[Azure AVM: resource_group / virtual_network / storage_account / key_vault]
        TFExecutor -->|Resolve module_key in catalog| GCP[GCP CFT: cloud_storage / vpc_network / cloud_sql_postgresql]
    end

    style Probabilistic_Perception fill:#0f172a,color:#fff,stroke:#38bdf8
    style Deterministic_Control fill:#1e1b4b,color:#fff,stroke:#818cf8
    style Infrastructure_Execution fill:#064e3b,color:#fff,stroke:#34d399
    style SecurityVeto fill:#7f1d1d,color:#fff,stroke:#f87171
    style BudgetVeto fill:#7f1d1d,color:#fff,stroke:#f87171
    style ActionVeto fill:#7f1d1d,color:#fff,stroke:#f87171
```

In plain terms, this is the same flow the main [README](../README.md#-architectural-flow)
summarizes as five steps: capture intent, issue a signed proof token
(`H_A`), verify `H_A == H_B` at execution, apply deterministic FinOps/GovOps
policy, and only then run `terraform plan`.

## 4. Complete End-to-End Execution Dataflow

This state diagram traces an incoming intent through JWT issuance,
cryptographic hash verification, deterministic policy validation, and
Terraform execution.

```mermaid
stateDiagram-v2
    [*] --> IntentCapture: Operator inputs intent (Budget, Provider, Region, module_key)

    state "1. Intent Generation" as IntentCapture {
        [*] --> GenerateJWT: Validate request parameters
        GenerateJWT --> IssueToken: Sign JWT with enterprise secret
        IssueToken --> [*]
    }

    IntentCapture --> ActionRequest: Agent submits Execution Payload (HB fields) + JWT

    state "2. Inline GovOps Verification" as Verification {
        [*] --> DecodeJWT: Verify JWT signature & expiry
        DecodeJWT --> ComputeHA: Derive HA from decoded token fields
        ComputeHA --> ComputeHB: Derive HB from execution request fields
        ComputeHB --> CheckHash: SHA-256(HA) == SHA-256(HB) ?
        CheckHash --> HashPassed: HA == HB
        CheckHash --> HashFailed: HA != HB (Tampered / Drifted / Injected)
        HashPassed --> [*]
        HashFailed --> [*]
    }

    ActionRequest --> Verification

    Verification --> RejectTransaction: HashFailed (Cryptographic Veto, HTTP 403)
    Verification --> PolicyEngine: HashPassed

    state "3. Deterministic Policy Engine" as PolicyEngine {
        [*] --> CheckBudget: Compare requested_budget vs max_budget_usd
        CheckBudget --> CheckRegion: Budget OK
        CheckRegion --> CheckDestructive: Compare region vs allowed_region
        CheckDestructive --> [*]: No unauthorized destroy/delete
    }

    CheckBudget --> RejectTransaction: Budget Exceeded (HTTP 403)
    CheckRegion --> RejectTransaction: Region Violation (HTTP 403)
    CheckDestructive --> RejectTransaction: Destructive Action Veto (HTTP 403)

    PolicyEngine --> Infrastructure: Policy Approved

    state "4. Infrastructure Runtime Execution" as Infrastructure {
        [*] --> ResolveModule: Resolve module_key in provider catalog
        ResolveModule --> TFInit: Exec 'terraform init -backend=false'
        TFInit --> TFPlan: Exec 'terraform plan' (or simulated plan if CLI/credentials unavailable)
        TFPlan --> [*]
    }

    Infrastructure --> TransactionSuccess: Return HTTP 200 + Terraform plan output
    RejectTransaction --> [*]
    TransactionSuccess --> [*]
```

> Note: `RejectTransaction --> [*]` and `TransactionSuccess --> [*]` both
> legitimately converge on the diagram's single shared final state — a
> state machine has exactly one top-level final pseudostate, so every
> terminal path (approved or vetoed) funnels into it. That's expected UML
> `stateDiagram-v2` behavior, not a modeling error.

## 5. Comparative Matrix: Traditional Agents vs. Intent-Gated Architecture

| Architectural Feature | Traditional Agentic Architecture | Amex Intent Intelligence / GovOps Action Gate |
|---|---|---|
| Execution Authority | Delegated directly to probabilistic LLM | Reserved for deterministic control plane |
| Constraint Timing | Evaluated post-execution or in-prompt | Evaluated upstream, prior to state mutation |
| Security Mechanism | System prompts & LLM guardrails | Cryptographic Action-Binding (`H_A == H_B`) & JWT tokens |
| Audit Trail | Unstructured conversational logs | Immutable Intent ID linked to hashed execution payloads |
| Malicious Injection Resilience | Low (vulnerable to prompt manipulation) | High (payload modifications fail hash check `H_A != H_B`) |
| Regulatory & FinOps Alignment | Probabilistic / non-deterministic | Zero-variance compliance & bounded budget ceilings |

## Conclusion

The release of American Express's Intent Intelligence Framework marks an
industry milestone: it formalizes the shift from unconstrained model
autonomy to intent-bounded execution. Whether applied to consumer payment
rails or enterprise multi-cloud FinOps, the core engineering imperative
remains identical: never grant a probabilistic model direct execution
authority. By leveraging LLMs for perception and orchestration (System 2)
while enforcing state mutations through cryptographically bound,
deterministic gates (System 1), enterprises can safely deploy agentic
workflows at scale — maximizing speed while retaining absolute control over
security, budget, and compliance.

## Framework reference

- [Intent Intelligence: Building Trust in Agentic Commerce — American Express Technology](https://americanexpress.io/intent-intelligence-building-trust-in-agentic-commerce/)
- [American Express Publishes Intent Intelligence Framework for Trusted Agentic Commerce](https://www.americanexpress.com/en-us/newsroom/articles/innovation/intent-intelligence-framework-agentic-commerce.html)
- Reference implementation: [sehgalnamit/govops-finops-action-gate](https://github.com/sehgalnamit/govops-finops-action-gate)

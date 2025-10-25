

This page gives a high-level overview of the system, centring explanations on three diagrams:
1) Project setup and scoring from metrics/weights
2) Recommendation loop + cost tokens
3) Finish & report generation (with embedded graph)

---

## Background

| Term               | Meaning                                                                         |
| ------------------ | --------------------------------------------------------------------------      |
| **Project**        | Represents a building scenario including metrics and applied interventions      |
| **Metrics**        | Building attributes that influence sustainability scores                        |
| **Interventions**  | Strategies users can apply (e.g., Structural Optimisation, Low carbon concrete) |
| **Themes**         | Weighting priorities (e.g. energy, biodiversity)                                |
| **Runtime Scores** | Intermediate score calculations per project-intervention                        |



## 1) Project Setup & Scoring

Computes base scores from `metric_effects`, stores them in `runtime_scores`, then applies normalised theme weights from `project_theme_weightings` to produce `theme_weighted_effectiveness`.

```mermaid
%%{init: { "flowchart": { "nodeSpacing": 20, "rankSpacing": 28, "useMaxWidth": false }}}%%
flowchart LR
  classDef fe fill:#F0F9FF,stroke:#0284c7,color:#0c4a6e
  classDef be fill:#F8FAFC,stroke:#334155,color:#0f172a
  classDef db fill:#ECFDF5,stroke:#047857,color:#064e3b
  classDef legend fill:#FFF7ED,stroke:#ea580c,color:#7c2d12

  subgraph Frontend
    direction TB
    A1["(1) Web form: building metrics + project name"]:::fe
    A2["(2) Weighting sliders: theme weights"]:::fe
  end

  subgraph Backend
    direction TB
    B1["(3) POST /projects/:id/metrics"]:::be
    B2["(4) Compute metric_effects → base scores"]:::be
    B3["(5) PUT /projects/:id/theme-scores"]:::be
    B4["(6) Normalise theme weights & apply to runtime_scores"]:::be
  end

  subgraph Database
    direction TB
    D1["projects"]:::db
    D2["metric_effects"]:::db
    D3["runtime_scores (per project × intervention)"]:::db
    D4["project_theme_weightings (weight_raw, weight_norm)"]:::db
  end

  %% Flow
  A1 -->|"payload: metrics"| B1
  B1 -->|"insert project + metrics"| D1
  B1 --> B2
  B2 -->|"read rules"| D2
  B2 -->|"UPSERT base_effectiveness → runtime_scores"| D3

  A2 -->|"payload: {theme_id: weight_raw}"| B3
  B3 -->|"UPSERT weight_raw"| D4
  B3 --> B4
  B4 -->|"renormalise weight_norm; multiply into theme_weighted_effectiveness"| D3

  %% Legend
  subgraph L["Legend"]
    direction TB
    L1["Frontend"]:::fe
    L2["Backend"]:::be
    L3["Database"]:::db
  end
  class L legend


```
## 2) Recommendation Loop + Cost Tokens

```mermaid
%%{init: { "flowchart": { "nodeSpacing": 20, "rankSpacing": 28, "useMaxWidth": false}}}%%
flowchart LR
  classDef fe fill:#F0F9FF,stroke:#0284c7,color:#0c4a6e
  classDef be fill:#F8FAFC,stroke:#334155,color:#0f172a
  classDef db fill:#ECFDF5,stroke:#047857,color:#064e3b
  classDef legend fill:#FFF7ED,stroke:#ea580c,color:#7c2d12

  subgraph Frontend
    direction TB
    F1["(1) Show top N"]:::fe
    F2["(2) User selects intervention"]:::fe
    F3["(5) Cost panel (tokens)"]:::fe
  end

  subgraph Backend
    direction TB
    B1["GET /projects/:id/recommendations"]:::be
    B2["POST /projects/:id/apply"]:::be
    B3["Apply intervention_effects → recompute"]:::be
    B4["GET /projects/:id/costs"]:::be
  end

  subgraph Database
    direction TB
    D1["runtime_scores (ranked)"]:::db
    D2["implemented_interventions"]:::db
    D3["intervention_effects (± multipliers)"]:::db
    D4["interventions (cost_weight, theme_id)"]:::db
    D5["config (token step_size)"]:::db
    D6["project_theme_weightings (decay α; floor)"]:::db
  end

  %% fetch recommendations
  F1 -. fetch .-> B1
  B1 -->|"read & rank by theme_weighted_effectiveness"| D1
  B1 --> F1

  %% apply selection
  F2 -->|"payload: intervention_id"| B2
  B2 -->|"insert"| D2
  B2 --> B3

  %% recompute after apply
  B3 -->|"read effects rules"| D3
  B3 -->|"adjust runtime_scores via multipliers"| D1
  B3 -->|"decay chosen theme weight: weight_raw *= α; renormalise"| D6
  B3 -. triggers next fetch .-> B1

  %% costs
  B2 --> B4
  B4 -->|"read step_size"| D5
  B4 -->|"join selections"| D2
  B4 -->|"join interventions.cost_weight"| D4
  B4 -->|"return token count"| F3

  %% Legend
  subgraph L["Legend"]
    direction TB
    L1["Frontend"]:::fe
    L2["Backend"]:::be
    L3["Database"]:::db
  end
  class L legend

```


## 3) Finish & Report

```mermaid
%%{init: { "flowchart": { "nodeSpacing": 20, "rankSpacing": 28 }}}%%
flowchart LR
  classDef fe fill:#F0F9FF,stroke:#0284c7,color:#0c4a6e
  classDef be fill:#F8FAFC,stroke:#334155,color:#0f172a
  classDef db fill:#ECFDF5,stroke:#047857,color:#064e3b
  classDef legend fill:#FFF7ED,stroke:#ea580c,color:#7c2d12

  subgraph Frontend
    direction TB
    F1["(1) Finish & Generate Report"]:::fe
    F2["(3) Report viewer / PDF download"]:::fe
  end

  subgraph Backend
    direction TB
    B1["GET /projects/:id/report  (HTML/PDF + embedded graph)"]:::be
  end

  subgraph Database
    direction TB
    D1["runtime_scores (final)"]:::db
    D2["implemented_interventions (chronological)"]:::db
  end

  F1 --> B1
  B1 -->|"read final scores & selections"| D1
  B1 --> D2
  B1 --> F2

  %% Legend
  subgraph L["Legend"]
    direction TB
    L1["Frontend"]:::fe
    L2["Backend"]:::be
    L3["Database"]:::db
  end
  class L legend

```
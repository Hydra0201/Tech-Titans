| Term               | Meaning                                                                    |
| ------------------ | -------------------------------------------------------------------------- |
| **Project**        | Represents a building scenario including metrics and applied interventions |
| **Metrics**        | Building attributes that influence sustainability scores                   |
| **Interventions**  | Strategies users can apply (e.g., green roof, insulation)                  |
| **Themes**         | Weighting priorities (e.g. energy, biodiversity)                           |
| **Runtime Scores** | Intermediate score calculations per project-intervention                   |


```mermaid
%%{init: { "flowchart": { "nodeSpacing": 20, "rankSpacing": 28 }}}%%
flowchart LR
  subgraph Frontend
    direction TB
    F_Form["Web form: enter building metrics + project name"]
    F_Sliders["Weighting sliders (user adjusts & submits)"]
  end

  subgraph Backend
    direction TB
    B_PostMetrics["POST /projects/:id/metrics"]
    B_CheckRules["Compute base scores from metric_effects → upsert"]
    B_PostWeights["PUT /api/projects/:id/theme-scores"]
    B_ApplyWeights["Normalize & apply weightings to runtime scores"]
  end

  subgraph Database
    direction TB
    D_Projects[(projects)]
    D_MetricEffects[(metric_effects)]
    D_Runtime[(runtime_scores)]
  end

  F_Form -->|Submit| B_PostMetrics
  B_PostMetrics -->|Insert project + metrics| D_Projects
  B_PostMetrics --> B_CheckRules
  B_CheckRules -->|Read rules| D_MetricEffects
  B_CheckRules -->|Upsert scores| D_Runtime

  F_Sliders -->|Submit weights| B_PostWeights
  B_PostWeights --> B_ApplyWeights
  B_ApplyWeights -->|Update scores| D_Runtime

```

```mermaid
%%{init: { "flowchart": { "nodeSpacing": 20, "rankSpacing": 28 }}}%%
flowchart LR
  subgraph Frontend
    direction TB
    F_ShowTop3["Display top 3 interventions"]
    F_Select["User selects one intervention"]
    F_CostPanel["Cost panel: number of cost tokens"]
  end

  subgraph Backend
    direction TB
    B_GetTop3["GET /projects/:id/recommendations"]
    B_PostImplement["POST /projects/:id/apply"]
    B_UpdateAfterImpl["Apply intervention effects → update runtime scores"]
    B_Costing["GET /projects/:id/costs (return cost tokens)"]
  end

  subgraph Database
    direction TB
    D_Runtime[(runtime_scores)]
    D_Implemented[(implemented_interventions)]
    D_InterventionEffects[(intervention_effects)]
    D_Interventions[(interventions)]
    D_Config[(config)]
  end

  %% Show & fetch recommendations
  F_ShowTop3 -. fetch .-> B_GetTop3
  B_GetTop3 -->|Read ranked scores| D_Runtime
  B_GetTop3 --> F_ShowTop3

  %% Apply selection and recompute
  F_Select -->|Submit selection| B_PostImplement
  B_PostImplement -->|Insert| D_Implemented
  B_PostImplement --> B_UpdateAfterImpl
  B_UpdateAfterImpl -->|Read effects| D_InterventionEffects
  B_UpdateAfterImpl -->|Update scores| D_Runtime
  B_UpdateAfterImpl -. next fetch .-> B_GetTop3

  %% Costing (tokens depend on selections)
  B_PostImplement --> B_Costing
  B_Costing -->|Read step_size| D_Config
  B_Costing -->|Read selected impls| D_Implemented
  B_Costing -->|Join for cost_weight| D_Interventions
  B_Costing --> F_CostPanel
```

```mermaid
%%{init: { "flowchart": { "nodeSpacing": 20, "rankSpacing": 28 }}}%%
flowchart LR
  subgraph Frontend
    direction TB
    F_Done["Finish & Generate Report"]
    F_Report["Report viewer / PDF download"]
  end

  subgraph Backend
    direction TB
    B_Report["GET /projects/:id/report (HTML/PDF incl. graph)"]
  end

  subgraph Database
    direction TB
    D_Runtime[(runtime_scores)]
    D_Implemented[(implemented_interventions)]
  end

  F_Done --> B_Report
  B_Report -->|Read scores & selections| D_Runtime
  B_Report --> D_Implemented
  B_Report --> F_Report
```
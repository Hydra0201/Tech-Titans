## Areas for Extension

This document outlines key problems which must be resolved to bring CarbonBalance to production quality.

## 1) Extensive Testing

A key component to the success of this app is the continued development and testing of datasets. By this I mean that base effectiveness values and the various recommendations rules will necessarily require a significant amount of tweaking and testing to correctly reflect CostPlan's sustainability knowledge and to ensure the program logic is capable of doing so. Unfortunately, no such testing was completed during this development cycle due to time pressures, lack of synchronisation between the backend and frontend, and lack of immediately available data.

Areas for testing include:
- Costing
- Base effectiveness values
- Metric rules
- Intervention rules
- Stage rules
- Theme weightings

## 2) Data Quality, Versioning & Governance

The system currently relies on manually curated Excel spreadsheets for core data (interventions, themes, rules). There is no formal process to manage chagnes, detect errors, or trace the evolution of decisions.

**Required improvements**
- Data versioning
- Quality control checks (duplicate interventions, conflicting rules, circular dependencies)



## 3) Business Validation & Alignment with Real Projects

The rules engine and scoring model were not validated against actual CostPlan projects during development, instead the logic was developed using a set of dummy data. To ensure redibility, expert validation must be an absolute priority.

**Required improvements**
- Test the model using historical case studies
- Compare system recommendations vs. expert decisions
- Track how the model's accuracy drifts as new sustainability strategies emergy, determine whether these require core logic changes

## 4) UX Design & User Guidance

The prototype lacks meaningful user guidance, with certain aspects of functionality appearing unclear, e.g. there is no meaningful description of what a theme weighting might represent.

**Required improvements**
- Add tooltip explanations of key concepts (e.g. cost tokens, base effectiveness, ...)
- Make outputs interpretable, the user should have an idea of:
    - Why was this recommendation given?
    - What rule/s or metric/s impacted this score?


## 5) Frontend Integration

Some key features are not surfaced on the frontend, specifically:
- Costing
- Data ingestion


## 6) Feature Maturation

Some features were implemented in a naive manner due to time constraints, and would benefit from further thought and development:
- Report
- Graph
- Data ingestion
- Costing
- Authentication

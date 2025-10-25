# Areas Requiring Improvement

This page outlines key areas flagged for technical improvement.

## 1) Auth & Roles
- Add additional roles
- Gate account creation behind admin status

## 2) Data Ingestion
- Improve interface
- Allow upload via API route rather than reading hardcoded file location
    - Offer template download route
- Enforce sheet/column schema

**Next step:** validate against a schema and return `{inserted, updated, skipped, errors}` per section.

## 3) Input Validation
- Replace ad-hoc coercion with requestion schemas


## 4) Transactions & Orchestration
- Make ingestion atomic and add a dry-run mod
- In some way enforce ordering of API calls
    - Currently, app requires calls are made in specific order for correctness

## 5) Graph & Report
- **Improve presentation**
    - Add letterhead, disclaimers, branding

## 6) Explainability
- Consistently add and expose rule explanations
- Provide feedback on intervention relationships, i.e. on hover a user might be able to see that an intervention conflicts with another they've already selected
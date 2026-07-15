# Exposure and Outcome Definition Patterns

## Medication, fluid, and blood-product exposure

- Decide whether the concept requires an order, dispensing, administration, start of infusion, delivered dose, cumulative dose, rate, or duration.
- Use `prescriptions` or `pharmacy` for order context and `emar`/`emar_detail` or ICU event sources for administration evidence as appropriate.
- Normalize generic names, routes, units, dose forms, status, and canceled or held events.
- Define overlapping administrations, dose changes, boluses, and treatment episodes before aggregation.
- For treatment-effect questions, distinguish baseline use, assignment, grace period, switching, discontinuation, and rescue treatment.

## Procedures, devices, and organ support

- Distinguish ordered, attempted, completed, and ongoing states.
- Combine procedure codes with `procedureevents`, device charting, ventilation, oxygen-delivery, or other direct evidence when the question requires actual receipt.
- Define insertion or start, removal or stop, gaps, restarts, and transfer between modalities.
- For duration, establish whether the endpoint is elapsed clock time, calendar days, event-record duration, or days alive and free of support.

## Infection and clinical-state phenotypes

- State whether the definition captures suspected infection, confirmed microbiology, clinician diagnosis, treatment, organ dysfunction, or a combination.
- Align culture collection, antimicrobial administration, diagnostic coding, and physiologic evidence within a justified window.
- Keep contamination, surveillance cultures, prophylaxis, and infection present on admission distinct when relevant.
- Validate rates, organism/source distributions, and timing against clinical expectations; treat an algorithmic phenotype as imperfect measurement.

## Mortality, readmission, and complications

- Distinguish ICU, hospital, fixed-horizon, and available post-discharge mortality. State timestamp resolution and follow-up completeness.
- Define whether discharge alive competes with an in-hospital event rather than censoring it by assumption.
- For readmission, specify same hospital versus any observable return, planned versus unplanned status, transfer handling, and the observation window.
- Require complications to be new or worsened after follow-up starts; separate prevalent conditions from incident outcomes.

## Composite outcomes

- Give a clinical rationale for combining components and identify the first qualifying component.
- Publish every component flag, event time, and component-specific rate alongside the composite.
- Avoid a composite dominated by a frequent but less important component without making that dominance visible.
- Handle competing events and recurrent components consistently. Do not mix fixed-horizon binary and time-to-event definitions silently.

## Adjudication and validation

- Build an evidence table containing source, code/itemid, label, event time, value/dose, unit, status, and rule matched.
- Compare sources with a concordance matrix and inspect discordant cases without exposing restricted patient data outside the approved environment.
- Use blinded manual review where source material and governance permit it; record sampling, reviewer roles, disagreements, and resolution.
- Report positive predictive agreement, sensitivity against available reference evidence, or other validation measures only when the reference standard supports them.

## Provenance and QC artifacts

Retain:

- human-readable definition and version;
- code and item lists with matched descriptions;
- source-table and timestamp-field inventory;
- unit/status normalization map;
- event-level audit evidence in the governed environment;
- aggregation SQL and target-grain duplicate checks;
- source concordance and definition-sensitivity tables;
- final variable dictionary with window, type, unit, missingness, and limitations.

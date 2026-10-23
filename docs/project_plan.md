# Project plan

## Release objective

Build a three-minute review experience that lets a hiring manager understand the decision, inspect the economics and reproduce the evidence without reading source code first.

## Completed foundation

- point-in-time Vietnam regulatory and market research;
- amortising loan cash-flow and survival schedule;
- expected-loss calculation using monthly marginal default;
- regulatory, economic and management capital views;
- numerical price-floor solver for the RAROC hurdle;
- approve, reprice, manual-review and decline policy;
- deterministic 4,000-application synthetic portfolio;
- formula-driven Excel workbook with portfolio and sensitivity views;
- automated formula, monotonicity and policy boundary tests.

## Next release layer

1. Executive decision memo with recommendation, economics attribution and implementation gates.
2. Interactive dashboard with single-loan pricing, portfolio mix and stress scenarios.
3. Model card covering validation, monitoring, fairness and prohibited uses.
4. Scenario suite for funding shock, PD/LGD stress, prepayment and operating-cost variance.
5. Independent reconciliation between Python, Excel and dashboard outputs.
6. README preview images, release notes and GitHub Pages deployment.

## Definition of done

- a reviewer can understand the business decision in three minutes;
- the reference loan reconciles across Python, Excel and dashboard to stated tolerances;
- price floors increase monotonically with PD, LGD, funding cost and the RAROC hurdle;
- decision rules expose missing inputs and policy exceptions rather than converting them to zero;
- every external benchmark has a date, source and interpretation boundary;
- the release separates demonstration evidence from claims that require lender-owned data;
- tests and report generation pass from a clean checkout.


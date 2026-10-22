# Model Card — Vietnam Loan Pricing & RAROC Lab

## Model identity

- **Model type:** application-level loan pricing, profitability and policy prototype.
- **Product:** unsecured personal instalment lending in VND.
- **Primary outputs:** minimum hurdle-clearing APR, expected loss, allocated capital, annualised RAROC and approve/reprice/review/decline action.
- **Current version:** portfolio prototype, not validated for production use.
- **As-of date:** 22 October 2026.

## Intended use

The model is designed for portfolio analysis, pricing-policy design, scenario testing and management discussion. It demonstrates how underwriting risk, affordability, funding, operating cost, expected loss, capital and tax can be translated into a controlled lending decision.

Appropriate uses include:

- testing whether a quoted APR meets a target RAROC;
- comparing price floors across risk tiers and loan structures;
- estimating decision migration under funding and credit stress;
- identifying applications that require repricing or manual review;
- supporting model-development, pricing and credit-risk interviews.

## Prohibited use

Do not use the repository to make real lending decisions, determine legal rate limits, represent an approved bank policy, or infer Vietnamese market approval rates. It does not contain customer data and has not completed independent validation, fair-lending review, legal review, security testing or production monitoring approval.

## Inputs

The application record includes principal, term, annual PD, LGD, quoted APR, upfront fee, monthly income, existing monthly debt and a data-quality flag. Scenario inputs include PD and LGD stress, funding and liquidity cost, servicing cost, capital buffer and RAROC hurdle.

All 4,000 portfolio records are synthetic and generated with a deterministic seed. Public information is used only to frame broad market or regulatory context.

## Method summary

The engine builds a monthly amortisation schedule and survival-weighted expected cash flows. Expected loss is calculated from marginal default, exposure at default and LGD. Regulatory, economic and management-floor capital views are calculated separately; allocated capital is the maximum of the three. The minimum APR is solved numerically so annualised after-tax RAROC meets the selected hurdle.

The workbook retains both a 10-basis-point Excel rate grid and an independent Python exact-solver benchmark. Their difference is controlled in the `Audit` sheet.

## Decision logic

1. Route records with a data-quality flag to manual review.
2. Decline records that breach PD or affordability boundaries.
3. Route infeasible price solutions to manual review.
4. Reprice eligible records whose quoted APR is below the price floor.
5. Approve eligible records whose quoted APR meets or exceeds the floor.

## Validation evidence

- 11 automated tests cover amortisation, solver behaviour, monotonic risk relationships, policy gates, scenario counts and report reconciliation.
- The Excel workbook reconciles monthly payment, EAD, income, costs, expected loss, capital and RAROC to the Python engine.
- Base, Downside and Severe median price floors increase monotonically.
- Every scenario reconciles to 4,000 decisions.

Passing tests establish implementation consistency, not production fitness.

## Key limitations

- Synthetic applications do not reproduce real borrower mix, selection effects or repayment behaviour.
- PD and LGD are inputs rather than independently estimated and calibrated models.
- Economic capital is a portfolio proxy, not an approved internal-model or ICAAP calculation.
- Prepayment, cure, recovery timing, stage migration, ECL staging and behavioural maturity are outside scope.
- The pricing engine does not model acquisition elasticity, competitor response or customer lifetime value.
- The maximum management APR is an internal scenario boundary, not a legal conclusion.

## Monitoring expectations

Before any real-world use, owners should monitor approval and override rates, observed-to-expected defaults, funding cost, price-floor distributions, RAROC, data-quality exceptions and performance by risk tier and protected or sensitive customer groups where legally permitted. Trigger breaches should lead to investigation, recalibration or policy suspension.

## Governance path to production

Production use would require governed source data, model-development documentation, independent validation, legal and compliance approval, fair-lending assessment, security review, change control, access controls, audit logging, calibrated thresholds and a formally approved monitoring plan.

## Ownership

This repository is a portfolio case study. Assumptions, outputs and source boundaries are versioned so reviewers can reproduce and challenge the analysis.

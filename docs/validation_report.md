# Validation report

## Executive conclusion

The prototype passes its current deterministic control suite and is fit for portfolio demonstration, policy design discussion and controlled sensitivity analysis. It is not approved for production lending decisions. The largest remaining validation gap is empirical calibration against observed Vietnamese application, default, recovery and prepayment data.

## Validation perimeter

The control suite covers four layers:

1. **Contractual mechanics** — payment calculation, zero-rate handling and principal amortisation.
2. **Risk economics** — positive capital for risky loans and directional response to PD and funding stress.
3. **Decision policy** — affordability declines and data-quality routing to manual review.
4. **Reporting integrity** — scenario population reconciliation, price-bridge reconciliation and monotonic stressed price floors.

## Automated controls

| Control family | Current evidence | Result |
|---|---|---|
| Amortisation | Payment schedule fully repays principal | Pass |
| Solver | Minimum feasible APR clears the configured RAROC hurdle | Pass |
| Expected loss | Higher PD increases expected loss | Pass |
| Pricing sensitivity | Higher PD or funding cost increases the price floor | Pass |
| Economic capital | Risky exposure produces positive economic capital | Pass |
| Affordability policy | Unaffordable application is declined | Pass |
| Data quality | Flagged record is routed to review | Pass |
| Scenario totals | Every scenario reconciles to 4,000 applications | Pass |
| Price bridge | Component bridge reconciles to the exact solver floor | Pass |
| Scenario ordering | Price floors rise from Base to Downside to Severe | Pass |

The repository runs 11 automated tests on Python 3.11 and 3.12 through GitHub Actions. The workflow also rebuilds deterministic reports and compares them with the committed evidence pack using explicit cross-platform numerical tolerances (`rel_tol=1e-12`, `abs_tol=1e-8`). This prevents machine-level floating-point noise from masking the distinction between harmless representation differences and economically meaningful drift.

## Independent workbook reconciliation

The Excel audit sheet compares key workbook outputs against the Python reference implementation. The current reference case reconciles monthly payment, average performing EAD, interest income, funding cost, expected loss, after-tax profit, allocated capital and annualised RAROC. The 10 bp Excel price grid is also compared with the exact numerical Python floor.

## Sensitivity expectations

The following monotonic relationships are treated as model invariants:

- price floor increases as PD, LGD, funding cost or target RAROC increases;
- expected loss increases as PD or LGD increases;
- affordability pressure increases as principal increases or term shortens;
- approval share falls and repricing/decline migration rises under adverse scenarios.

A breach of these relationships is a validation failure unless it is explained by a policy boundary or a competing nonlinear effect.

## Material limitations

- PD and LGD are scenario inputs rather than statistically calibrated estimates.
- Prepayment, delinquency cure, collections timing and vintage seasoning are not modelled.
- Economic capital is a portfolio proxy, not an approved IRB or ICAAP model.
- Operating, liquidity and funding costs are decision assumptions rather than product-level finance allocations.
- Synthetic applications demonstrate workflow behavior but cannot establish market approval, loss or profitability rates.
- Fair-lending, privacy, conduct and adverse-action requirements require separate legal and compliance review.

## Production validation backlog

Before production consideration, the model requires:

1. out-of-time PD calibration and discrimination evidence;
2. observed recovery and workout-cost LGD calibration;
3. prepayment and early-settlement behavior;
4. reject-inference and selection-bias assessment;
5. challenger pricing and capital specifications;
6. subgroup outcome and conduct-risk testing;
7. data lineage, access controls and change management;
8. independent model validation and approval by credit, finance and model-risk owners.

## Reproduction

```bash
python -m unittest discover -s tests -v
python -m scripts.run_portfolio
python -m scripts.build_sensitivity
python -m scripts.build_extended_reports
```

All committed portfolio outputs are deterministic for the configured seed.

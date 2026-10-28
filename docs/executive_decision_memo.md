# Executive decision memo

**Case:** Vietnam unsecured personal instalment loan pricing  
**Evidence cutoff:** 22 October 2026  
**Decision status:** Controlled shadow use only  
**Portfolio:** 4,000 synthetic applications; VND558.2 billion requested exposure

## Decision

Use the engine as a governed application-time pricing and policy reference, not as an autonomous lending system. The Base scenario supports approval for eligible applications that clear affordability, the PD limit, the management APR cap and the 16% RAROC hurdle. Downside and Severe scenarios require rapid repricing or policy tightening rather than assuming the Base offer remains economic.

## Base portfolio readout

| Measure | Result |
| --- | ---: |
| Approve | 68.75% |
| Reprice | 6.03% |
| Manual review | 1.40% |
| Decline | 23.83% |
| Approved exposure share | 65.60% |
| Median price floor | 13.80% |
| 75th percentile price floor | 17.65% |
| Median quoted-rate RAROC | 39.40% |

The reference VND100 million, 36-month application with 4% PD, 70% LGD and a 1% upfront fee has an exact price floor of 10.8561%. At an 18% quote, annualised RAROC is 88.61%; the regulatory proxy is the binding capital view at VND4.22 million.

## Stress migration

| Scenario | Approve | Reprice | Review | Decline | Median floor |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base | 68.75% | 6.03% | 1.40% | 23.83% | 13.80% |
| Downside | 7.33% | 57.13% | 3.63% | 31.93% | 18.40% |
| Severe | 0.00% | 45.33% | 11.03% | 43.65% | 21.78% |

The principal management signal is decision migration. Under Downside, most applications that remain eligible require repricing. Under Severe, no application clears the full approval path at its current quote.

## Controls required before use

1. Affordability and data-quality gates run before pricing.
2. Applications above the 20% PD or 50% DSTI limits decline.
3. A price floor above the 30% management APR cap routes to manual review.
4. Python, Excel and the browser dashboard must reconcile at the reference application.
5. Any refreshed portfolio or changed assumption set constitutes a new governed run.
6. Override reasons, approved exceptions and realised outcomes must be retained for monitoring.

## Production backlog

- Calibrate PD and LGD on a representative lender book with outcome-maturity controls.
- Replace the economic-capital proxy with an approved portfolio-capital methodology.
- Add prepayment, delinquency states, collections, utilisation and recovery timing.
- Backtest realised margin, loss, operating cost and approval migration by vintage.
- Add fairness, customer-conduct, regulatory, model-risk and independent validation review.
- Define ownership, change approval, rollback, incident and override policies.

## Claims boundary

This is an educational portfolio case. Applicant records and monitoring histories are synthetic. Public benchmarks inform research assumptions but do not establish that the model is calibrated, compliant or suitable for a production lender.

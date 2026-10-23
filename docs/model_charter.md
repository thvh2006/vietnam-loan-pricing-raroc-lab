# Model charter

## Decision and users

The model supports application-time pricing discussion for a VND unsecured personal instalment loan. Intended users are credit strategy, finance, treasury and model-risk reviewers. It produces a minimum contractual APR for a target RAROC and routes an application to approve, reprice, manual review or decline.

## Intended use

- compare the quoted APR with a risk-adjusted price floor;
- attribute the price floor to funding, liquidity, operating cost, expected loss and capital;
- test approval and economics under controlled scenarios;
- identify applications that cannot meet the return hurdle within the management APR cap;
- support portfolio planning and product-pricing review.

## Prohibited use

- automated lending decisions in production;
- treating the synthetic application portfolio as representative of Vietnamese borrowers;
- using the standardized capital proxy as an approved regulatory calculation;
- treating the economic-capital proxy as an approved IRB or ICAAP model;
- communicating the modelled rate as a customer offer or legal maximum;
- inferring protected characteristics or using them in pricing.

## Material assumptions

The engine requires PD, LGD, EAD, funding rate, liquidity premium, operating costs, tax, capital parameters and a RAROC hurdle. Pricing depends on every one of these inputs. The repository keeps public benchmarks separate from management assumptions.

## Validation gates before production

1. Confirm the default definition, observation horizon and calibration of PD.
2. Validate LGD using recoveries, cure timing, collection costs and discounting.
3. Reconcile contractual cash flows to the servicing system, including prepayment and delinquency behaviour.
4. Replace portfolio-proxy capital with approved regulatory and ICAAP calculations.
5. Validate cost allocation with Treasury and Finance.
6. Complete lawful fairness testing and adverse-action review.
7. Establish override governance, monitoring thresholds and independent validation.

## Monitoring design

Monthly monitoring should separate ranking, calibration and economics. Minimum metrics include PD calibration by vintage, realised loss, recovery timing, prepayment, funding variance, operating-cost variance, rate overrides, approval mix, price-floor exceptions and realised RAROC by origination cohort.


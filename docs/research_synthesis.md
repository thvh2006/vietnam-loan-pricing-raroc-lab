# Research synthesis and benchmark register

As-of date: 22 October 2026.

## Regulatory capital context

Vietnam's Circular 14/2025/TT-NHNN establishes a revised capital-adequacy framework and a transition that ultimately replaces Circular 41/2016. Standardized qualifying retail exposures carry a 75% credit risk weight. Circular 14 also introduces capital conservation and countercyclical buffer concepts.

Implementation consequence: the project uses 75% only as an editable standardized retail benchmark. Qualification must be established exposure by exposure. The base case shows the 8% capital ratio separately from a 2.5% management buffer so reviewers can distinguish minimum capital from an internal planning choice.

## Market context

Techcombank's official financial highlights reported a 6M26 cost of funds of 4.6% and a Basel II capital adequacy ratio around 15%. These are bank-wide observations, not product-level costs. The project therefore uses 4.6% as a dated funding benchmark but does not infer product operating cost, loss rate or hurdle rate from it.

Techcombank also reported LTM ROE around 16.8% for 6M26. The case uses a 16% RAROC hurdle as a management assumption, not as an estimate of Techcombank's pricing policy or cost of equity.

## RAROC design evidence

The Basel Committee describes RAROC and shareholder value added as common risk-adjusted performance measures and highlights the importance of a hurdle rate that reflects the bank's cost of capital. BIS research on loan pricing distinguishes expected credit loss from the cost of equity held against unexpected loss.

Implementation consequence: expected loss is charged in the numerator, while allocated capital is held in the denominator. The engine does not subtract both expected and unexpected loss from profit and then charge the same capital again.

## Source register

1. State Bank of Vietnam, Circular 14/2025/TT-NHNN, issued 30 June 2025. English reproduction: https://english.luatvietnam.vn/circular-no-14-2025-tt-nhnn-dated-june-30-2025-of-the-state-bank-of-vietnam-on-capital-adequacy-ratio-of-commercial-banks-and-foreign-bank-branches-405700-doc1.html
2. State Bank of Vietnam, Circular 41/2016/TT-NHNN and subsequent amendments. Retail risk-weight benchmark: 75%.
3. Techcombank, Financial Highlights, accessed 22 October 2026: https://techcombank.com/en/investors/financial-information/highlights
4. Basel Committee on Banking Supervision, Range of practices and issues in economic capital modelling: https://www.bis.org/publ/bcbs143.pdf
5. Bank for International Settlements, Higher bank capital requirements and mortgage pricing: https://www.bis.org/publ/work511.pdf

## Claim boundary

The legal and bank sources above inform parameterization and governance. They do not validate the synthetic portfolio, applicant-level risk estimates, cost allocation or rate recommendations. Those elements require lender-owned data and approvals.


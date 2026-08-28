# Requirements

## Business Problem

UK government debt and financial-hardship data is published by four
separate bodies — Food Standards Agency, Insolvency Service, Ofgem,
and ONS — each on its own schedule, in its own format, with its own
naming conventions. No single view exists today; an analyst has to
manually download and reconcile four differently-shaped datasets by
hand.

## Data Sources

| Source             | What it publishes                                            | Real format issues found                                                        |
| ------------------ | ------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| FSA                | Meat industry debtor days                                    | Mixed CSV/XLSX, rolling 12-month windows that overlap                           |
| Insolvency Service | Bankruptcies, DROs, IVAs (England & Wales, Northern Ireland) | Cumulative releases, confirmed real revisions, mixed grains (month/year/cohort) |
| Ofgem              | Energy debt and arrears indicators                           | Mixed time-series and supplier-snapshot grains in the same source               |
| ONS                | Government deficit and debt                                  | Cumulative releases, official revisions table later discontinued                |

## Definition of Done

1. No duplicate rows for the same (source, indicator, geography, period)
2. Every value sits in a column matching its real grain
3. Revisions are detected and logged, never silently lost
4. Every row traceable to its exact source file
5. All four sources queryable through one consistent structure

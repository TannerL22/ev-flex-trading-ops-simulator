# Market Data Sources

## Overview

Phase 2 standardizes market price inputs for later charging optimization, forecast-vs-actual reconciliation, settlement-style exposure, Excel reporting, and dashboard views.

The project does not require paid or proprietary market data. All default workflows run from synthetic or sample files.

## Source Types

### Synthetic Market Data

Synthetic market data is the default offline demo source. It generates complete GB half-hourly price curves with:

- lower overnight prices
- morning and evening peaks
- random noise controlled by a seed
- optional high-volatility, evening-spike, negative-price, and missing-interval scenarios

Synthetic data is used for repeatable tests, demos, and later optimization examples.

### EPEX-Style Sample CSVs

The EPEX-style CSV loader is a local sample-file adapter. It simulates the shape of day-ahead or intraday auction price files without claiming to use official EPEX data.

Supported sample fields:

- `delivery_date`
- `settlement_period`
- `delivery_start`
- `delivery_end`
- `price_gbp_per_mwh`
- `market`
- `source`
- optional `price_type`, `currency`, `unit`, `notes`

Files generated under `data/sample_inputs/` are synthetic sample files for public demonstration only.

### ELEXON Insights API

ELEXON is relevant because system prices are used in GB imbalance settlement. Public ELEXON material describes System Buy Price and System Sell Price as cash-out or energy imbalance prices for each settlement period.

The optional client in `src/ev_flex_trading/ingestion/elexon_client.py` is designed around the ELEXON Insights-style system-prices path:

```text
/balancing/settlement/system-prices/{settlement_date}
```

The client is deliberately mockable and defensive. Tests do not call the live API. Live integration may require small field-mapping adjustments if ELEXON changes response shapes.

Reference:

- ELEXON imbalance pricing: https://www.elexon.co.uk/bsc/settlement/imbalance-pricing/

### NESO Data Portal API

NESO is relevant for public GB system and demand context that may support later analysis. The NESO Data Portal uses CKAN-style endpoints under:

```text
https://api.neso.energy/api/3/action/
```

The optional client supports:

- `package_search`
- `resource_search`
- `resource_show`
- `datastore_search`

Tests use mocked responses only.

Reference:

- NESO API guidance: https://www.neso.energy/data-portal/api-guidance
- CKAN API guide: https://docs.ckan.org/en/latest/api/

## Normalized Market Price Schema

All market inputs normalize into the same schema:

- `timestamp`
- `settlement_date`
- `settlement_period`
- `price_gbp_per_mwh`
- `source`
- `market`
- `price_type`
- `currency`
- `unit`
- `ingestion_timestamp`
- `data_quality_flag`
- `notes`

Negative prices are allowed. Implausibly large magnitudes are flagged for review rather than blocked automatically.

## Current Limitations

- EPEX files are sample-only and not official EPEX data.
- ELEXON and NESO clients are optional scaffolds and are not required for offline workflows.
- Unit tests do not hit live APIs.
- Later phases will decide which price series feeds optimization and which feeds settlement-style exposure.

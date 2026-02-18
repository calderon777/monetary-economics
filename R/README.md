# Topic 7 Figure Generation

This directory contains the R script for generating data-driven figures for **Topic 7: The Monetary Policy Consensus**.

## Quick Start

Run the figure generation script:

```r
source("R/make_consensus_figures.R")
```

## What It Does

The script `make_consensus_figures.R` pulls **real data** from official sources and generates:

### Figures Generated

1. **fig_policy_rates_cross_country.(png|svg)** — Cross-country policy rates (BoE, ECB, Fed, BoJ) with event markers for key crisis/policy dates
2. **fig_uk_inflation_target_band.(png|svg)** — UK CPI inflation vs 2% target with 1-3% open-letter threshold band
3. **fig_uk_bank_rate.(png|svg)** — UK Official Bank Rate (policy instrument) since 1997
4. **fig_uk_inflation_expectations_proxies.(png|svg)** — Survey-based UK inflation expectations (1-year and 5-year horizons)
5. **fig_qe_envelopes_step.(png|svg)** — QE/asset purchase envelope announcements (BoE APF, ECB PEPP, Fed LSAP1)
6. **fig_qe_envelopes_bar.(png|svg)** — Bar chart comparison of QE program sizes
7. **fig_nominal_anchor_comparison_heatmap.(png|svg)** — Qualitative comparison of monetary targeting, pegs, and inflation targeting
8. **fig_great_moderation_inflation_volatility_proxy.(png|svg)** — Rolling 5-year SD of UK CPI inflation
9. **fig_great_moderation_timeline.(png|svg)** — Timeline of consensus-era milestones
10. **fig_transmission_mechanism_schematic.(png|svg)** — Monetary transmission mechanism diagram

### Tables Generated

- **table_qe_envelopes_announcements.csv** — QE announcement dates and sizes with source links
- **table_nominal_anchor_comparison.csv** — Strategy comparison matrix

## Data Sources

All data pulled from official sources:

- **Bank of England:** IADB series IUDBEDR (Bank Rate), Inflation Attitudes Survey
- **ECB:** Data Portal API (deposit facility rate)
- **Federal Reserve:** FRED (DFEDTARL, DFEDTARU — target range bounds)
- **BIS:** Policy rates and consumer prices datasets (via BIS R package)

## Requirements

### R Packages

The script auto-installs required packages:

```r
tidyverse, lubridate, readxl, scales, stringr, janitor, zoo, svglite, ggrepel
```

### Optional: BIS Package

For Japan policy rates and UK CPI, the script uses the `BIS` package. If installation fails, you can add manual CSV fallbacks.

```r
install.packages("BIS")
```

## Directory Structure

After running the script, your project will have:

```
yourbook/
  R/
    make_consensus_figures.R
    README.md
  data_cache/          # Downloaded data files (cached)
  figs/                # Generated figures (PNG + SVG)
  tables/              # Generated CSV tables
```

## Notes

- **Figure formats:** All figures saved as both PNG (320 DPI) and SVG for flexibility
- **Caching:** Data downloads are cached in `data_cache/` to avoid repeated API calls
- **Event markers:** The cross-country policy rate chart includes markers for:
  - 2008-09: Global Financial Crisis (Lehman)
  - 2014-06: ECB negative deposit facility rate
  - 2020-03: COVID shock
  - 2022-03: Global tightening cycle

## Policy Rate Definitions

The script uses **institution-specific headline rates**:

- **BoE:** Bank Rate (official policy rate)
- **ECB:** Deposit facility rate (DFR)
- **Fed:** Target range midpoint (from FOMC announcements)
- **BoJ:** Policy rate as defined by BIS

If you prefer a **standardized BIS definition** for all four, edit the fetch functions in the script.

## Troubleshooting

### BIS Package Installation Fails

The script will continue without the BIS package, but Japan and UK CPI data will need manual alternatives. You can:

1. Download BIS bulk CSV files manually
2. Use alternative data sources (e.g., OECD, IMF IFS)
3. Skip those specific figures

### BoE IADB Format Changes

The BoE IADB Excel format tries multiple skip values (0-12) to find the date column. If the format changes significantly:

1. Download the file manually from: `https://www.bankofengland.co.uk/boeapps/database/`
2. Open in Excel to inspect structure
3. Adjust the `fetch_boe_bank_rate()` function

### Network Issues

All downloads use `download_with_cache()` with local caching. If a download fails mid-run:

1. Delete the partial file from `data_cache/`
2. Re-run the script

## Citation

When using these figures in publications, cite the original data sources:

- Bank of England. (various). Interactive Database (IADB). https://www.bankofengland.co.uk/boeapps/database/
- European Central Bank. (various). ECB Data Portal. https://data.ecb.europa.eu/
- Federal Reserve Bank of St. Louis. (various). FRED Economic Data. https://fred.stlouisfed.org/
- Bank for International Settlements. (various). BIS Statistics. https://data.bis.org/

## Questions?

For issues or modifications, contact the course instructor or open an issue in the project repository.

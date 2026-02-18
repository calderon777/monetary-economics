# ============================================================
# Monetary Policy Consensus — Figure Pack (PNG + SVG)
# Real-data pulls from BoE / ECB / BIS / Fed-system (FRED)
# ============================================================

# ----------------------------
# 0) Packages
# ----------------------------
required_pkgs <- c(
  "tidyverse", "lubridate", "readxl", "scales",
  "stringr", "janitor", "zoo", "svglite", "ggrepel"
)
to_install <- required_pkgs[!required_pkgs %in% installed.packages()[, "Package"]]
if (length(to_install) > 0) install.packages(to_install)

library(tidyverse)
library(lubridate)
library(readxl)
library(scales)
library(stringr)
library(janitor)
library(zoo)
library(svglite)
library(ggrepel)

# Optional BIS package (nice-to-have). If install fails, the script still runs,
# but UK CPI will be pulled from BIS bulk/CSV alternatives you can add later.
use_bis_pkg <- TRUE
if (use_bis_pkg) {
  if (!("BIS" %in% installed.packages()[, "Package"])) {
    try(install.packages("BIS"), silent = TRUE)
  }
}

# ----------------------------
# 1) Directories & helpers
# ----------------------------
dir.create("data_cache", showWarnings = FALSE, recursive = TRUE)
dir.create("figs", showWarnings = FALSE, recursive = TRUE)
dir.create("tables", showWarnings = FALSE, recursive = TRUE)

download_with_cache <- function(url, destfile) {
  if (!file.exists(destfile)) {
    message("Downloading: ", url)
    download.file(url, destfile = destfile, mode = "wb", quiet = TRUE)
  }
  destfile
}

guess_col <- function(df, candidates) {
  nm <- names(df)
  hit <- candidates[candidates %in% nm]
  if (length(hit) > 0) return(hit[1])
  hit2 <- nm[str_to_lower(nm) %in% str_to_lower(candidates)]
  if (length(hit2) > 0) return(hit2[1])
  stop("Could not find any of columns: ", paste(candidates, collapse = ", "))
}

as_month_end <- function(df, date_col = "date", value_col = "value") {
  df %>%
    mutate(month = floor_date(.data[[date_col]], "month")) %>%
    group_by(month) %>%
    arrange(.data[[date_col]]) %>%
    summarise(value = last(.data[[value_col]]), .groups = "drop") %>%
    mutate(date = month) %>%
    select(date, value)
}

save_both <- function(plot, filename_base, width = 9, height = 5, dpi = 320) {
  ggsave(paste0("figs/", filename_base, ".png"), plot = plot,
         width = width, height = height, dpi = dpi)
  ggsave(paste0("figs/", filename_base, ".svg"), plot = plot,
         width = width, height = height, device = "svg")
}

# ----------------------------
# 2) Data pulls — Policy rates
# ----------------------------

# 2.1 BoE: Official Bank Rate (daily) — series code IUDBEDR
# BoE IADB Excel download format documented here:
# https://www.bankofengland.co.uk/boeapps/database/help.asp
fetch_boe_bank_rate <- function(start = "01/Jan/1990") {
  url <- paste0(
    "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?excel97.x=yes",
    "&Datefrom=", URLencode(start),
    "&Dateto=now",
    "&SeriesCodes=IUDBEDR",
    "&UsingCodes=Y",
    "&VPD=Y",
    "&VFD=N"
  )
  f <- download_with_cache(url, "data_cache/boe_IUDBEDR_bank_rate.xls")
  # The IADB file can have header lines; try multiple skips until we find a Date column.
  for (sk in 0:12) {
    tmp <- try(readxl::read_excel(f, skip = sk), silent = TRUE)
    if (!inherits(tmp, "try-error")) {
      nm <- names(tmp) %>% str_to_lower()
      if (any(nm %in% c("date", "dates"))) {
        tmp <- tmp %>% clean_names()
        dcol <- guess_col(tmp, c("date"))
        # series might be code column, e.g., "iudbedr"
        vcol <- setdiff(names(tmp), dcol)[1]
        out <- tmp %>%
          transmute(date = as.Date(.data[[dcol]]),
                    value = as.numeric(.data[[vcol]])) %>%
          filter(!is.na(date), !is.na(value))
        return(out)
      }
    }
  }
  stop("Could not parse BoE IADB output. Try opening the xls in Excel to inspect column names.")
}

# 2.2 ECB: Deposit facility rate (daily) from ECB Data Portal API
# API docs:
# https://data.ecb.europa.eu/help/api/data
# Series key page (deposit facility): ILM.D.U2.C.L020200.U2.EUR
# Example query: https://data-api.ecb.europa.eu/service/data/EXR/M..EUR.SP00.A?format=csvdata
fetch_ecb_deposit_facility <- function(start_period = "1999-01-01") {
  url <- paste0(
    "https://data-api.ecb.europa.eu/service/data/ILM/ILM.D.U2.C.L020200.U2.EUR",
    "?startPeriod=", start_period, "&format=csvdata"
  )
  f <- download_with_cache(url, "data_cache/ecb_deposit_facility.csv")
  df <- readr::read_csv(f, show_col_types = FALSE)
  df <- df %>% clean_names()

  # ECB csvdata typically contains: time_period, obs_value
  dcol <- guess_col(df, c("time_period", "time"))
  vcol <- guess_col(df, c("obs_value", "value"))
  df %>%
    transmute(date = as.Date(.data[[dcol]]),
              value = as.numeric(.data[[vcol]])) %>%
    filter(!is.na(date), !is.na(value))
}

# 2.3 Fed: Target range midpoint from FRED (Fed system; source: Board of Governors FOMC press release)
# Series IDs: DFEDTARL & DFEDTARU
fetch_fed_target_midpoint <- function() {
  url_l <- "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFEDTARL"
  url_u <- "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFEDTARU"
  fl <- download_with_cache(url_l, "data_cache/fed_dfedtarL.csv")
  fu <- download_with_cache(url_u, "data_cache/fed_dfedtarU.csv")

  dl <- readr::read_csv(fl, show_col_types = FALSE)
  du <- readr::read_csv(fu, show_col_types = FALSE)

  names(dl) <- c("date", "lower")
  names(du) <- c("date", "upper")

  d <- dl %>%
    mutate(date = as.Date(date)) %>%
    left_join(du %>% mutate(date = as.Date(date)), by = "date") %>%
    mutate(value = 0.5 * (lower + upper)) %>%
    select(date, value) %>%
    filter(!is.na(value))

  d
}

# 2.4 BoJ: Policy rate from BIS policy rates dataset (preferred) or fallback to manual series
# BIS: Central bank policy rates are available in BIS Data Portal and via SDMX API; easiest in R: BIS package.
# https://data.bis.org (SDMX API documented), and topic CBPOL exists.
fetch_boj_policy_rate_bis <- function() {
  if (!("BIS" %in% installed.packages()[, "Package"])) {
    stop("Package 'BIS' not installed. Set use_bis_pkg=TRUE or install.packages('BIS').")
  }
  library(BIS)

  ds <- BIS::get_datasets()
  # Try to locate policy rates dataset
  pr <- ds %>%
    mutate(title_l = str_to_lower(title)) %>%
    filter(str_detect(title_l, "policy rates") | str_detect(title_l, "central bank policy rates")) %>%
    slice(1)

  if (nrow(pr) == 0) stop("Could not find BIS dataset for policy rates via BIS::get_datasets().")

  raw <- BIS::get_bis(pr$url) %>% clean_names()

  # Common SDMX columns
  area_col <- if ("ref_area" %in% names(raw)) "ref_area" else guess_col(raw, c("ref_area", "country", "geo"))
  time_col <- guess_col(raw, c("time_period", "time"))
  val_col  <- guess_col(raw, c("obs_value", "value"))

  # Japan codes often "JP" or "JPN"
  out <- raw %>%
    mutate(
      date = suppressWarnings(as.Date(.data[[time_col]])),
      date = if_else(is.na(date), ymd(paste0(.data[[time_col]], "-01")), date),
      value = as.numeric(.data[[val_col]]),
      area = as.character(.data[[area_col]])
    ) %>%
    filter(area %in% c("JP", "JPN")) %>%
    select(date, value) %>%
    filter(!is.na(date), !is.na(value)) %>%
    arrange(date)

  if (nrow(out) == 0) {
    stop("BIS policy rate dataset downloaded, but Japan series not found under ref_area JP/JPN. Inspect unique(ref_area).")
  }
  out
}

# 2.5 UK CPI (for target band plot) from BIS consumer prices dataset (preferred)
fetch_uk_cpi_bis <- function() {
  if (!("BIS" %in% installed.packages()[, "Package"])) {
    stop("Package 'BIS' not installed. Set use_bis_pkg=TRUE or install.packages('BIS').")
  }
  library(BIS)

  ds <- BIS::get_datasets()
  cp <- ds %>%
    mutate(title_l = str_to_lower(title)) %>%
    filter(str_detect(title_l, "consumer prices") | str_detect(title_l, "cpi")) %>%
    slice(1)

  if (nrow(cp) == 0) stop("Could not find BIS consumer prices dataset via BIS::get_datasets().")

  raw <- BIS::get_bis(cp$url) %>% clean_names()

  area_col <- if ("ref_area" %in% names(raw)) "ref_area" else guess_col(raw, c("ref_area", "country", "geo"))
  time_col <- guess_col(raw, c("time_period", "time"))
  val_col  <- guess_col(raw, c("obs_value", "value"))

  df <- raw %>%
    mutate(
      area = as.character(.data[[area_col]]),
      date_raw = as.character(.data[[time_col]]),
      # tries monthly first: YYYY-MM -> date
      date = suppressWarnings(ymd(paste0(date_raw, "-01"))),
      value = as.numeric(.data[[val_col]])
    ) %>%
    filter(area %in% c("GB", "GBR", "UK", "UNITED KINGDOM", "UNITED_KINGDOM")) %>%
    select(date, value) %>%
    filter(!is.na(date), !is.na(value)) %>%
    arrange(date)

  if (nrow(df) == 0) {
    stop("BIS CPI dataset downloaded, but UK series not found. Inspect unique(ref_area).")
  }
  df
}

# 2.6 UK inflation expectations proxy (BoE long-run Inflation Attitudes Survey)
# Legacy long-run summary file referenced in BoE releases:
# https://www.bankofengland.co.uk/statistics/Documents/nop/noplongrun.xls
fetch_boe_inflation_attitudes_longrun <- function() {
  url <- "https://www.bankofengland.co.uk/statistics/Documents/nop/noplongrun.xls"
  f <- download_with_cache(url, "data_cache/boe_inflation_attitudes_longrun.xls")

  # We don't know sheet names, so try all and bind; choose the one with a Date column.
  sheets <- try(excel_sheets(f), silent = TRUE)
  if (inherits(sheets, "try-error")) sheets <- NULL

  read_try <- function(sheet = NULL, skip = 0) {
    if (is.null(sheet)) {
      read_excel(f, skip = skip) %>% clean_names()
    } else {
      read_excel(f, sheet = sheet, skip = skip) %>% clean_names()
    }
  }

  candidates <- list()

  if (!is.null(sheets)) {
    for (sh in sheets) {
      for (sk in 0:10) {
        tmp <- try(read_try(sh, sk), silent = TRUE)
        if (!inherits(tmp, "try-error") && "date" %in% names(tmp)) {
          candidates[[paste0(sh, "_", sk)]] <- tmp
        }
      }
    }
  } else {
    for (sk in 0:10) {
      tmp <- try(read_try(NULL, sk), silent = TRUE)
      if (!inherits(tmp, "try-error") && "date" %in% names(tmp)) {
        candidates[[paste0("default_", sk)]] <- tmp
      }
    }
  }

  if (length(candidates) == 0) {
    stop("Could not find a sheet/skip combination that yields a 'date' column in noplongrun.xls.")
  }

  # Pick the first candidate
  df <- candidates[[1]]

  # Convert date and keep numeric columns
  out <- df %>%
    mutate(date = as.Date(date)) %>%
    filter(!is.na(date)) %>%
    mutate(across(where(is.character), ~na_if(., "")))

  out
}

# ----------------------------
# 3) Build datasets for plotting
# ----------------------------
message("Fetching policy rates...")
boe_rate_d <- fetch_boe_bank_rate()
ecb_dfr_d  <- fetch_ecb_deposit_facility()
fed_mid_d  <- fetch_fed_target_midpoint()
boj_rate_d <- fetch_boj_policy_rate_bis()

# Convert to month-end for comparison plot
boe_rate_m <- as_month_end(boe_rate_d, "date", "value")
ecb_dfr_m  <- as_month_end(ecb_dfr_d,  "date", "value")
fed_mid_m  <- as_month_end(fed_mid_d,  "date", "value")
boj_rate_m <- as_month_end(boj_rate_d, "date", "value")

policy_rates <- bind_rows(
  boe_rate_m %>% mutate(bank = "BoE (Bank Rate)"),
  ecb_dfr_m  %>% mutate(bank = "ECB (Deposit facility)"),
  fed_mid_m  %>% mutate(bank = "Fed (Target range midpoint)"),
  boj_rate_m %>% mutate(bank = "BoJ (Policy rate)")
) %>%
  filter(date >= as.Date("2000-01-01"))

# Event markers requested by you (fixed dates; you can adjust)
events <- tibble(
  label = c("GFC (Lehman)", "ECB DFR < 0", "COVID shock", "Tightening cycle"),
  date  = as.Date(c("2008-09-15", "2014-06-11", "2020-03-18", "2022-03-16"))
)

# ----------------------------
# 4) FIGURE A — Cross-country policy rates with event markers
# ----------------------------
p_rates <- ggplot(policy_rates, aes(x = date, y = value, group = bank)) +
  geom_line(linewidth = 0.8) +
  geom_vline(data = events, aes(xintercept = date), linetype = "dashed", linewidth = 0.4) +
  geom_text(
    data = events,
    aes(x = date, y = Inf, label = label),
    angle = 90, vjust = 1.2, hjust = 1.0, size = 3
  ) +
  scale_y_continuous(labels = percent_format(scale = 1)) +
  labs(
    title = "Policy rates: BoE, ECB, Fed, BoJ (monthly end-of-month)",
    subtitle = "Event markers: 2008–09 crisis; 2014 ECB negative rate; 2020 COVID; 2022 tightening cycle",
    x = NULL, y = "Percent"
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "none") +
  facet_wrap(~ bank, ncol = 1, scales = "free_y")

save_both(p_rates, "fig_policy_rates_cross_country", width = 9, height = 9)

# ----------------------------
# 5) FIGURE B — UK inflation vs target band (1%–3%) + Bank Rate overlay (two panels)
# ----------------------------
message("Fetching UK CPI from BIS...")
uk_cpi_idx <- fetch_uk_cpi_bis()

# Year-on-year inflation (%)
uk_infl <- uk_cpi_idx %>%
  arrange(date) %>%
  mutate(infl_yoy = 100 * (value / lag(value, 12) - 1)) %>%
  filter(!is.na(infl_yoy), date >= as.Date("1997-01-01")) %>%
  select(date, infl_yoy)

# Bank rate monthly (align)
uk_rate <- boe_rate_m %>%
  filter(date >= as.Date("1997-01-01")) %>%
  rename(rate = value)

p_infl <- ggplot(uk_infl, aes(x = date, y = infl_yoy)) +
  geom_ribbon(aes(ymin = 1, ymax = 3), alpha = 0.15) +
  geom_hline(yintercept = 2, linewidth = 0.6) +
  geom_line(linewidth = 0.8) +
  labs(
    title = "UK CPI inflation and the BoE open-letter band",
    subtitle = "Shaded band is 1%–3%; line at 2% target (CPI). Inflation from BIS CPI dataset.",
    x = NULL, y = "CPI inflation (y/y, %)"
  ) +
  theme_minimal(base_size = 12)

p_rate_uk <- ggplot(uk_rate, aes(x = date, y = rate)) +
  geom_line(linewidth = 0.8) +
  labs(
    title = "UK Official Bank Rate (policy instrument)",
    subtitle = "BoE series IUDBEDR (monthly end-of-month).",
    x = NULL, y = "Bank Rate (%)"
  ) +
  theme_minimal(base_size = 12)

save_both(p_infl, "fig_uk_inflation_target_band", width = 9, height = 5)
save_both(p_rate_uk, "fig_uk_bank_rate", width = 9, height = 5)

# ----------------------------
# 6) FIGURE C — UK inflation expectations proxy (BoE Inflation Attitudes Survey long run)
# ----------------------------
message("Fetching BoE Inflation Attitudes Survey long-run file...")
ias <- fetch_boe_inflation_attitudes_longrun()

# Try to auto-detect likely expectation columns
nm <- names(ias)
# Candidate patterns (best effort): adjust if the file structure differs
col_1y <- nm[str_detect(nm, "q2a|one|coming|next_12|12_month|year")] %>% head(1)
col_5y <- nm[str_detect(nm, "q2c|five|5")] %>% head(1)

if (length(col_1y) == 0 || length(col_5y) == 0) {
  message("Could not auto-detect 1y/5y expectation columns. Available columns:\n",
          paste(nm, collapse = ", "))
  # Stop with a friendly message so you can pick columns.
  stop("Please set col_1y and col_5y manually after inspecting names(ias).")
}

ias_plot <- ias %>%
  transmute(
    date = date,
    exp_1y = as.numeric(.data[[col_1y]]),
    exp_5y = as.numeric(.data[[col_5y]])
  ) %>%
  filter(date >= as.Date("1997-01-01")) %>%
  pivot_longer(cols = c(exp_1y, exp_5y), names_to = "horizon", values_to = "expectation") %>%
  mutate(horizon = recode(horizon,
                          exp_1y = "Inflation expectations (1-year ahead)",
                          exp_5y = "Inflation expectations (5-years ahead)")) %>%
  filter(!is.na(expectation))

p_ias <- ggplot(ias_plot, aes(x = date, y = expectation, group = horizon)) +
  geom_hline(yintercept = 2, linewidth = 0.6) +
  geom_line(linewidth = 0.8) +
  facet_wrap(~ horizon, ncol = 1, scales = "free_y") +
  labs(
    title = "UK inflation expectations proxies (BoE Inflation Attitudes Survey)",
    subtitle = "Horizontal line is 2% target (for reference). Source: BoE long-run survey file (noplongrun.xls).",
    x = NULL, y = "Percent"
  ) +
  theme_minimal(base_size = 12)

save_both(p_ias, "fig_uk_inflation_expectations_proxies", width = 9, height = 7)

# ----------------------------
# 7) FIGURE D — QE/asset purchase envelopes (step charts; official announcement totals)
# ----------------------------
# Sources (official pages):
# BoE May 2009 to 125: https://www.bankofengland.co.uk/news/2009/may/mpc-may-2009
# BoE Aug 2009 to 175: https://www.bankofengland.co.uk/news/2009/august/mpc-august-2009
# BoE Nov 2009 to 200: https://www.bankofengland.co.uk/news/2009/november/mpc-november-2009
# BoE Mar 19 2020 to 645: https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2020/monetary-policy-summary-for-the-special-monetary-policy-committee-meeting-on-19-march-2020
# BoE Jun 2020 to 745: https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2020/june-2020
# BoE Nov 2020 to 895: https://www.gov.uk/government/publications/asset-purchase-facility-apf-ceiling-november-2020/aft-letter-to-the-chancellor

# ECB PEPP:
# Initial 750 (Mar 18 2020): https://www.ecb.europa.eu/press/pr/date/2020/html/ecb.pr200318_1~3949d6f266.en.html
# PEPP page includes +600 (Jun 4 2020) and +500 (Dec 10 2020) totals: https://www.ecb.europa.eu/mopo/implement/pepp/html/index.en.html

# Fed LSAP1:
# Timeline: https://www.federalreserve.gov/monetarypolicy/timeline-balance-sheet-policies.htm

qe_steps <- tribble(
  ~bank, ~program, ~date, ~cum_amount, ~unit,
  "BoE", "APF/QE authorised size", as.Date("2009-03-05"),  75,  "GBP bn",
  "BoE", "APF/QE authorised size", as.Date("2009-05-07"), 125,  "GBP bn",
  "BoE", "APF/QE authorised size", as.Date("2009-08-06"), 175,  "GBP bn",
  "BoE", "APF/QE authorised size", as.Date("2009-11-05"), 200,  "GBP bn",
  "BoE", "APF/QE authorised size", as.Date("2020-03-19"), 645,  "GBP bn",
  "BoE", "APF/QE authorised size", as.Date("2020-06-18"), 745,  "GBP bn",
  "BoE", "APF/QE authorised size", as.Date("2020-11-05"), 895,  "GBP bn",

  "ECB", "PEPP envelope",          as.Date("2020-03-18"), 750,  "EUR bn",
  "ECB", "PEPP envelope",          as.Date("2020-06-04"), 1350, "EUR bn",
  "ECB", "PEPP envelope",          as.Date("2020-12-10"), 1850, "EUR bn",

  "Fed", "LSAP1 announced totals", as.Date("2008-11-25"), 600,  "USD bn",
  "Fed", "LSAP1 announced totals", as.Date("2009-03-18"), 1750, "USD bn"
)

# Save the table for your book appendix
readr::write_csv(qe_steps, "tables/table_qe_envelopes_announcements.csv")

p_qe <- ggplot(qe_steps, aes(x = date, y = cum_amount, group = program)) +
  geom_step(linewidth = 0.9, direction = "hv") +
  geom_point(size = 2) +
  facet_wrap(vars(bank, unit), scales = "free_y", ncol = 1) +
  labs(
    title = "Key QE / purchase envelope announcements (step chart)",
    subtitle = "Cumulative announced envelopes (not realised flow). Source links in script header comments.",
    x = NULL, y = "Cumulative envelope"
  ) +
  theme_minimal(base_size = 12)

save_both(p_qe, "fig_qe_envelopes_step", width = 9, height = 8)

# Bar-style comparison (side-by-side) for quick teaching slides
p_qe_bar <- qe_steps %>%
  mutate(label = paste(bank, format(date, "%Y-%m-%d"), sep = " | ")) %>%
  ggplot(aes(x = reorder(label, cum_amount), y = cum_amount)) +
  geom_col() +
  coord_flip() +
  facet_wrap(vars(unit), scales = "free_y") +
  labs(
    title = "QE / purchase envelope announcements (bar comparison)",
    subtitle = "For cross-program size comparisons, keep units separate (GBP/EUR/USD).",
    x = NULL, y = "Envelope size"
  ) +
  theme_minimal(base_size = 12)

save_both(p_qe_bar, "fig_qe_envelopes_bar", width = 9, height = 7)

# ----------------------------
# 8) FIGURE E — Nominal anchor comparison heatmap (teaching figure)
# ----------------------------
anchors <- tribble(
  ~strategy, ~criterion, ~score,
  "Monetary targeting", "Anchor visibility (public)", "Medium",
  "Monetary targeting", "Robustness to velocity shifts", "Low",
  "Monetary targeting", "Domestic policy autonomy", "High",
  "Monetary targeting", "Speculative attack vulnerability", "Low",
  "Monetary targeting", "Works well at ELB?", "Medium",

  "Exchange-rate peg", "Anchor visibility (public)", "High",
  "Exchange-rate peg", "Robustness to velocity shifts", "High",
  "Exchange-rate peg", "Domestic policy autonomy", "Low",
  "Exchange-rate peg", "Speculative attack vulnerability", "High",
  "Exchange-rate peg", "Works well at ELB?", "Medium",

  "Inflation targeting", "Anchor visibility (public)", "High",
  "Inflation targeting", "Robustness to velocity shifts", "High",
  "Inflation targeting", "Domestic policy autonomy", "High",
  "Inflation targeting", "Speculative attack vulnerability", "Low",
  "Inflation targeting", "Works well at ELB?", "High"
)

anchors <- anchors %>%
  mutate(score = factor(score, levels = c("Low", "Medium", "High")))

readr::write_csv(anchors, "tables/table_nominal_anchor_comparison.csv")

p_anchor <- ggplot(anchors, aes(x = criterion, y = strategy, fill = score)) +
  geom_tile() +
  geom_text(aes(label = score), size = 3) +
  labs(
    title = "Nominal anchors: qualitative comparison (teaching heatmap)",
    subtitle = "Scores are pedagogical (Low/Medium/High) to match lecture-note logic.",
    x = NULL, y = NULL
  ) +
  theme_minimal(base_size = 12) +
  theme(axis.text.x = element_text(angle = 25, hjust = 1),
        legend.position = "bottom")

save_both(p_anchor, "fig_nominal_anchor_comparison_heatmap", width = 10, height = 5.5)

# ----------------------------
# 9) FIGURE F — Great Moderation proxy: rolling inflation volatility (UK CPI y/y)
# ----------------------------
# This is an inflation-volatility proxy, not an output-volatility measure.
# It is a defensible classroom visual alongside Bernanke (2004).
uk_infl_vol <- uk_infl %>%
  arrange(date) %>%
  mutate(
    infl_sd_5y = rollapply(infl_yoy, width = 60, FUN = sd, align = "right", fill = NA)
  ) %>%
  filter(date >= as.Date("1970-01-01"))

gm_markers <- tibble(
  label = c("approx start of Great Moderation", "GFC begins"),
  date = as.Date(c("1984-01-01", "2007-08-01"))
)

p_vol <- ggplot(uk_infl_vol, aes(x = date, y = infl_sd_5y)) +
  geom_line(linewidth = 0.8) +
  geom_vline(data = gm_markers, aes(xintercept = date), linetype = "dashed", linewidth = 0.4) +
  geom_text(data = gm_markers, aes(x = date, y = Inf, label = label),
            angle = 90, vjust = 1.2, hjust = 1, size = 3) +
  labs(
    title = "UK inflation volatility proxy (rolling 5-year SD of CPI inflation, y/y)",
    subtitle = "A visual complement to Great Moderation discussions; inflation volatility proxy only.",
    x = NULL, y = "SD (percentage points)"
  ) +
  theme_minimal(base_size = 12)

save_both(p_vol, "fig_great_moderation_inflation_volatility_proxy", width = 9, height = 5)

# A timeline figure (teaching) using ggplot annotations
timeline <- tribble(
  ~date, ~event,
  as.Date("1990-01-01"), "Inflation targeting spreads (early 1990s)",
  as.Date("1997-05-01"), "BoE operational independence era (UK)",
  as.Date("2008-09-15"), "GFC intensifies (Lehman)",
  as.Date("2009-03-05"), "BoE QE begins (APF)",
  as.Date("2014-06-11"), "ECB deposit facility rate turns negative",
  as.Date("2020-03-18"), "COVID shock + PEPP/QE expansions",
  as.Date("2022-03-16"), "Global tightening phase (illustrative)"
)

p_timeline <- ggplot(timeline, aes(x = date, y = 0)) +
  geom_hline(yintercept = 0, linewidth = 0.6) +
  geom_point(size = 2) +
  geom_text_repel(aes(label = event), direction = "y", nudge_y = 0.1, size = 3,
                  min.segment.length = 0) +
  scale_y_continuous(NULL, breaks = NULL) +
  labs(
    title = "Great Moderation / consensus-era timeline (selected milestones)",
    subtitle = "Designed for teaching in the Monetary Policy Consensus chapter.",
    x = NULL
  ) +
  theme_minimal(base_size = 12)

save_both(p_timeline, "fig_great_moderation_timeline", width = 10, height = 4.5)

# ----------------------------
# 10) FIGURE G — Transmission mechanism schematic in ggplot2 (diagram)
# ----------------------------
# A simple boxes-and-arrows diagram rendered as a ggplot (Quarto friendly).
library(grid)

nodes <- tribble(
  ~id, ~label, ~x, ~y,
  "i",   "Policy rate (i)",              0.1, 0.8,
  "mr",  "Market rates & credit",        0.4, 0.8,
  "ap",  "Asset prices",                 0.4, 0.6,
  "fx",  "Exchange rate",                0.4, 0.4,
  "ad",  "Spending / AD",                0.7, 0.6,
  "og",  "Output gap",                   0.85,0.6,
  "inf", "Wages & prices → inflation",   0.85,0.4
)

edges <- tribble(
  ~from, ~to,
  "i","mr",
  "i","ap",
  "i","fx",
  "mr","ad",
  "ap","ad",
  "fx","ad",
  "ad","og",
  "og","inf"
) %>%
  left_join(nodes %>% select(from = id, x1 = x, y1 = y), by = "from") %>%
  left_join(nodes %>% select(to = id, x2 = x, y2 = y), by = "to")

p_trans <- ggplot() +
  geom_segment(
    data = edges,
    aes(x = x1, y = y1, xend = x2, yend = y2),
    arrow = arrow(length = unit(0.12, "inches"), type = "closed"),
    linewidth = 0.5
  ) +
  geom_label(
    data = nodes,
    aes(x = x, y = y, label = label),
    label.size = 0.2,
    size = 3
  ) +
  coord_cartesian(xlim = c(0,1), ylim = c(0.25,0.95), expand = FALSE) +
  theme_void() +
  labs(
    title = "Monetary transmission mechanism (schematic)"
  )

save_both(p_trans, "fig_transmission_mechanism_schematic", width = 10, height = 4)

# ----------------------------
# 11) Finish
# ----------------------------
message("All figures saved to figs/ and tables to tables/.")

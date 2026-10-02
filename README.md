# Research Code and Analysis Pipeline for Heatwaves and Compound Social Vulnerabilities in Brazil

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23103009.svg)](https://doi.org/10.5281/zenodo.23103009)

This repository contains the data-processing code and notebooks used in the
accompanying article on heatwaves and compound social vulnerabilities.

The study evaluates XHWI, the National Weather Service heat index (HINWS), and
an anomaly-based WMO approach using ERA5 data for Brazilian capitals from 1950
through 2023. It combines heatwave metrics with mortality and hospitalization
rate anomalies and produces hazard, vulnerability, and risk maps for older,
Indigenous, and Quilombola populations.

## Repository layout

- `data/`: raw, intermediate, and legacy local data. See `data/README.md`.
- `src/`: reusable analysis functions and centralized paths.
- `pipeline.py`: public entry point for validation, auditing, preprocessing,
  and aggregation.
- `notebooks/`: research notebooks and analysis orchestration.
- `scripts/`: provenance scripts, including the historical XHWI generator.
- `results/`: documented output groups. Generated result files are ignored by Git.
- `tests/`: lightweight integrity and function tests.

## Study periods

- Reference climatology: 1961--1990.
- P1: 1950--1974.
- P2: 1975--1998.
- P3: 1999--2023.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python -m src.main --stage validate
python pipeline.py --stage audit
python pipeline.py --stage analysis
python pipeline.py --stage maps
```

The original source data are not committed to Git. Their expected locations,
provenance, and intermediate products are documented under `data/`.

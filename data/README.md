# Data

Data are separated into three layers:

- `raw/`: source files required by the article pipeline;
- `intermediate/`: files produced by preprocessing and aggregation stages;
- `legacy/`: files retained for provenance but not used by the article.

The active analysis uses ERA5-derived monthly capital files, the Brazilian
XHWI NetCDF, mortality and hospitalization data, administrative boundaries,
older-population counts, and Indigenous and Quilombola territories.

The study ends on 31 December 2023. Files containing later observations are
not included in article calculations.

## Sources

- ERA5 temperature and relative humidity data;
- DATASUS mortality and hospitalization data;
- IBGE administrative boundaries and older-population data;
- FUNAI Indigenous territories;
- INCRA Quilombola territories.

`legacy/` contains additional files that were present in the working archive,

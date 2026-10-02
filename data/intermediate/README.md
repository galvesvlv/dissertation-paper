# Intermediate Data

Intermediate files are exactly the products that would be created by running
the preprocessing and aggregation stages. They are kept in the directories
where those stages would write them, but the main notebooks are not executed as
part of the repository checks.

The current analysis preserves hourly, daily, monthly, and capital-wide ERA5
products. These files can be regenerated from `data/raw/` with
`python pipeline.py --stage all`. The audit rejects products outside the study
period, incomplete daily/monthly coverage, missing columns, duplicate times,
and stale aggregate filenames.

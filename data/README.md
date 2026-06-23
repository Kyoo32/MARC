# Research data

Place your own multivariate time-series dataset in this directory.

The default configuration expects:

```text
data/timeseries.csv
```

Required structure:

- one timestamp column;
- one optional unit column for spatial, site, subject, or replicate identity;
- two or more numeric time-series variables.

Example:

```csv
time,unit,X,Y,Z
2025-01-01 00:00:00,A,0.1,0.4,-0.2
2025-01-01 01:00:00,A,0.3,0.5,-0.1
2025-01-01 00:00:00,B,0.2,0.1,0.0
```

Research data are ignored by Git by default.

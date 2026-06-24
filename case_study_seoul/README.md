# Seoul air-quality case study

This directory contains publication figures and summary tables from the MARC
case study. It is an example application, not the default MARC input.

The original observational dataset is not bundled. Researchers applying MARC
must supply their own time-series dataset through the repository-level
`marc_config.yml`.

## Public data sources used for the case study

The Seoul case study was designed around Seoul Open Data Plaza station-level air
quality resources. Researchers who want to reproduce or adapt this case study
should obtain the raw data from the official provider and check the current API,
file format, and terms of use before analysis.

| ID | Dataset | Access | Role in the case study | Resolution | Variables / contents | Unit |
| --- | --- | --- | --- | --- | --- | --- |
| OA-2275 | 서울시 시간 평균 대기오염도 정보 / Seoul hourly average air-pollution information | OpenAPI + file | Main dataset | Hourly | `NO2`, `O3`, `CO`, `SO2`, `PM10`, `PM2.5` | Monitoring station |
| OA-2220 | 서울시 기간별 일평균 대기환경 정보 / Seoul daily average air-environment information by period | OpenAPI / file, depending on provider availability | Backup dataset when hourly missingness is too high; also useful for daily-resolution comparisons | Daily | Same six pollutants | Monitoring station |
| OA-1199 | 서울시 지역 구별 측정소 행정코드 정보 / Seoul district-level station administrative-code information | OpenAPI / file, depending on provider availability | Station metadata for distance calculation and map visualization | Metadata | Station name, latitude, longitude, administrative district code | Monitoring station |

Practical notes:

- OA-2275 is preferred when the research question requires hourly lagged causal
  discovery because it has the highest temporal resolution.
- OA-2220 should not be mixed with hourly data without explicitly changing the
  temporal design, lag interpretation, and comparison target.
- OA-1199 is metadata, not a time-series input. Use it to attach coordinates,
  administrative districts, and station-distance information.
- The public MARC repository does not redistribute these raw datasets. Place
  downloaded and cleaned files under `data/` or another local path, then point
  `marc_config.yml` to that file.

## Suggested wide-format input after local preprocessing

MARC expects a researcher-prepared table rather than raw API responses. A Seoul
hourly case-study input might look like this after local collection, merging,
and validation:

```text
time,unit,NO2,O3,CO,SO2,PM10,PM25
2023-01-01 00:00,111291,...
2023-01-01 01:00,111291,...
2023-01-01 00:00,111261,...
```

The exact station list, time period, missing-data policy, transformations, and
positive controls must be declared in the study configuration and manuscript.

The case-study artifacts are retained to support manuscript inspection. Local
paths, execution caches, and machine-specific provenance files are excluded
from the public repository.

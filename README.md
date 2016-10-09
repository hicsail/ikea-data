# ikea-data
Scripts for manipulating data sets containing products and corresponding prices obtained from publicly available IKEA catalogs.

## Data Management Scripts

The root directory contains scripts for managing the legacy and latest processed versions of the data set:
* `config.json` specifies the format of the legacy data, as well as additional information for the projections defined in the scripts;
* `data.py` provides functionality for converting a legacy data set into the new format, and for computing the projection of that data to obtain the latest derived data set.

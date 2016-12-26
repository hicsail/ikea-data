# ikea-data
Scripts for manipulating data sets containing products and corresponding prices obtained from publicly available IKEA catalogs.

## Data Management Scripts

The root directory contains scripts for managing the legacy and latest processed versions of the data set:
* `config.json` specifies the format and content of the legacy data, corrections to the legacy data, and additional information for the projections defined in the scripts;
* `measurements.py` provides a helper class for creating and working with normalized measurements along dimensions found in the data; and
* `data.py` provides a number of functionalities:
 * converting a legacy data set into JSON format,
 * converting a JSON-format data set into a Microsoft Excel format,
 * computing the projection of a data set with normalized field values for geometry dimensions, and
 * clustering a data set using an ad hoc approach based on a Chebyshev metric.

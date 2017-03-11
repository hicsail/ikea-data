# ikea-data
Scripts for manipulating data sets containing products and corresponding prices obtained from publicly available IKEA catalogs.

## Data Management Scripts

The root directory contains scripts for managing the legacy and latest processed versions of the data set:
* `config.json` specifies the format and content of the legacy data, corrections to the legacy data, and additional information for the projections defined in the scripts;
* `measurements.py` provides a helper class for creating and working with normalized measurements along dimensions found in the data; and
* `data.py` provides a number of functionalities:
 * converting a legacy data set into JSON format,
 * converting a JSON-format data set into a Microsoft Excel format,
 * generating a JSON-format color translation file,
 * computing the projection of a data set with normalized field values for geometry dimensions, and
 * clustering a data set using an ad hoc approach based on a Chebyshev metric.
* `kmeans.py` 
 * divide projected.json gained from data.py by name, -gi indicates the input file, -go indicates the output directory,
 * run kmeans on given directory using the number of distinct ikea id as parameter k, -iik is the input directory, -oid is the output directory, it also save some plots to show the errors,
 * run kmeans on given k, -ik is the input directory, -oid is the output directory, -low indicates the start value of k of the iteration, -high indicates the higher bound of k, -incre is the increment of k in every loop,
 * we'd better make -high > -low and -incre be positive, or it may cause some problems from scikit-learn.
 * here is a sample, only when the parameters are all provided for a function, the function will be ran.
```  
  python kmeans.py -gi projected.json -go groupByNameResult/ -iid groupByNameData/ -oid groupByNameResult/ -ik groupByNameData/ -ok groupByNameResult/ -low 5 -high 10 -incre 5
```

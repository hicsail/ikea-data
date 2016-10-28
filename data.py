###############################################################################
## 
## data.py
##
##   Script with functions for cleaning, filtering, converting, and managing
##   the legacy database as well as the working versions of the data for the
##   current project.
##
##

import argparse
import json
import xlrd
import xlrd.sheet
import xlsxwriter
import re

from measurements import Measurement, Assortment

###############################################################################
##

CONFIG = json.loads(open('config.json').read()) # For conversion/translation.

def set_or_update_op(d, k, op, val):
    '''
    Sets or updates an entry with an operator.
    '''
    if k not in d:
        d[k] = val
    else:
        d[k] = op(d[k], val)

def str_ascii_only(s):
    '''
    Convert a string to ASCII and strip it of whitespace pre-/suffix.
    '''
    return s.encode("ascii", errors='ignore').decode("ascii").strip()

def xlsx_cell_to_json(column, cell):
    '''
    Use appropriate data structures and string representations
    based on the column/field and cell value.
    '''
    cell_type = xlrd.sheet.ctype_text.get(cell.ctype, 'unknown type')
    if cell_type == 'empty':
        return None
    elif cell_type == 'number' and abs(cell.value - int(cell.value)) < 0.0000000001:
        return int(cell.value)
    elif cell_type == 'number':
        return float(cell.value)
    elif cell_type == 'text':
        return str_ascii_only(str(cell.value))
    return None

def open_workbook_try_extensions(name):
    '''
    Attempt to open an Excel workbook file regardless of its extension.
    '''
    xl_workbook = None
    for ext in ["xlsx", "XLSX", "xls", "XLS"]:
        try:
            xl_workbook = xlrd.open_workbook(name + "." + ext)
            break
        except:
            continue
    return xl_workbook

def xlsx_to_dict(path, countries, years, columns, include_nulls = False):
    '''
    Converts data from multiple XLSX files into a single Python dictionary.
    '''
    entries = []
    print("Retrieving data from files to build dictionary...")
    for country in countries:
        for year in years:
            filepath = path + country + str(year)
            xl_workbook = open_workbook_try_extensions(filepath)
            if xl_workbook is None:
                print("...did not find any file '" + filepath + ".{xlsx/XLSX/xls/XLS} so skipping;")
                continue
            sheet_names = xl_workbook.sheet_names()
            xl_sheet = xl_workbook.sheet_by_index(0)
            row = xl_sheet.row(0)
            cols = [cell_obj.value for idx, cell_obj in enumerate(row)]
            first = cols.index('page')
            for row_idx in range(1, xl_sheet.nrows):
                entry = {'country': country, 'year': year} 
                for (field, col_idx) in zip(columns, range(first, min(xl_sheet.ncols, first+len(columns)))):
                    value = xlsx_cell_to_json(field, xl_sheet.cell(row_idx, col_idx))
                    if value is not None or include_nulls:
                        entry[field] = value
                entries.append(entry)
            print("...finished retrieving data from '" + filepath + "';")
    print("...dictionary built successfully.")
    return {'entries': entries}

def xlsx_files_to_json_file(xlsx_files_path, json_file, legible = False, countries = CONFIG['countries'], years = CONFIG['years']):
    '''
    Saves data from XLSX files to a JSON file.
    '''
    d = xlsx_to_dict(xlsx_files_path, countries, years, CONFIG['columns'])
    print("Writing file '" + json_file + "'...")
    with open(json_file, 'w') as handle:
        if legible: handle.write(json.dumps(d, sort_keys = True, indent = 2)) # Human-legible.
        else: handle.write(json.dumps(d))
    print("...finished writing file '" + json_file + "'.\n")

def json_file_to_xlsx_file(json_file, xlsx_file):
    '''
    Converts a JSON file into an XLSX file.
    '''
    print("Converting data in file '" + json_file + "' to file '" + xlsx_file + "'...")
    d = json.loads(open(json_file).read())
    entries = d['entries']
    xl_workbook = xlsxwriter.Workbook(xlsx_file)
    xl_bold = xl_workbook.add_format({'bold': True})
    xl_sheet = xl_workbook.add_worksheet("data")

    # Set the column widths.
    for (i,w) in zip(range(0,11), [2,5,10,25,18,8,4,4.5,5.5,6.5,8]):
        xl_sheet.set_column(i, i, w)

    # Add the column headers.
    for i in range(0,len(CONFIG['dimensions'])):
        xl_sheet.write(0, i, CONFIG['dimensions'][i], xl_bold)

    # Insert the data (all rows).
    for i in range(len(entries)):
        entry = entries[i]
        for j in range(0,len(CONFIG['dimensions'])):
            dimension = CONFIG['dimensions'][j]
            xl_sheet.write(i+1, j, entry.get(dimension))

        # Progress counter.
        if i > 0 and i % 5000 == 0:
            print("...wrote " + str(i) + "/" + str(len(entries)) + " entries;")

    xl_workbook.close()
    print("...finished writing file '" + xlsx_file + "'.\n")

def projection_product_unit_quantity(entry):
    PULS = CONFIG['translations']['product_unit_labels']
    quantity = entry.get("quantity")
    if quantity is None:
        return

    # If we already have a numeric quantity representation, use it.
    if type(quantity) == int or type(quantity) == float:
        entry["pieces"] = quantity
        return

    # Obtain any labels and numeric literals found in the quantity string.
    label = re.sub(r'(\s*)[0-9]+(\s*)', '', quantity) # Quantity label (ignoring numeric quantity).
    numerals = re.search(r'(\s*)[0-9]+(\s*)', quantity) # Numeric quantity, if present.

    if numerals:
        if quantity == str(int(numerals.group())): entry["pieces"] = int(numerals.group())
        elif quantity == "m2": entry["sqr_m"] = 1
        elif label in (PULS['piece'] + PULS['pieces']): entry["pieces"] = int(numerals.group())
        elif label in PULS['pairs']: entry["pieces"] = 2*int(numerals.group())
        elif label in PULS['grams']: entry["grams"] = int(numerals.group())
        elif label in PULS['linear_meters']: entry["lin_m"] = int(numerals.group())
        #else: print(quantity, label)
    else:
        if label in PULS['piece']: entry["pieces"] = 1
        elif label in PULS['two']: entry["pieces"] = 2
        elif label in PULS['six']: entry["pieces"] = 6
        elif quantity in PULS['linear_meters']: entry["lin_m"] = 1
        elif quantity in PULS['linear_feet']: entry["lin_m"] = 0.3048
        elif quantity in PULS['linear_yards']: entry["lin_m"] = 0.9144
        elif quantity in PULS['square_meters']: entry["sqr_m"] = 1
        elif quantity in PULS['square_feet']: entry["sqr_m"] = 0.092903
        elif quantity in PULS['collection']: entry["collection"] = True
        #else: print(quantity, label)

def project_geometry_dimension_matches(dimension):
    '''
    Retrieve all numeric values from a string that
    match one of the specified formats. Finds each
    longest match from left to right.
    '''
    patterns = [\
        ('prime_double_prime', r'([0-9]+)\'(\s*)([0-9]+)(\")?'),
        ('prime', r'([0-9]+)\''),
        ('decimal_mixed', r'([0-9]+)\.([0-9]+)(\s)([0-9]+)/(2|4|6|8)(\s|$|-|x|\+|/)'),
        ('mixed', r'([0-9]+)(\s)([0-9]+)/(2|4|6|8)(\s|$|-|x|\+|/)'),
        ('fraction', r'([0-9]+)/(2|4|6|8)(\s|$|-|x|\+|/)'),
        ('decimal', r'([0-9]+)\.([0-9]+)'),
        ('integer', r'([0-9]+)')
      ]

    # Keep finding matches left-to-right until there are no more.
    suffix = dimension
    assortment = Assortment()
    match = True
    while match:
        # Find the longest match.
        match = None
        length = 0
        for (notation, regexp) in patterns:
            result = re.search(regexp, suffix)
            if result:
                raw = result.group()
                raw = raw[:-1] if raw[-1] in "-x+/" else raw
                if result and len(raw) > length:
                    length = len(raw)
                    match = [Measurement(raw, notation), result.span()[1]]
        if match is not None:
            assortment.add(match[0])
            suffix = suffix[match[1]:]

    return assortment

def projection_geometry_dimension(dimension_column, unit_column, entry):
    '''
    Extract labelled dimension measurement information from a
    given combination of a dimension column and a unit
    column.
    '''
    # Build lookup table for translating dimension labels.
    DIMS = {TXT:DIM for (DIM, LBLS) in CONFIG['translations']['dimension_labels'].items() for TXT in LBLS}

    # Retrieve the dimension column value, fix typos, and
    # perform some formatting normalizations.
    dimension = entry.get(dimension_column)
    if dimension is None or dimension == "":
        return None
    if type(dimension) == int or type(dimension) == float:
        dimension = str(dimension)
    if type(dimension) == str:
        dimension = dimension.replace('`','')
        dimension = dimension.replace('h263/4', 'h26 3/4')\
                             .replace('h551/8', 'h55 1/8')\
                             .replace("l9' 10'", "l9'-10'")\
                             .replace("44. 5/62", "44 5/62")\
                             .replace("l220, l56.5", "l220-l56.5")
        dimension = dimension.lower().strip()
        dimension = dimension[:-1] if dimension[-1] == '.' else dimension

        # Adjust for comma instead of decimal point in some cases.
        if entry['country'] in {'de','se','it','fr'} and dimension.count(',') == 1:
            dimension = dimension.replace(',','.')

        # Adjust for comma instead of separator in some cases.
        if entry['country'] in {'ca','fr'} and dimension.count(',') in {1,2}:
            dimension = dimension.replace(',','-')

    # Clear out all numeric information from the dimension string
    # (leaving only the label, if one is present).
    dim_label = dimension
    dim_label = re.sub(r'(\s*)([0-9]+)\'(\s*)([0-9]+)(\")?(\s*)', '', dim_label)
    dim_label = re.sub(r'(\s*)([0-9]+)\'(\s*)', '', dim_label)
    dim_label = re.sub(r'(\s*)([0-9]+)\.([0-9]+)(\s)([0-9]+)/(2|4|6|8)(\s|$|-|x|\+|/)(\s*)', '', dim_label)
    dim_label = re.sub(r'(\s*)([0-9]+)(\s)([0-9]+)/(2|4|6|8)(\s|$|-|x|\+|/)(\s*)', '', dim_label)
    dim_label = re.sub(r'(\s*)([0-9]+)/(2|4|6|8)(\s|$|-|x|\+|/)(\s*)', '', dim_label)
    dim_label = re.sub(r'(\s*)([0-9]+)\.([0-9]+)(\s*)', '', dim_label)
    dim_label = re.sub(r'(\s*)[0-9]+(\s*)', '', dim_label)
    dim_label = dim_label.replace('-','').replace('x','').replace('/','').replace('+','')
    dim_label = dim_label.strip().lower()

    # Retrieve the numeric and dimension information from the column.
    assortment = project_geometry_dimension_matches(dimension)

    # Obtain the unit column text and fix typos where
    # it is possible or reasonable to do so.
    unit = entry.get(unit_column)
    if unit is not None:
        unit = unit.replace('`','').replace(' black-brown/auli mirror','').replace('52','').replace('/st','')
        unit = unit.lower().strip()
    if unit is None and entry['country'] in {'se', 'de'} and set(assortment.raws()).issubset({'140', '150', '180', '200', '220', '240', '280'}):
        unit = "cm"
    if unit is None and entry['country'] == 'us' and set(assortment.notations()).issubset({'mixed', 'frac'}): # Mixed numbers are used exclusively to represent inches.
        unit = "in"
    if unit == "po" and entry['country'] in {'ca', 'fr'}:
        unit = "in"
    if unit == "meter":
        unit = "m"

    # Convert quantity representation match into a standard unit
    # (centimeters) and extend the entry with this new information.
    if assortment.set_unit(unit) and assortment:
        if dim_label in DIMS:
            set_or_update_op(entry, DIMS[dim_label] + '_max_cm', max, assortment.max().cm)
            set_or_update_op(entry, DIMS[dim_label] + '_min_cm', min, assortment.min().cm)
        set_or_update_op(entry, 'max_cm', max, assortment.max().cm)
        set_or_update_op(entry, 'max_cm', min, assortment.min().cm)
    else:
        pass #print(dimension + " :: " + str(unit) + " :: " + str(dim_label) + " :: " + str(dim_label in DIMS) + ".")

def projection_geometry(entry):
    # Process every "standard" dimension column.
    for dimension_column in ["dim" + str(i) for i in range(1,4)]:
        projection_geometry_dimension(dimension_column, "unit", entry)

    # Process the "other measurement" columns.
    ou1 = entry.get("other-unit-1")
    if ou1 == "diameter in":
        entry["other-measurement-1"] = str(entry.get("other-measurement-1")) + " diameter"
        entry["other-unit-1"] = "in"
        projection_geometry_dimension("other-measurement-1", "other-unit-1", entry)
    comments = entry.get("comments")
    if comments in CONFIG['translations']['comments']['thickness']:
        if entry.get("other-unit-1") != "diameter cm": # Filter out mistakes.
            entry["other-measurement-1"] = str(entry.get("other-measurement-1")) + " thick"
            projection_geometry_dimension("other-measurement-1", "other-unit-1", entry)

def projections_add(input, output):
    print("Projecting data in file '" + input + "' to file '" + output + "'...")
    d = json.loads(open(input, 'r').read())
    entries = d['entries']
    for i in range(len(entries)):
        entry = entries[i]
        
        # Remove any entries that do not have any data.
        for column in CONFIG['columns']:
            if entry.get(column) == "n/a": 
                del entry[column]

        # Adjust data representations and one-off errors.
        if entry.get("quantity") == 0: entry["quantity"] = 1
        if entry.get("new") is not None: entry["new"] = (entry["new"] > 0)
        if entry.get("exceptions") == "no printed page number, keyed PDF page number": entry["exceptions"] = "PDF pg #"

        # Perform projections.
        projection_product_unit_quantity(entry)
        projection_geometry(entry)

        # Progress counter.
        if i > 0 and i % 5000 == 0:
            print("...processed " + str(i) + "/" + str(len(entries)) + " entries;")

    open(output, 'w').write(json.dumps(d, sort_keys=True, indent=2)) # Human-legible.
    print("...finished writing file '" + output + "'.\n")

# Examples of calls to functions in this module.
# It is assumed that the IKEA data sets are under the
# "data/" subdirectory path.
#xlsx_files_to_json_file('data/', 'data.json', True)
#xlsx_files_to_json_file('data/', 'data.json', True, ['us'], [2005])
projections_add("data.json", "projected.json")
#json_file_to_xlsx_file('projected.json', 'ikea-data.xlsx')

#eof
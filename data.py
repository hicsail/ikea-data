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

###############################################################################
##

CONFIG = json.loads(open('config.json').read()) # For conversion/translation.

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

    # Add the column headers.
    for i in range(0,len(CONFIG['dimensions'])):
        xl_sheet.write(0, i, CONFIG['dimensions'][i], xl_bold)

    # Insert the data (all rows).
    for i in range(len(entries)):
        entry = entries[i]
        for j in range(0,len(CONFIG['dimensions'])):
            dimension = CONFIG['dimensions'][j]
            xl_sheet.write(i+1, j, entry.get(dimension))
        if i > 0 and i % 5000 == 0:
            print("...wrote " + str(i) + "/" + str(len(entries)) + " entries;")

    xl_workbook.close()
    print("...finished writing file '" + xlsx_file + "'.\n")

# Examples of calls to functions in this module.
# It is assumed that the IKEA data sets are under the
# "data/" subdirectory path.
#xlsx_files_to_json_file('data/', 'data.json', True)
#xlsx_files_to_json_file('data/', 'data.json', True, ['us'], [2005])
#json_file_to_xlsx_file('data.json', 'ikea-data.xlsx')

#eof
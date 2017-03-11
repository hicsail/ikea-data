from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist
from pandas import Series, DataFrame
import pandas as pd
import numpy as np
import xlrd
import xlrd.sheet
import xlsxwriter
import matplotlib.pyplot as plt
from matplotlib.pyplot import savefig
import argparse, os, json, cProfile

CONFIG = json.loads(open('config.json').read()) # For conversion/translation.


def groupByName(json_file, out_directory):
    '''
    divide original data into subfiles by item name
    '''
    d = json.loads(open(json_file, 'r').read())
    entries = d['entries']
    itemname = []   # store the name of items
    items={}    # dictionary, <itemname, itemlist>
    itemcount = {}

    print("divide ",json_file," by item name")
    for e in entries:
        if 'name'   in e:
            name = e.get('name')
            if name in itemname:  
                tmp = items.get(name)
            else:
                itemname.append(name)
                tmp = []
            tmp.append(e)
            items[name] = tmp

    for key,value in items.items():
        dict = {'entries': value}
        itemcount[key.replace("/","_")] = len(value)
        filename = out_directory + "/" + key.replace("/","_") + ".json"
        writeJsonFiles(filename, dict)

    # Sorted by count
    writeJsonFiles("name_count.json", sorted(itemcount.items(), key = lambda x: x[1], reverse = True))


def writeJsonFiles(json_file, content):
    '''
    write content into json_file
    '''

    open(json_file, 'w').write(json.dumps(content, sort_keys=True, indent=2)) # Human-legible.
    print("write ", json_file)

def writeBlank(input_dir, json_file, output_dir):
    '''
    The function will be called when runkmeans run on a jsonfile which has no valid items for kmeans.
    Valid item means this item has name data, max_cm data and min_cm data
    '''
    content = "does not exist valid items under this name tag"
    open(output_dir + json_file, 'w').write(json.dumps(content, sort_keys=True, indent=2))
    

def runkmeans(input_dir, json_file, output_dir, cluster_number):
    '''
    run kmeans on json_file
    k = cluster_number
    '''

    d = json.loads(open(input_dir+json_file, 'r').read())
    entries = d['entries']

    name = []
    max_cm = []
    min_cm = []
    #print("Fetch max and min...")
    validCount = 0

    for e in entries:
    	if 'name' in e and 'max_cm' in e and 'min_cm' in e:
            validCount += 1
            name.append(e.get('name'))
            max_cm.append(e.get('max_cm'))
            min_cm.append(e.get('min_cm'))


    if(validCount == 0):
        writeBlank(input_dir, json_file, output_dir)
        return 

    # store in a dataframe
    frame = DataFrame({"name": name, "max_cm": max_cm, "min_cm": min_cm})

    kmeans = KMeans(init = 'k-means++', n_clusters = cluster_number)
    predictResult = kmeans.fit_predict(frame.ix[:,['max_cm','min_cm']])

    '''
    for e in entries:
    	if 'name' in e and 'max_cm' in e and 'min_cm' in e:
    		groupid = kmeans.predict([[e.get('max_cm'), e.get('min_cm')]])
    		e['group'] = e.get('name') + "_" + str(kmeans.cluster_centers_[groupid][0][0]) + "_" + str(kmeans.cluster_centers_[groupid][0][1])
    		#print(e['group'])
    '''

    index = 0
    for i in range(len(entries)):
        if 'name' in entries[i] and 'max_cm' in entries[i] and 'min_cm' in entries[i]:
            center = kmeans.cluster_centers_[predictResult[index]]
            entries[i]['group'] = entries[i].get('name') + "_" + str(center[0]) + "_" + str(center[1])
            index += 1

    entries.sort(key=lambda k: (str(k.get('group', 0))), reverse = True)

    outputfile = output_dir + json_file.replace(".json", "result"+"_"+str(cluster_number)+".json")
    writeJsonFiles(outputfile, d)
    json_file_to_xlsx_file(outputfile, outputfile.replace(".json", ".xlsx"))
    return kmeans.inertia_
    

def json_file_to_xlsx_file(json_file, xlsx_file):
    '''
    Converts a JSON file into an XLSX file.
    '''
    print("Converting data in file '" + json_file + "' to file '" + xlsx_file + "'...")
    d = json.loads(open(json_file).read())
    entries = d['entries']

    xl_workbook = xlsxwriter.Workbook(xlsx_file)
    xl_bold = xl_workbook.add_format({'bold': True})
    xl_row_evn = xl_workbook.add_format({'bg_color':'#FFFFFF'})
    xl_row_odd = xl_workbook.add_format({'bg_color':'#EAEAEA'})
    xl_row_non = xl_workbook.add_format({'bg_color':'#FBFFD8'})
    xl_sheet = xl_workbook.add_worksheet("data")

    groups = set()
    for e in entries:
        if 'group' in e and e['group'] is not None:
            groups.add(e['group'])
    group_to_index = {g:i for (g, i) in zip(sorted(list(groups)), range(0,len(groups)))}

    # Set the column widths.
    for (i,w) in zip(range(0,11), [2,5,10,25,18,8,4,4.5,5.5,6.5,8]):
        xl_sheet.set_column(i, i, w)

    # Add the column headers.
    for i in range(0,len(CONFIG['dimensions'])):
        xl_sheet.write(0, i, CONFIG['dimensions'][i], xl_bold)

    # Insert the data (all rows).
    for i in range(len(entries)):
        entry = entries[i]

        fmt = xl_row_non
        if 'group' in entry and entry['group'] is not None:
            fmt = xl_row_evn if ((group_to_index[entry['group']])%2==0) else xl_row_odd

        for j in range(0,len(CONFIG['dimensions'])):
            dimension = CONFIG['dimensions'][j]
            xl_sheet.write(i+1, j, entry.get(dimension), fmt)

        # Progress counter.
        if i > 0 and i % 5000 == 0:
            print("...wrote " + str(i) + "/" + str(len(entries)) + " entries;")

    xl_workbook.close()
    print("...finished writing file '" + xlsx_file + "'.\n")

def iterkmeansSingleFile(input_dir, json_file, output_dir, start_k, end_k, increment):
    '''
    run kmeans for different k values
    '''
    
    if(start_k > end_k):
        print("end_k must be larger than start_k")
        return 

    error = np.zeros(int((end_k - start_k) / increment) + 1)
    #error = np.zeros(end_k + 1)


    k = start_k
    while(k <= end_k):
        error[int((k - start_k)/increment)] = runkmeans(input_dir, json_file, output_dir, k)
        #error[k] = runkmeans(input_dir, json_file, output_dir, k)
        k += increment
    #error = [4234.82432459,3720.48656751,2947.39259877]

    # get count
    d = json.loads(open(input_dir + json_file).read())
    entries = d['entries']

    fig, ax = plt.subplots()
    plt.plot(error)
    plt.xlabel('Number of clusters')
    plt.title("k starts from " + str(start_k) + " to " + str(end_k) + " increment = " + str(increment))
    #ax.set_xticks(np.linspace(0,20,0.8))
    #ax.set_xticklabels(labels)
    dummy = plt.ylabel('Error')
    #plt.show()
    savefig("figures/" + json_file.split(".")[0] + "_" + str(len(entries)) + "_" + str(start_k) + "_" + str(end_k) + "_" + str(increment) + ".png")

def iterkemansDirectory(input_dir, output_dir, start_k, end_k, increment):
    '''
    run kmeans on all the json files in input_dir and output the result to output_dir
    '''
    jsonFileList = os.listdir(input_dir)
    for i in range(len(jsonFileList)):
        iterkmeansSingleFile(input_dir, jsonFileList[i], output_dir, start_k, end_k, increment)


def kmeansBasedOnIkeaIdCount(input_dir, output_dir): 
    '''
    Use the count of Ikea ID of a jsonfile as the parameter k of its kmeans
    '''
    print("start kmeans")
    jsonFileList = os.listdir(input_dir)
    errordic = {}
    for i in range(len(jsonFileList)):
        filepath = input_dir + jsonFileList[i]
        cluster_number = getIkeaIdCount(filepath)
        if cluster_number != 0:
            error = runkmeans(input_dir, jsonFileList[i], output_dir, cluster_number)
        else:
            error = -1;
        if str(cluster_number) in errordic:
            tmp = errordic.get(str(cluster_number))
        else:
            tmp = []
        tmp.append(error)
        errordic[str(cluster_number)] = tmp

    writeJsonFiles("nameikeaidcountlittlek.json", sorted(errordic.items(), key = lambda x: x[0], reverse = True))

    count = [0] * 400

    errorarr = [0] * 400
    for key, value in errordic.items():
        result = 0
        for i in range(len(value)):
            result += value[i]
        result /= len(value)
        errorarr[int(key)] = result
        count[int(key)] = len(value)
    
    plt.plot(errorarr[:100])
    plt.title("error when use ikeaid numbers as k")
    savefig("error_ikeaidnumberkallk.png")

    plt.plot(errorarr[:100])
    plt.title("error when use ikeaid numbers as k")
    savefig("error_ikeaidnumberklittlek.png")
    
    
def getIkeaIdCount(filepath):
    '''
    get the number of different given ikeaid of a file
    '''
    d = json.loads(open(filepath, 'r').read())
    entries = d['entries']
    ikeaid = []
    for e in entries:
        if 'ikeaid' in e and 'max_cm' in e and 'min_cm' in e:
            if e.get('ikeaid') not in ikeaid:
                ikeaid.append(e.get('ikeaid'))
    return len(ikeaid)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-gi", action = "store", help = "input file argument")
    parser.add_argument("-go", action = "store", help = "output directory argument")
    parser.add_argument("-iid", action = "store", help = "the input directory of run kmeans on Ikea ID count")
    parser.add_argument("-oid", action = "store", help = "the output directory of run kmeans on IKea ID count")
    parser.add_argument("-ik", action = "store", help = "the input directory of run kmeans on given k")
    parser.add_argument("-ok", action = "store", help = "the output directory of run kmeans on given k")
    parser.add_argument("-low", action = "store", help = "give a lower bound of k")
    parser.add_argument("-high", action = "store", help = "give a higher bound of k")
    parser.add_argument("-incre", action = "store", help = "set the increment, should be positive")

    try:
        args = parser.parse_args()
    except IOError:
        pass

    if args.gi != None and args.go != None:
        groupByName(args.gi, args.go)
    if args.iid != None and args.oid != None:
        kmeansBasedOnIkeaIdCount(args.iid, args.oid)
    if int(args.incre) <= 0:
        print("Increment should be positive")
    elif int(args.low) <= 0:
        print("Both the lower bound and the higher bound shoule be larger than 0")
    elif int(args.low >= args.high):
        print("The higher bound shoule be larger than lower bound")
    else:
        iterkemansDirectory(args.ik, args.ok, int(args.low), int(args.high), int(args.incre))


if __name__ == '__main__':
    cProfile.runctx('main()', globals(), locals())

'''
def example():
    #groupByName("projected.json")
    #k = getIkeaIdCount('groupByNameData/adel.json')
    #print(runkmeans("groupByNameData/", "adel.json", "groupByNameResult/", k))
    #iterkemansDirectory("groupByNameData/", "groupByNameResult/", 1, 10, 2)
    #plot()
    #kmeansBasedOnIkeaIdCount("groupByNameData/", "groupByNameResult/")
'''

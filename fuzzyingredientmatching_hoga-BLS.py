import csv
import time

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.request import urlretrieve
from urllib.parse import urlencode
from urllib.parse import quote

from itertools import chain

import inquirer
import json
# -----------------------------------------------------------------------------
# GOAL: add to each hoga product a BLS product
# Design IDEA:
# For each hoga_product:
#   Try: find a matching BLS product
#   if there is one found:
#         check if score is > THRESHOLD
#     else:
#         search a synonym via thesaurus API.
#         for each found synonym
#             Try: find a matching BLS product
#             if there is one found:
#                 check if score is > THRESHOLD
#                 propose it as alternative (ask for user input y/n)
   
# If there is no found synonym and no matching BLS product:
#     write NA and promp warning

# write the result as .csv with the required attributes

# https://www.openthesaurus.de/synonyme/search?q=r%C3%BCebli&format=application/json
# -----------------------------------------------------------------------------

# Settings
THRESHOLD = 80 # Levensthein threshold. Keep everything >= THRESHOLD.

cant_handle_that = ["/", "%", "<", "<", "="] # Signs which produce fuzzymatch errors

inquirer.render.console.base.MAX_OPTIONS_DISPLAYED_AT_ONCE = 1000000 # maximal amount of options to choose from if user input is required.
# -----------------------------------------------------------------------------
# Read and write files
def read_products(filepath, col_id, col_name):
    """
    Reads the list of PKS id and names or the BLS id and names

    Args:
        filepath    string. Path to file
        col_id      integer. Column number of id
        col_name    integer. Column number of description
    
    Returns:
        dictonary with id as key and value as name.
    """
    with open(filepath, mode='r') as infile:
        reader = csv.reader(infile)
        next(reader, None)  # skip the headers
        # with open('coors_new.csv', mode='w') as outfile:
        #     writer = csv.writer(outfile)
        return {rows[col_id]: rows[col_name] for rows in reader}

def write_to_LUT(filename, fuzzymatch):
    """
    Write fuzzymatch in the required format to a .csv file.

    Args: 
        filename    string. Baptize the new file.
        fuzzymatch  dict. key: hogaID. 
                        Value: Dictonary of hogaproduct, BLS_id, 
                               BLS_description, Levenshtein-distance

    Returns:
        Confirmation of success.
    """
    w = csv.writer(open(filename, "w"))
    w.writerow(["idHogaProd", "fiBasisprodukt", "Hogaprodukt", 
                "BLS_Code", "BLS_Bezeichnung", "Levenshtein-distance", 
                "LCA_Bezeichnung"])
    for key, val in fuzzymatch.items():
        w.writerow([key, val[1], val[0], val[1], val[2], val[3], ""])
    return print("Wrote new file: ", filename)

def save_intermediate(filename, fuzzymatch, save_counter, STEP=5):
    """
    Save what's already done after each fifth step.
    
    Args: 
        filename    str. Filename
        fuzzymatch  dict. hoga_id as key. hoga-product, BLS-id, BLS-name, Levenshtein-distance as values.
        STEP        int. After how many steps the file should be saved.

    Returns:
        prompt indicating that a file is saved.
    """
    save_counter += 1

    if save_counter % 5 == 0:
        write_to_LUT(filename, fuzzymatch)
        print("I just saved what's already done.")

    return save_counter
# -----------------------------------------------------------------------------
# Find BLS alternative to hoga
def split_product_by_symbol(product, symbol, LIMIT, cant_handle_that, return_best):
    """
    Splits the provided product, by the provided symbol and returns the best matching products. 
    The number of the returned products can be specified by limit.

    Args:
        product     string. Product name of hoga shop.
        symbol      string. Something like ", " or " ".
        limit       int.    Number of matched products to be returned.
        cant_handle_that    list. of symbols which fuzzywuzzy can't work with. 
        return_best bool.   If True, it only returns the matching product with the highest score

    Returns:
        List of tuples of matched products with their hoga_product, BLS_ID, BLS_product, Levenshtein-distance
    """
    split_prod = [0, 0, 0, 0]

    if type(product) == tuple:
        product = product[0]

    elif type(product) == list:
    #     product = list(chain(product))
        for j in range(len(product)):
            for i in range(len(product[j][0].split(symbol))):
                # split the product by comma and keep the highest matching one. 
                # i.e. Baumnüsse, ganz -> "Baumnüsse", "ganz" -> keep only "Baumnüsse"
                splitted_prod = product[j][0].split(symbol)[i]
                if splitted_prod in cant_handle_that:
                    # jumps to next iteration if it's a "/" to minimize fuzzymatch warnings.
                    continue # Unlike "pass" which does simply nothing.        
                else:
                    # gets the number (LIMIT) of best matching products
                    temp = process.extract(splitted_prod, BLS, limit = LIMIT)
                    if return_best == True:
                        # checks if only the best should be returned.
                        for j in range(len(temp)):
                            if temp[j][1] > split_prod[1]:
                                split_prod = temp[j]
                    else:
                        # or instead return the whole list
                        if split_prod[3] == 0:
                            split_prod = temp
                        else:
                            split_prod.extend(temp)

    if type(product) == str:
        for i in range(len(product.split(symbol))):
            # split the product by comma and keep the highest matching one. 
            # i.e. Baumnüsse, ganz -> "Baumnüsse", "ganz" -> keep only "Baumnüsse"
            splitted_prod = product.split(symbol)[i]
            if splitted_prod in cant_handle_that:
                # jumps to next iteration if it's a "/" to minimize fuzzymatch warnings.
                continue # Unlike "pass" which does simply nothing.        
            else:
                temp = process.extract(splitted_prod, BLS, limit = LIMIT)
                if return_best == True:
                    for j in range(len(temp)):
                        if temp[j][1] > split_prod[1]:
                            split_prod = temp[j]
                else:
                    split_prod = temp

    return split_prod

def enter_alternative(alternative_dict):
    substring = input('Enter a better alternative: ')
    alternative_name = []

    for name in alternative_dict.values():
        if (substring.lower() in name.lower()):
            alternative_name.append(name)
    return alternative_name

def find_alternative_by_user(alternative_dict, product):
    alternative_name = enter_alternative(alternative_dict)
    global good_alternative
    
    if len(alternative_name) == 0:
        nothing_found_tryagain = input("I couldn't find anything that fits. Try again? (y/n)")
        if nothing_found_tryagain in ["n", "N"]:
            good_alternative = [product, "NA", "NA", "NA"]
            return good_alternative
        elif nothing_found_tryagain in ["y", "Y"]:
            alternative_name = enter_alternative(alternative_dict)

    alternative_name.append("None of them")
    questions = [
        inquirer.List('user_alternative',
        message="I found these BLS products matching your entry. Wich one should I keep?",
        choices=alternative_name,
        ),
    ]
        
    answers = inquirer.prompt(questions)
    if answers['user_alternative'] == "None of them":
        find_alternative_by_user(alternative_dict, product)
    else:
        for blsID, blsProd in BLS.items():
            if blsProd == answers['user_alternative']:
                good_alternative = [product, blsID, blsProd, "NA"]
    return good_alternative

def BLS_alternative(product, alternative_dict, THRESHOLD, hoga_ID):
    """
    Finds a fuzzy matching BLS product corresponding to hogaproduct.
    If there is no clear choice, the user can choose.

    Args:
        product             string. Product name of Hoga shop.
        alternative_dict    dict. Product id and name of "Bundeslebensmittel"-table.
        THRESHOLD           integer. Threshold, specifying the minimal Levenshtein-distance to keep.
        BLS                 dict. BLS id and product name dictonary.

    Returns:
        list of hoga_product, BLS_ID, BLS_product, Levenshtein-distance
    """
    # build lists
    commasplit_prod = [0, 0, 0, 0]
    spaceCommasplit_prod = [0, 0, 0, 0]
    best_alternative = [0, 0, 0, 0]

    commasplit_prod = split_product_by_symbol(product, ", ", 4, cant_handle_that, True)
    # for i in range(len(product.split(", "))):
    #     # split the product by comma and keep the highest matching one. 
    #     # i.e. Baumnüsse, ganz -> "Baumnüsse", "ganz" -> keep only "Baumnüsse"
    #     splitted_prod = product.split(", ")[i]
    #     if splitted_prod in cant_handle_that:
    #         # jumps to next iteration if it's a "/" to minimize fuzzymatch warnings.
    #         continue # Unlike "pass" which does simply nothing.        
    #     else:
    #         temp = process.extractOne(splitted_prod, BLS)
    #         if temp[1] > commasplit_prod[1]:
    #             commasplit_prod = temp

    spaceCommasplit_prod = split_product_by_symbol(commasplit_prod, " ", 4, cant_handle_that, False)
    # for i in range(len(commasplit_prod[0].split(" "))):
    #     # Split the first entry of the commasplitted product and split it by spaces.
    #     # Keep only the highest scoring one. I.e. "Gewürzmischung für Fleisch, trocken" -> "Gewürzmischung für Fleisch" -> "Gewürzmischung", "für", "Fleisch" -> keep "Gewürzmischung"
    #     comsplitted_prod = commasplit_prod[0].split(" ")[i]
    #     if comsplitted_prod in cant_handle_that:
    #         # jumps to next iteration if it's a "/" to minimize fuzzymatch warnings.
    #         continue # Unlike "pass" which does simply nothing.
    #     else:
    #         temp = process.extractOne(comsplitted_prod, BLS)
    #         if temp[1] > spaceCommasplit_prod[1]:
    #             spaceCommasplit_prod = temp
    if (type(commasplit_prod) == list and len(commasplit_prod) > 1) and (best_alternative[3] == 0):
        # Let the user make the choice
        choice = []
        choice.append("None of them")
        choice.extend(commasplit_prod)
        choice.extend(chain(spaceCommasplit_prod))

        print("------------------------")
        print(product)
        questions = [
            inquirer.List('product_choice',
            message="which alternative matches best to the product above?",
            choices=choice,
            ),
        ]
        answers = inquirer.prompt(questions)
        
        if answers['product_choice'] == "None of them":
            # best_alternative =  [product, "NA", "NA", "NA"]
            best_alternative = find_alternative_by_user(alternative_dict, product)
            
        else:
            best_alternative =  [product, answers['product_choice'][2], answers['product_choice'][0], int(answers['product_choice'][1])]
    
    else:
        for j in range(len(spaceCommasplit_prod)):
            if best_alternative[3] == 0:
                if (commasplit_prod[1] and spaceCommasplit_prod[j][1] >= THRESHOLD):
                    # if both split variants are equally good,
                    if (commasplit_prod[2] == spaceCommasplit_prod[j][2]):
                        # check if they are exactely the same (same BLS code)
                        if spaceCommasplit_prod[j][1] > best_alternative[3]:
                            best_alternative = [product, spaceCommasplit_prod[j][2], spaceCommasplit_prod[j][0], int(spaceCommasplit_prod[j][1])] # hoga_ID, hoga_product, BLS_ID, BLS_product, Levenshtein-distance
                    else:
                        # Let the user make the choice
                        choice = list(chain(spaceCommasplit_prod))
                        choice.append(commasplit_prod)
                        choice.append("None of the above")


                        print("------------------------")
                        print(product)
                        questions = [
                            inquirer.List('product_choice',
                                            message="which alternative matches best to the product above?",
                                            # choices=[commasplit_prod, spaceCommasplit_prod, "None of the above"],
                                            choices=choice,
                                        ),
                        ]
                        answers = inquirer.prompt(questions)
                        
                        if answers['product_choice'] == "None of the above":
                            # best_alternative =  [product, "NA", "NA", "NA"]
                            best_alternative = find_alternative_by_user(alternative_dict, product)

                        else:
                            best_alternative =  [product, answers['product_choice'][2], answers['product_choice'][0], int(answers['product_choice'][1])]

                elif commasplit_prod[1] >= THRESHOLD:
                    best_alternative =  [product, commasplit_prod[2], commasplit_prod[0], int(commasplit_prod[1])]

                elif spaceCommasplit_prod[j][1] >= THRESHOLD:
                    if spaceCommasplit_prod[j][1] > best_alternative[3]:
                        best_alternative =  [product, spaceCommasplit_prod[j][2], spaceCommasplit_prod[j][0], int(spaceCommasplit_prod[j][1])]

                else:
                    best_alternative =  [product, "NA", "NA", "NA"]         
            else:
                break

    return best_alternative
    # Hyptohesis: Does Levenshtein distance work less good for big words compared to small ones? i.e. Baumnuss -> Rum, 100
    # How about inserting a penalty for word length?

# -----------------------------------------------------------------------------
# Finding synonyms
def get_jsonparsed_data(url):
    """
    Receive the content of ``url``, parse it as JSON and return the object.

    Parameters
    ----------
    url : str

    Returns
    -------
    dict
    """
    try:
        response = urlopen(url)
    except HTTPError as e:
        if e.code == 429:
            time.sleep(5)
            return get_jsonparsed_data(url)

    data = response.read().decode("utf-8")
    return json.loads(data)

def parse_url_for_request(item):
    """
    Recieve the url to query all synonyms from "item"

    Args:
        item    string.
    
    Returns: 
        url to query thesaurus
    """
    qstr = quote(item)
    query_url = "https://www.openthesaurus.de/synonyme/search?q=" + qstr + "&format=application/json"
    return query_url

def find_synonyms(item):
    """
    Search synonyms for "item".

    Args:
        item    string
    
    Returns:
        dict with synonyms for "item"
    """
    url = parse_url_for_request(item)
    try:
        synonym = get_jsonparsed_data(url)['synsets'][0]['terms']
        results = []
        for i in range(len(synonym)):
            results.append(synonym[i]['term'])
    except IndexError:
        results = []
    return results

# -----------------------------------------------------------------------------
# Read in Hoga shop data
hoga = read_products("QRY_ProdukteBrowse_Table_Export_Produkte_Hoga_limmat_only.csv", 1, 3)

# -----------------------------------------------------------------------------
# Read in BLS data
BLS  = read_products("Bundeslebensmittelschlüssel_(BLS)_(2014)_VERTRAULICH_NUR_INTERN.csv", 0, 1)

# -----------------------------------------------------------------------------
# Find a matching BLS product given the HOGA list
fuzzymatch = {}
save_counter = 0

for hogaID in hoga:
    # extract the product name for each ID in the pauli products dictonary
    hogaproduct = hoga[hogaID]

    # print some output for status info
    print(hogaID, hogaproduct)

    # Find a matching BLS product
    fuzzymatch[hogaID] = BLS_alternative(hogaproduct, BLS, THRESHOLD, hogaID)
    # if no alternative is found, 
    if (fuzzymatch[hogaID] == None) or (fuzzymatch[hogaID][1] == "NA"):
        try:
            # look for a synonym of the hogaproduct 
            pauli_synonym = find_synonyms(fuzzymatch[hogaID][0].split(", ")[0])
            # and try to find an alternative BLS product for the synonym. 
            # Keep only the best matching synonymous product.
            best_synonym = []
            for syn in pauli_synonym:
                syn = syn.replace("ß", "ss")
                temp = process.extractOne(syn, BLS)
                if ((temp[1] >= THRESHOLD) and (best_synonym == [] or temp[1] > best_synonym[1])):
                    best_synonym = temp
            fuzzymatch[hogaID] = [hogaproduct, best_synonym[2], best_synonym[0], int(best_synonym[1])]
        except:
            # If no synonym is found, write NAs for BLS code and product.
            fuzzymatch[hogaID] = [hogaproduct, "NA", "NA", "NA"]

    save_counter = save_intermediate("LUT_hoga_BLS.csv", fuzzymatch, save_counter, STEP=5)

# -----------------------------------------------------------------------------
# Write as csv output
write_to_LUT("LUT_hoga_BLS.csv", fuzzymatch)
print("Process finished.")
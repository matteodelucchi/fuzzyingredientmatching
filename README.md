# fuzzyingredientmatching

## Requirements 
```
sudo pip3 install pandas
sudo pip3 install inquirer
sudo pip3 install python-Levenshtein
sudo pip3 install fuzzywuzzy
```
change in the directory of fuzzywuzzy
```
python3 setup.py install
```
Tested under Ubuntu 19.04 with Python 3.7.3

## Production Pipeline
The pipeline is by purpose not fully automatised because the matching is based on a statistical measure of string similarity. Which is more or less exact... Depending on the use, it's important for manual corrections between the steps. 

1. Match PKS entries with BLS entries  
Run this file: ```fuzzyingredientmatching.py```  
Input: ```Produkte_Liste_PKS_Ansicht1.csv``` and ```Bundeslebensmittelschlüssel_(BLS)_(2014)_VERTRAULICH_NUR_INTERN.csv``` -> Adapt the paths and filenames to your system  
Output: ```LUT_PKS_BLS.csv```

2. Match Hoga-shop entries with BLS entries  
Run this file: ```fuzzyingredientmatching_hoga-BLS.py```  
Input: ```QRY_ProdukteBrowse_Table_Export_Produkte_Hoga_limmat_only.csv``` and ```Bundeslebensmittelschlüssel_(BLS)_(2014)_VERTRAULICH_NUR_INTERN.csv``` -> Adapt the paths and filenames to your system  
Output: ```LUT_hoga_BLS.csv```

3. Make manual corrections to both look-up tables if necessary.

4. Merge them by the BLS code  
Run this file: ```merge_all.py```  
Input: The manually corrected output from step 1 and 2 .  
Output: ```LUT_PKS_HOGA_BLS_part_corr.csv```

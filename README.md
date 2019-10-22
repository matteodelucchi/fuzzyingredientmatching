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
## Production Pipeline
The pipeline is by purpose not fully automatised because the matching is based on a statistical measure of string similarity. Which is more or less exact... Depending on the use, it's important for manual corrections between the steps. 

1. Match PKS entries with BLS entries
```fuzzyingredientmatching.py```

2. Match Hoga-shop entries with BLS entries
```fuzzyingredientmatching_hoga-BLS.py```

3. Merge them by the BLS code
```merge_all.py```

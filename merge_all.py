import csv
import pandas as pd

def load_dataframe(LUT, variables):
    """
    Load the .csv look up table as pandas dataframe and keep only the necessary columns (variables)

    Args: 
        LUT         str. Filepath to the hoga-bls or pks-bls look up table which results from fuzzyingredientmatching*.py
        variables   list of strings with the column names to keep. Basically just the id and the correstponding product name.

    Return:
        pandas data frame with the necessary variables.
    """
    df = pd.read_csv(LUT)[variables]
    return df

#----------------------------------------
### Load the two individal matchings as pandas data frames
hoga_bls = load_dataframe("/home/delt/ZHAW/MNIdatabase/LUT_hoga_BLS_Marleen-BB_empty-cells.csv", ['idHogaProd', 'Hogaprodukt', 'BLS_Code', 'BLS_Bezeichnung'])
pks_bls = load_dataframe("/home/delt/ZHAW/MNIdatabase/PKS_BLS_final_20190924.csv", ['idPauliProd', 'Pauliprodukt', 'BLS_Code', 'BLS_Bezeichnung'])

### Merge the two matchings by their BLS_Code (serves as key)
pks_bls_hoga = pd.merge(pks_bls, hoga_bls, on=['BLS_Code'], how='inner')

### Save the merged Look-up-table
pks_bls_hoga.to_csv(r'LUT_PKS_HOGAlimmat_BLS_corr_BB.csv')
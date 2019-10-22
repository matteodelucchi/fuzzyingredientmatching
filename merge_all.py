import csv
import pandas as pd

def load_dataframe(LUT, variables):
    """
    Load the .csv look up table as pandas dataframe and keep only the necessary columns (variables)

    Args: 
        hoga_bls    str. Filepath to the hoga-bls look up table which results from fuzzyingredientmatching_hoga-BLS.py
        pks_bls     str. Filepath to the pkd-bls look up table which results from fuzzyingredientmatching.py

    Return:
        pandas data frame with the necessary variables.
    """
    df = pd.read_csv(LUT)[variables]
    return df

#----------------------------------------
### Load the two individal matchings as pandas data frames
hoga_bls = load_dataframe("LUT_hoga_BLS.csv", ['idHogaProd', 'Hogaprodukt', 'BLS_Code', 'BLS_Bezeichnung'])
pks_bls = load_dataframe("LUT_PKS_BLS.csv", ['idPauliProd', 'Pauliprodukt', 'BLS_Code', 'BLS_Bezeichnung'])

### Merge the two matchings by their BLS_Code (serves as key)
pks_bls_hoga = pd.merge(pks_bls, hoga_bls, on=['BLS_Code'], how='inner')

### Save the merged Look-up-table
pks_bls_hoga.to_csv(r'LUT_PKS_HOGA_BLS.csv')
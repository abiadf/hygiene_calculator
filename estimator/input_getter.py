'''This module takes the input file and reads it'''

import pandas as pd
from pathlib import Path


def read_file_in_pandas(path_location = r"C:\\bacteria_estimator\\input"):
    '''This function reads the input file into a pandas dataframe'''
    
    input_file_dir = Path(path_location)
    file_names   = [f.name for f in input_file_dir.iterdir()]
    desired_file = file_names[0]
    full_path    = input_file_dir / desired_file
    df           = pd.read_csv(full_path, delimiter = ';')
    return df


df = read_file_in_pandas(path_location = r"C:\\bacteria_estimator\\input")

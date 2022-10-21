import os
import pandas as pd

def get_add_two_numbers_dataset(num_examples: int= None):
    df = pd.read_csv(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'add_two.csv'
    ), delimiter=',')
    df['output_strings'] = df['output_strings'].str.replace("'", "")
    if num_examples is not None:
        df = df.sample(n=num_examples)
    return df['input_strings'].values, df['output_strings'].values
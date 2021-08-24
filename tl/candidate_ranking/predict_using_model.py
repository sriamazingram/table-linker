import sys

import pandas as pd
from tl.exceptions import RequiredInputParameterMissingException, UnsupportTypeError
from tl.file_formats_validator import FFV
import torch
import torch.nn as nn
import torch.nn.functional as F
import pickle


# Model Definition
class PairwiseNetwork(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        # original 12x24, 24x12, 12x12, 12x1
        self.fc1 = nn.Linear(hidden_size, 2 * hidden_size)
        self.fc2 = nn.Linear(2 * hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, hidden_size)
        self.fc4 = nn.Linear(hidden_size, 1)

    def forward(self, pos_features, neg_features):
        # Positive pass
        x = F.relu(self.fc1(pos_features))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        pos_out = torch.sigmoid(self.fc4(x))

        # Negative Pass
        x = F.relu(self.fc1(neg_features))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        neg_out = torch.sigmoid(self.fc4(x))

        return pos_out, neg_out

    def predict(self, test_feat):
        x = F.relu(self.fc1(test_feat))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        test_out = torch.sigmoid(self.fc4(x))
        return test_out


def predict(features, output_column, ranking_model, min_max_scaler_path, file_path=None, df=None):
    if file_path is None and df is None:
        raise RequiredInputParameterMissingException(
            'One of the input parameters is required: {} or {}'.format("file_path", "df"))

    if file_path:
        df = pd.read_csv(file_path, dtype=object)

    ffv = FFV()
    if not (ffv.is_candidates_file(df)):
        raise UnsupportTypeError("The input file is not a candidate file!")

    if not (ranking_model) and not (min_max_scaler_path):
        raise RequiredInputParameterMissingException(
            'One of the input parameters is required: {} or {}'.format("ranking_model", "min_max_scaler_path"))

    normalize_features = features.split(",")

    model = PairwiseNetwork(len(normalize_features))
    model.load_state_dict(torch.load(ranking_model))
    scaler = pickle.load(open(min_max_scaler_path, 'rb'))

    df[normalize_features] = df[normalize_features].astype('float64')
    grouped_obj = df.groupby(['column', 'row'])
    new_df_list = []
    pred = []
    for cell in grouped_obj:
        cell[1][normalize_features] = scaler.transform(cell[1][normalize_features])
        df_copy = cell[1].copy()
        df_features = df_copy[normalize_features]
        new_df_list.append(df_copy)
        arr = df_features.to_numpy()
        test_inp = []
        for a in arr:
            test_inp.append(a)
        test_tensor = torch.tensor(test_inp).float()
        scores = torch.squeeze(model.predict(test_tensor)).tolist()
        pred.extend(scores) if isinstance(scores, list) else pred.append(scores)
    out_df = pd.concat(new_df_list)
    out_df[output_column] = pred
    out_df[output_column].fillna(0.0, inplace=True)

    return out_df

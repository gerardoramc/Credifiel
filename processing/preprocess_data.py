import os
import pandas as pd
import numpy as np
import joblib
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm
import json

from process import mask_client_probabilities, append_hit_costs, append_profits, calculate_best_emisora


files = pd.DataFrame({"files":os.listdir("processing/modelOut")})

def preprocess(train_df):
    train_df["dic"] = train_df.apply(lambda x: {
        "bank":str(x['IdBanco_Credito']),
        "payment": float(x['montoCobrar'])
                }, axis=1)
    features = ['montoCobrar', 'transCount', 'IdBanco_Credito',
                'pagoAnterior', 'ratioAnterior', 'residualAnterior', 'idEmisora', "dic", "idCredito"]
    train_df = train_df.dropna(subset=features)
    train_df = train_df[features]
    train_df = pd.get_dummies(train_df, columns=['IdBanco_Credito', 'idEmisora'], drop_first=True)
    train_df['montoCobrar'] = np.log1p(train_df['montoCobrar'])

    numeric_cols = ['montoCobrar', 'transCount', 'pagoAnterior', 'ratioAnterior', 'residualAnterior']
    scaler = StandardScaler()
    train_df[numeric_cols] = scaler.fit_transform(train_df[numeric_cols])
    return train_df

test_parquet_path="processing/2025Test.parquet"
test_df = pd.read_parquet(test_parquet_path)
test_df = preprocess(test_df)

def test(x):
    model = joblib.load(os.path.join("processing/modelOut", x))
    test_df[list(set(model.feature_names_in_).difference(set(test_df.columns)))] = False
    return model.predict_proba(test_df[model.feature_names_in_])
files["predicts"] = files.files.apply(test)
files["emisora"] = files.files.apply(lambda x: x[8:].split(".")[0])

def crearJson(x):
    json = {}
    files.apply(lambda model: json.update({model.emisora: min(model.predicts[x.name]) if len(model.predicts[x.name]) == 2 else 0}), axis=1)
    x.dic.update({"probabilities":json})
test_df.apply(crearJson, axis=1)


emisoras_banco = pd.read_csv("data/EmisoraBancoPrecios.csv")

clients = test_df.set_index("idCredito")["dic"].to_dict()

mask_client_probabilities(emisoras_banco, clients)
append_hit_costs(emisoras_banco, clients)
append_profits(clients)
print(json.dumps(calculate_best_emisora(clients), indent=4))



import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib

df = pd.read_csv("model/numeric_crop_yield_small.csv")
X = df.drop("crop_yield", axis=1)
y = df["crop_yield"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(random_state=42)
model.fit(X_train, y_train)

joblib.dump({"model": model, "columns": X.columns.tolist()}, "model/retrained_model.pkl")

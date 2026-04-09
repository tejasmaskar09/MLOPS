"""
Experiment 1: Train ML Model and Deploy Model to File (PKL)
============================================================
- Train a Linear Regression model on student_data.csv
- Save the trained model using Pickle
- Verify that the model loads correctly and produces predictions
"""

import pickle
import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def main():
    # ------------------------------------------------------------------
    # 1. Load dataset
    # ------------------------------------------------------------------
    data_path = os.path.join(os.path.dirname(__file__), "student_data.csv")
    df = pd.read_csv(data_path)
    print(f"[INFO] Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")
    print(df.head())

    # ------------------------------------------------------------------
    # 2. Prepare features and target
    # ------------------------------------------------------------------
    feature_cols = ["hours", "attendance", "previous_score"]
    target_col = "final_score"

    X = df[feature_cols].values
    y = df[target_col].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"[INFO] Train size: {X_train.shape[0]}, Test size: {X_test.shape[0]}")

    # ------------------------------------------------------------------
    # 3. Train model
    # ------------------------------------------------------------------
    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print(f"\n=== Model Evaluation ===")
    print(f"  MAE  : {mae:.4f}")
    print(f"  RMSE : {rmse:.4f}")
    print(f"  R²   : {r2:.4f}")
    print(f"  Coefficients : {model.coef_}")
    print(f"  Intercept    : {model.intercept_:.4f}")

    # ------------------------------------------------------------------
    # 4. Save model with Pickle
    # ------------------------------------------------------------------
    model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"\n[INFO] Model saved to {model_path}")

    # ------------------------------------------------------------------
    # 5. Verify: reload model and compare predictions
    # ------------------------------------------------------------------
    with open(model_path, "rb") as f:
        loaded_model = pickle.load(f)

    y_pred_loaded = loaded_model.predict(X_test)
    assert np.allclose(y_pred, y_pred_loaded), "Loaded model predictions differ!"
    print("[INFO] Verification PASSED — loaded model produces identical predictions.")

    # Quick sanity check with a sample input
    sample = np.array([[5, 70, 60]])
    prediction = loaded_model.predict(sample)
    print(f"[INFO] Sample prediction (hours=5, attendance=70, previous_score=60): {prediction[0]:.2f}")


if __name__ == "__main__":
    main()

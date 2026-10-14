"""One market + one commodity CSV: date,price. Forecasts one day ahead."""
import argparse
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

def with_lags(frame):
    frame = frame.sort_values("date").copy()
    frame["date"] = pd.to_datetime(frame["date"])
    for lag in (1, 7, 14):
        frame[f"lag_{lag}"] = frame["price"].shift(lag)
    frame["rolling_7"] = frame["price"].shift(1).rolling(7).mean()
    frame["day_of_year"] = frame["date"].dt.dayofyear
    return frame.dropna().reset_index(drop=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path, help="CSV for a single normalized market and commodity")
    parser.add_argument("--output", type=Path, default=Path("models/price_forecaster.joblib"))
    args = parser.parse_args()
    data = pd.read_csv(args.csv, parse_dates=["date"])
    if not {"date", "price"}.issubset(data.columns):
        raise SystemExit("CSV must contain date and price columns, in consistent units.")
    data = with_lags(data)
    if len(data) < 60:
        raise SystemExit("Need at least 60 observations after lag creation; more history is preferable.")
    features = ["lag_1", "lag_7", "lag_14", "rolling_7", "day_of_year"]
    split = int(len(data) * 0.8)
    train, valid = data.iloc[:split], data.iloc[split:]
    model = HistGradientBoostingRegressor(random_state=42)
    model.fit(train[features], train["price"])
    print(f"Time holdout MAE: {mean_absolute_error(valid['price'], model.predict(valid[features])):.3f}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model":model, "features":features, "last_rows":data.tail(14)}, args.output)
    print(f"Saved {args.output}. Validate by market and compare with a seasonal-naive baseline.")

if __name__ == "__main__":
    main()

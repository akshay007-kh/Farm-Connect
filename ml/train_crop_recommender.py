"""Train a crop recommender from a CSV with N,P,K,temperature,humidity,ph,rainfall,label."""
import argparse
from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import make_column_selector
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--output", type=Path, default=Path("models/crop_recommender.joblib"))
    args = parser.parse_args()
    data = pd.read_csv(args.csv)
    required = set(FEATURES + ["label"])
    if not required.issubset(data.columns):
        raise SystemExit(f"CSV must include: {', '.join(sorted(required))}")
    X, y = data[FEATURES], data["label"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = make_pipeline(SimpleImputer(strategy="median"), RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42))
    model.fit(X_train, y_train)
    print(classification_report(y_test, model.predict(X_test), zero_division=0))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model":model, "features":FEATURES}, args.output)
    print(f"Saved {args.output}; validate locally before using recommendations.")

if __name__ == "__main__":
    main()

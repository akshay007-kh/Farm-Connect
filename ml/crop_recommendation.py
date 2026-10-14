"""Load the trained artifact and return ranked labels for one soil/weather sample."""
from pathlib import Path
import joblib
import pandas as pd

def recommend(values: dict, artifact: Path = Path("models/crop_recommender.joblib")) -> list[dict]:
    bundle = joblib.load(artifact)
    features = bundle["features"]
    row = pd.DataFrame([[values.get(name) for name in features]], columns=features)
    model = bundle["model"]
    probabilities = model.predict_proba(row)[0]
    ranked = sorted(zip(model.classes_, probabilities), key=lambda pair: pair[1], reverse=True)
    return [{"crop":str(label), "confidence":round(float(score), 4)} for label, score in ranked[:3]]

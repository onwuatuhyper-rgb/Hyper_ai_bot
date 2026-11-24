import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score
from core.features import FeatureEngineer

class MarketAIModel:
    LABEL_MAP = {1: "BUY", -1: "SELL", 0: "NEUTRAL"}

    def __init__(self, pair: str):
        self.pair = pair
        self.model = None
        self.best_model_name = "Untrained"
        self.unseen_accuracy = 0.0
        self.is_trained = False

    def train_and_validate(self, candles: list) -> dict:
        df = FeatureEngineer.build_features(candles)
        trainable = df.iloc[:-1].copy()
        if len(trainable) < 60:
            raise ValueError(f"{self.pair}: Not enough candles.")
        X = trainable[FeatureEngineer.FEATURE_COLUMNS].values
        y = trainable["target"].values
        split = int(len(trainable) * 0.80)
        X_tr, X_te, y_tr, y_te = X[:split], X[split:], y[:split], y[split:]
        candidates = {
            "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42),
            "GradientBoosting": GradientBoostingClassifier(n_estimators=80, learning_rate=0.05, max_depth=3, random_state=42),
        }
        best_acc, best_clf, best_name = -1.0, None, ""
        for name, clf in candidates.items():
            clf.fit(X_tr, y_tr)
            acc = float(accuracy_score(y_te, clf.predict(X_te)))
            if acc > best_acc:
                best_acc, best_clf, best_name = acc, clf, name
        best_clf.fit(X, y)
        self.model = best_clf
        self.best_model_name = best_name
        self.unseen_accuracy = round(best_acc, 4)
        self.is_trained = True
        return {"pair": self.pair, "model": best_name, "unseen_accuracy": self.unseen_accuracy}

    def predict_latest(self, candles: list) -> dict:
        if not self.is_trained or self.model is None:
            self.train_and_validate(candles)
        df = FeatureEngineer.build_features(candles)
        latest = df[FeatureEngineer.FEATURE_COLUMNS].iloc[-1:].values
        probs = self.model.predict_proba(latest)[0]
        classes = list(self.model.classes_)
        idx = int(np.argmax(probs))
        return {
            "pair": self.pair,
            "signal": self.LABEL_MAP.get(int(classes[idx]), "NEUTRAL"),
            "confidence": round(float(probs[idx]), 4),
            "model": self.best_model_name,
            "unseen_accuracy": self.unseen_accuracy,
  }
      

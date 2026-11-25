import numpy as np
import pandas as pd

class FeatureEngineer:
    FEATURE_COLUMNS = [
        "body_pct", "upper_wick_pct", "lower_wick_pct", "range_pct",
        "return_1", "return_3", "return_6", "ema_fast_diff",
        "ema_slow_diff", "atr_pct", "rsi_14", "volatility_10",
    ]

    @staticmethod
    def build_features(candles: list) -> pd.DataFrame:
        if not candles or len(candles) < 35:
            raise ValueError("Need at least 35 candles to compute AI features.")
        df = pd.DataFrame(candles)
        for col in ("open", "high", "low", "close"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df.dropna(subset=["open", "high", "low", "close"], inplace=True)
        df.reset_index(drop=True, inplace=True)

        full_range = (df["high"] - df["low"]).replace(0, np.nan)
        df["body_pct"] = ((df["close"] - df["open"]) / full_range).fillna(0.0)
        df["upper_wick_pct"] = ((df["high"] - df[["open", "close"]].max(axis=1)) / full_range).fillna(0.0)
        df["lower_wick_pct"] = ((df[["open", "close"]].min(axis=1) - df["low"]) / full_range).fillna(0.0)
        df["range_pct"] = (full_range / df["close"]).fillna(0.0)

        df["return_1"] = df["close"].pct_change(1)
        df["return_3"] = df["close"].pct_change(3)
        df["return_6"] = df["close"].pct_change(6)

        ema_9 = df["close"].ewm(span=9, adjust=False).mean()
        ema_21 = df["close"].ewm(span=21, adjust=False).mean()
        df["ema_fast_diff"] = (df["close"] - ema_9) / df["close"]
        df["ema_slow_diff"] = (ema_9 - ema_21) / df["close"]

        prev = df["close"].shift(1)
        tr = pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1).max(axis=1)
        df["atr_pct"] = tr.rolling(14).mean() / df["close"]

        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, np.nan)
        df["rsi_14"] = (100 - (100 / (1 + gain / loss))).fillna(50.0) / 100.0
        df["volatility_10"] = df["return_1"].rolling(10).std().fillna(0.0)

        fut = df["close"].shift(-1) / df["close"] - 1.0
        df["target"] = 0
        df.loc[fut > df["atr_pct"] * 0.25, "target"] = 1
        df.loc[fut < -df["atr_pct"] * 0.25, "target"] = -1

        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(subset=FeatureEngineer.FEATURE_COLUMNS, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
      

from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBClassifier
import numpy as np


def train_and_select_model(df):
    """
    Trains XGBoost via TimeSeriesSplit + SelectKBest pipeline.
    FIX: Removed use_label_encoder=False (param dropped in XGBoost >= 1.6).
    FIX: scale_pos_weight zero-division guard.
    FIX: Duplicate feature column guard.
    FIX: Minimum data size check.
    """
    drop_cols    = ['Target', 'Target_Price', 'Date', 'target_return']
    all_features = [c for c in df.columns if c not in drop_cols]

    # Add sentiment placeholders only if missing
    for col, default in [('Sentiment_Score', 0.0), ('Pos_Neg_Ratio', 1.0), ('News_Count', 0)]:
        if col not in df.columns:
            df[col] = default
        if col not in all_features:
            all_features.append(col)

    # Remove exact duplicate column names (safety)
    all_features = list(dict.fromkeys(all_features))

    df = df.dropna()

    if len(df) < 60:
        raise ValueError(f"Not enough training rows after dropna: {len(df)} (need ≥ 60).")

    X_full = df[all_features]
    y_full = df['Target']

    split_idx    = int(len(X_full) * 0.8)
    X_train_full = X_full.iloc[:split_idx]
    y_train      = y_full.iloc[:split_idx]
    y_reg_train  = df['target_return'].iloc[:split_idx]

    # Need at least 2 classes
    unique_classes = y_train.unique()
    if len(unique_classes) < 2:
        raise ValueError(
            f"Training target contains only one class ({unique_classes.tolist()}). "
            "Need both UP (1) and DOWN (0) examples."
        )

    # Feature Selection on training split only (no leakage)
    k_features    = min(10, len(all_features))
    selector      = SelectKBest(score_func=f_classif, k=k_features)
    selector.fit(X_train_full, y_train)
    features      = np.array(all_features)[selector.get_support()].tolist()

    X_train = df[features].iloc[:split_idx]
    scaler  = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    print(f"[TRAIN] XGBoost | features={features} | rows={len(X_train)}")
    tscv = TimeSeriesSplit(n_splits=5)

    n_pos = int(y_train.sum())
    n_neg = len(y_train) - n_pos
    scale_pos_weight = (n_neg / n_pos) if n_pos > 0 else 1.0

    # FIX: use_label_encoder removed in XGBoost >= 1.6 — don't pass it
    xgb = XGBClassifier(
        eval_metric='logloss',
        random_state=42,
        scale_pos_weight=scale_pos_weight,
    )

    param_grid = {
        'n_estimators':  [100, 200, 300],
        'max_depth':     [3, 5, 7],
        'learning_rate': [0.01, 0.05, 0.1],
    }

    search = RandomizedSearchCV(
        xgb, param_distributions=param_grid,
        n_iter=5, cv=tscv, scoring='accuracy',
        random_state=42, n_jobs=-1,
    )
    search.fit(X_train_scaled, y_train)
    best_model = search.best_estimator_
    print(f"[TRAIN] Best params: {search.best_params_}")

    reg_model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
    reg_model.fit(X_train_scaled, y_reg_train)

    return best_model, scaler, features, {
        "XGBoost":   best_model,
        "Stacking":  best_model,
        "Regressor": reg_model,
    }

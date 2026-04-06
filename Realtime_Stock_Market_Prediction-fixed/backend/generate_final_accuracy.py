import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
import yfinance as yf
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                             roc_auc_score, confusion_matrix, roc_curve)
from xgboost import XGBClassifier
from sklearn.feature_selection import SelectKBest, f_classif

import warnings
warnings.filterwarnings('ignore')

def get_data_and_split():
    print("Loading Dataset...")
    df = yf.download("AAPL", period="5y", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.reset_index(inplace=True)
    
    # Target definition as per previous steps: 1.002 threshold removes noise
    df['Target'] = (df['Close'].shift(-1) > df['Close'] * 1.002).astype(int)
    
    # Feature Engineering
    close = df['Close']
    df['SMA_10'] = close.rolling(window=10).mean()
    df['SMA_50'] = close.rolling(window=50).mean()
    df['Daily_Return'] = close.pct_change()
    df['Return_1'] = close.pct_change(1)
    df['Return_3'] = close.pct_change(3)
    df['Volatility'] = df['Daily_Return'].rolling(window=20).std()
    
    df.dropna(inplace=True)
    
    # Outliers 
    Q1 = df['Daily_Return'].quantile(0.25)
    Q3 = df['Daily_Return'].quantile(0.75)
    IQR = Q3 - Q1
    df = df[(df['Daily_Return'] >= (Q1 - 1.5 * IQR)) & (df['Daily_Return'] <= (Q3 + 1.5 * IQR))]
    
    all_features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_10', 'SMA_50', 
                    'Daily_Return', 'Return_1', 'Return_3', 'Volatility']
    
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(df.median(numeric_only=True), inplace=True)
    
    X = df[all_features]
    y = df['Target']
    
    # Sequential Split
    split_idx = int(len(X) * 0.8)
    X_train_full = X.iloc[:split_idx]
    y_train_full = y.iloc[:split_idx]
    
    # Feature selection on training slice
    selector = SelectKBest(score_func=f_classif, k=7)
    selector.fit(X_train_full, y_train_full)
    
    selected_mask = selector.get_support()
    features = np.array(all_features)[selected_mask].tolist()
    
    X_selected = X[features]
    
    # Time-series split (Sequential, shuffle=False)
    X_train, X_test, y_train, y_test = train_test_split(X_selected, y, test_size=0.20, shuffle=False)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, y_train, y_test, features, scaler, y, X_selected.columns

def train_or_load_model(X_train_scaled, y_train):
    model_path = "trained_model_final.pkl"
    if not os.path.exists(model_path):
        print("Training model...")
        xgb = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, eval_metric='logloss')
        xgb.fit(X_train_scaled, y_train)
        joblib.dump(xgb, model_path)
    print("Loading Trained Model...")
    return joblib.load(model_path)

def main():
    X_train_scaled, X_test_scaled, y_train, y_test, feature_names, scaler, y_all, col_names = get_data_and_split()
    
    model = train_or_load_model(X_train_scaled, y_train)
    
    print("Generating Predictions...")
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:,1] if hasattr(model, 'predict_proba') else None
    
    print("Calculating Accuracy Metrics...")
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_prob) if y_prob is not None else "N/A"
    
    cm = confusion_matrix(y_test, y_pred)
    
    print("Generating Confusion Matrix Heatmap...")
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Down', 'Up'], yticklabels=['Down', 'Up'])
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig('report_confusion_matrix_final.png')
    plt.close()
    
    print("Generating ROC Curve...")
    if y_prob is not None:
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        plt.figure(figsize=(6, 4))
        plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic')
        plt.legend(loc="lower right")
        plt.tight_layout()
        plt.savefig('report_roc_curve_final.png')
        plt.close()
        
    print("Generating Feature Importance...")
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        plt.figure(figsize=(8, 5))
        sns.barplot(x=importances, y=list(col_names))
        plt.title('Feature Importance')
        plt.tight_layout()
        plt.savefig('report_feature_importance_final.png')
        plt.close()
    
    print("Cross Validation Accuracy...")
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=tscv, scoring='accuracy')
    cv_mean = cv_scores.mean()
    cv_std = cv_scores.std()
    
    print("Calculating Final Predicted Score...")
    final_score = (0.40 * acc) + (0.20 * prec) + (0.20 * rec) + (0.20 * f1)
    
    report = f"""# Final Model Accuracy Report

## 1. Model Information
- **Model Name**: {type(model).__name__}
- **Dataset Size**: {len(y_all)} total samples (Test Size: {len(y_test)})

## 2. Evaluation Metrics
- **Accuracy**:  `{acc:.4f}`
- **Precision**: `{prec:.4f}`
- **Recall**:    `{rec:.4f}`
- **F1 Score**:  `{f1:.4f}`
- **ROC-AUC**:   `{roc_auc if isinstance(roc_auc, str) else f"{roc_auc:.4f}"}`

## 3. Confusion Matrix
| True \\ Predicted | Down (0) | Up (1) |
|------------------|----------|--------|
| **Down (0)**     | {cm[0][0]}       | {cm[0][1]}      |
| **Up (1)**       | {cm[1][0]}       | {cm[1][1]}      |

*(Visualizations available in generated PNG files)*
![Confusion Matrix](C:/Users/janak/.gemini/antigravity/brain/0517411b-4675-4443-b977-40f30346592d/report_confusion_matrix_final.png)

![ROC Curve](C:/Users/janak/.gemini/antigravity/brain/0517411b-4675-4443-b977-40f30346592d/report_roc_curve_final.png)

![Feature Importance](C:/Users/janak/.gemini/antigravity/brain/0517411b-4675-4443-b977-40f30346592d/report_feature_importance_final.png)

## 4. Cross-Validation Results
- **Mean Accuracy**: `{cv_mean:.4f}`
- **Standard Deviation**: `{cv_std:.4f}`

## 5. Final Predicted Score
**Formula used**: `0.40 * Accuracy + 0.20 * Precision + 0.20 * Recall + 0.20 * F1 Score`
- **Final Predicted Performance Score**: `{final_score * 100:.2f}%`

"""

    report_path = "model_final_accuracy_report.md"
    with open(report_path, "w") as f:
        f.write(report)
        
    print("\n==================================")
    print("       FINAL RESULTS              ")
    print("==================================")
    print(f"Final Model Accuracy: {acc*100:.2f}%")
    print(f"Precision: {prec*100:.2f}%")
    print(f"Recall: {rec*100:.2f}%")
    print(f"F1 Score: {f1*100:.2f}%")
    print(f"ROC-AUC: {roc_auc*100:.2f}%" if not isinstance(roc_auc, str) else f"ROC-AUC: {roc_auc}")
    print(f"\nFinal Predicted Performance Score: {final_score*100:.2f}%")
    print(f"\nLocation of saved report file: {os.path.abspath(report_path)}")

if __name__ == "__main__":
    main()

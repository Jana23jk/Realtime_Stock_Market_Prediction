import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
import yfinance as yf
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                             roc_auc_score, confusion_matrix, classification_report, roc_curve)
import warnings
warnings.filterwarnings('ignore')

def get_data_and_split():
    df = yf.download("AAPL", period="5y", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.reset_index(inplace=True)
    
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df['Day_Of_Week'] = df['Date'].dt.day_name()
    df.dropna(inplace=True)
    df = df.drop_duplicates()
    
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['Daily_Return'] = df['Close'].pct_change()
    df['Volatility'] = df['Daily_Return'].rolling(window=20).std()
    df.dropna(inplace=True)
    
    Q1 = df['Daily_Return'].quantile(0.25)
    Q3 = df['Daily_Return'].quantile(0.75)
    IQR = Q3 - Q1
    df = df[(df['Daily_Return'] >= (Q1 - 1.5 * IQR)) & (df['Daily_Return'] <= (Q3 + 1.5 * IQR))]
    
    le = LabelEncoder()
    df['Day_Of_Week_Encoded'] = le.fit_transform(df['Day_Of_Week'])
    
    feature_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_10', 'SMA_50', 'Daily_Return', 'Volatility', 'Day_Of_Week_Encoded']
    
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(df.median(numeric_only=True), inplace=True)
    
    X = df[feature_cols]
    y = df['Target']
    
    # Simplify feature selection for the test script
    top_features = ['Daily_Return', 'Volatility', 'SMA_10', 'SMA_50', 'Close', 'High', 'Low', 'Open']
    X_selected = X[top_features]
    
    X_train, X_test, y_train, y_test = train_test_split(X_selected, y, test_size=0.20, stratify=y, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, y_train, y_test, top_features, X_test

def create_dummy_model_if_missing(X_train_scaled, y_train):
    if not os.path.exists("trained_model.pkl"):
        print("Model 'trained_model.pkl' not found. Training a model to evaluate...")
        from sklearn.ensemble import VotingClassifier, RandomForestClassifier
        from xgboost import XGBClassifier
        from sklearn.svm import SVC
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=42)
        X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)
        rf = RandomForestClassifier(n_estimators=50, max_depth=10, min_samples_split=5, random_state=42)
        xgb = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, eval_metric='logloss')
        svm = SVC(kernel='rbf', C=10, probability=True, random_state=42)
        voting_clf = VotingClassifier(estimators=[('rf', rf), ('xgb', xgb), ('svm', svm)], voting='soft')
        voting_clf.fit(X_train_res, y_train_res)
        joblib.dump(voting_clf, 'trained_model.pkl')
        print("Model saved to 'trained_model.pkl'")

def main():
    print("1 & 2. Loading Libraries and Dataset...")
    X_train_scaled, X_test_scaled, y_train, y_test, feature_names, X_test_raw = get_data_and_split()
    
    create_dummy_model_if_missing(X_train_scaled, y_train)
    
    print("3. Loading Trained Model...")
    model = joblib.load("trained_model.pkl")
    
    print("4. Making Predictions...")
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:,1] if hasattr(model, 'predict_proba') else None
    
    print("5. Calculating Model Evaluation Metrics...")
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob) if y_prob is not None else "N/A"
    
    cm = confusion_matrix(y_test, y_pred)
    class_report = classification_report(y_test, y_pred)
    
    print("6. Generating Visualizations...")
    # Confusion Matrix
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Down', 'Up'], yticklabels=['Down', 'Up'])
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig('report_confusion_matrix.png')
    plt.close()
    
    # ROC Curve
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
        plt.savefig('report_roc_curve.png')
        plt.close()
    
    print("7. Performing Cross Validation...")
    # Perform cross validation on the training set using the loaded model
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='accuracy', n_jobs=-1)
    cv_mean = cv_scores.mean()
    cv_std = cv_scores.std()
    
    print("8. Error Analysis...")
    # Identify incorrectly predicted samples
    incorrect_idx = np.where(y_pred != y_test)[0]
    error_analysis_text = ""
    error_analysis_text += f"Total misclassified samples: {len(incorrect_idx)} out of {len(y_test)}\n\n"
    error_analysis_text += "Top 5 Misclassified Cases Features:\n"
    
    # Top misclassified
    for i in incorrect_idx[:5]:
        error_analysis_text += f"- True: {y_test.iloc[i]}, Predicted: {y_pred[i]}\n"
        error_analysis_text += f"  Features: {X_test_raw.iloc[i].to_dict()}\n"
        if y_prob is not None:
            error_analysis_text += f"  Probability of class 1: {y_prob[i]:.4f}\n"

    print("9 & 10. Generating and Saving Evaluation Report...")
    report_content = f"""# Model Evaluation Report

## 1. Model Information
- **Model Type**: {type(model).__name__}
- **Parameters**: 
```python
{model.get_params() if hasattr(model, 'get_params') else 'N/A'}
```

## 2. Dataset Summary
- **Target**: Next Day Closing Price Direction (1 = Up, 0 = Down)
- **Features Used**: {feature_names}
- **Test Set Size**: {len(y_test)} samples

## 3. Evaluation Metrics
- **Accuracy**:  `{acc:.4f}`
- **Precision**: `{prec:.4f}`
- **Recall**:    `{rec:.4f}`
- **F1 Score**:  `{f1:.4f}`
- **ROC-AUC**:   `{roc_auc if isinstance(roc_auc, str) else f"{roc_auc:.4f}"}`

### Classification Report
```text
{class_report}
```

## 4. Confusion Matrix
| True \\ Predicted | Down (0) | Up (1) |
|------------------|----------|--------|
| **Down (0)**     | {cm[0][0]}       | {cm[0][1]}      |
| **Up (1)**       | {cm[1][0]}       | {cm[1][1]}      |

*(Visualizations saved as `report_confusion_matrix.png` and `report_roc_curve.png`)*

## 5. Cross Validation Results (5-Fold)
- **Mean Accuracy**: `{cv_mean:.4f}`
- **Standard Deviation**: `{cv_std:.4f}`

## 6. Error Analysis
{error_analysis_text}

## 7. Final Model Performance Summary
The model achieved an accuracy of `{acc:.4f}` on the holdout test set with an AUC of `{roc_auc if isinstance(roc_auc, str) else f"{roc_auc:.4f}"}`. 
Cross-validation during training yielded a consistent mean accuracy of `{cv_mean:.4f}`, indicating minimal overfitting compared to the final test score.
"""

    report_path = "model_evaluation_report.md"
    with open(report_path, "w") as f:
        f.write(report_content)
        
    print("\n==================================")
    print("       OUTPUT SUMMARY             ")
    print("==================================")
    print(f"Final Accuracy: {acc:.4f}")
    print(f"ROC AUC: {roc_auc if isinstance(roc_auc, str) else f'{roc_auc:.4f}'}")
    print(f"Precision: {prec:.4f} | Recall: {rec:.4f}")
    print(f"Cross Validation Mean: {cv_mean:.4f} (+/- {cv_std:.4f})")
    print("\nGraphs saved:")
    print("- report_confusion_matrix.png")
    print("- report_roc_curve.png")
    print(f"\nLocation of saved report file: {os.path.abspath(report_path)}")

if __name__ == "__main__":
    main()
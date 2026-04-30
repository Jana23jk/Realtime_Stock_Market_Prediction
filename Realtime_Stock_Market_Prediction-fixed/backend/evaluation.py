from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score
import pandas as pd
import numpy as np

def evaluate_model(model, X_test, y_test):
    """
    Evaluates model performance and returns metrics.
    """
    preds = model.predict(X_test)
    
    # Probabilities for ROC AUC
    if hasattr(model, 'predict_proba'):
        probs = model.predict_proba(X_test)[:, 1]
        roc_auc = roc_auc_score(y_test, probs)
    else:
        roc_auc = "N/A"
        
    metrics = {
        "Accuracy": accuracy_score(y_test, preds),
        "Precision": precision_score(y_test, preds, zero_division=0),
        "Recall": recall_score(y_test, preds, zero_division=0),
        "F1_score": f1_score(y_test, preds, zero_division=0),
        "ROC_AUC": roc_auc
    }
    
    cm = confusion_matrix(y_test, preds).tolist()
    return metrics, cm

def get_feature_importances(model, feature_names):
    """
    Returns sorted list of feature importances if applicable.
    """
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        sorted_indices = np.argsort(importances)[::-1]
        
        feature_impact = []
        for i in sorted_indices:
            feature_impact.append({
                "feature": feature_names[i],
                "importance": float(importances[i])
            })
        return feature_impact
    return []
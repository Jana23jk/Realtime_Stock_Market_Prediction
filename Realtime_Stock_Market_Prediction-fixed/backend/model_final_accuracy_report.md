# Final Model Accuracy Report

## 1. Model Information
- **Model Name**: XGBClassifier
- **Dataset Size**: 1140 total samples (Test Size: 228)

## 2. Evaluation Metrics
- **Accuracy**:  `0.5395`
- **Precision**: `0.5079`
- **Recall**:    `0.3019`
- **F1 Score**:  `0.3787`
- **ROC-AUC**:   `0.5385`

## 3. Confusion Matrix
| True \ Predicted | Down (0) | Up (1) |
|------------------|----------|--------|
| **Down (0)**     | 91       | 31      |
| **Up (1)**       | 74       | 32      |

*(Visualizations available in generated PNG files)*
![Confusion Matrix](C:/Users/janak/.gemini/antigravity/brain/0517411b-4675-4443-b977-40f30346592d/report_confusion_matrix_final.png)

![ROC Curve](C:/Users/janak/.gemini/antigravity/brain/0517411b-4675-4443-b977-40f30346592d/report_roc_curve_final.png)

![Feature Importance](C:/Users/janak/.gemini/antigravity/brain/0517411b-4675-4443-b977-40f30346592d/report_feature_importance_final.png)

## 4. Cross-Validation Results
- **Mean Accuracy**: `0.5132`
- **Standard Deviation**: `0.0504`

## 5. Final Predicted Score
**Formula used**: `0.40 * Accuracy + 0.20 * Precision + 0.20 * Recall + 0.20 * F1 Score`
- **Final Predicted Performance Score**: `45.35%`


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score, roc_curve
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings('ignore')

def load_data():
    print("1. Loading dataset...")
    # Fetch real stock data as our dataset
    df = yf.download("AAPL", period="5y", progress=False)
    # Flatten multiindex if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.reset_index(inplace=True)
    return df

def preprocess_data(df):
    print("2. Preprocessing Data...")
    
    # Create target: 1 if next day's close > today's close, else 0
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    
    # Add dummy categorical variable to demonstrate Encoding Instruction
    df['Day_Of_Week'] = df['Date'].dt.day_name()
    
    # Handle missing values
    df.dropna(inplace=True)
    
    # Remove duplicate records
    df = df.drop_duplicates()
    
    # Feature Engineering before Outliers to keep features aligned
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['Daily_Return'] = df['Close'].pct_change()
    df['Volatility'] = df['Daily_Return'].rolling(window=20).std()
    
    # Drop rows with NaN from rolling calculations
    df.dropna(inplace=True)
    
    # Detect and remove outliers using IQR (on Daily_Return)
    Q1 = df['Daily_Return'].quantile(0.25)
    Q3 = df['Daily_Return'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    df = df[(df['Daily_Return'] >= lower_bound) & (df['Daily_Return'] <= upper_bound)]
    
    # Encode categorical variable
    le = LabelEncoder()
    df['Day_Of_Week_Encoded'] = le.fit_transform(df['Day_Of_Week'])
    
    # Feature columns set
    feature_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_10', 'SMA_50', 'Daily_Return', 'Volatility', 'Day_Of_Week_Encoded']
    
    # Ensure there are no infs or NaNs left before saving
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(df.median(numeric_only=True), inplace=True) # Median imputation
    
    X = df[feature_cols]
    y = df['Target']
    
    return X, y, feature_cols

def feature_selection(X, y, feature_cols):
    print("3. Feature Selection...")
    # SelectKBest using chi-square/f_classif
    selector = SelectKBest(score_func=f_classif, k='all') 
    selector.fit(X, y)
    
    scores = pd.DataFrame({'Feature': feature_cols, 'Score': selector.scores_})
    scores = scores.sort_values(by='Score', ascending=False)
    print("Feature Scores:\n", scores.head(10))
    
    # Drop low importance: let's select top features dynamically
    top_features = scores['Feature'].head(8).tolist()
    X_selected = X[top_features]
    print(f"Selected Top Features: {top_features}")
    return X_selected, top_features

def main():
    print("--- Starting Advanced ML Pipeline ---")
    
    # 1. Load Data
    df = load_data()
    
    # 2. Preprocess & Feature Engineering
    X, y, features = preprocess_data(df)
    
    # Feature Selection (Drop low importance)
    X_selected, selected_features = feature_selection(X, y, features)
    
    # 3. Train Test Split
    print("4. Train-Test Split (80/20 & Stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(X_selected, y, test_size=0.20, stratify=y, random_state=42)
    
    # 4. Normalization
    print("5. Normalizing Numerical Features (StandardScaler)...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 8. Optimization (SMOTE to fix class imbalance)
    print("6. Applying SMOTE for class imbalance optimization...")
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)
    
    # 5. Model Selection & Hyperparameter Tuning
    print("7. Model Selection & Hyperparameter Tuning (Grid/Randomized Search, 5-Fold CV)...")
    
    # Defining models
    models = {
        'Logistic Regression': LogisticRegression(random_state=42),
        'Random Forest': RandomForestClassifier(random_state=42),
        'XGBoost': XGBClassifier(random_state=42, eval_metric='logloss'),
        'SVM': SVC(probability=True, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(random_state=42)
    }
    
    # Defining hyperparameter grids for tuning
    param_grids = {
        'Logistic Regression': {'C': [0.1, 1, 10]},
        'Random Forest': {'n_estimators': [50, 100], 'max_depth': [5, 10], 'min_samples_split': [2, 5]},
        'XGBoost': {'n_estimators': [50, 100], 'max_depth': [3, 5], 'learning_rate': [0.01, 0.1]},
        'SVM': {'C': [0.1, 1, 10], 'kernel': ['rbf']},
        'Gradient Boosting': {'n_estimators': [50, 100], 'learning_rate': [0.01], 'max_depth': [3, 5]}
    }
    
    best_estimators = {}
    for name, model in models.items():
        print(f" --> Tuning {name}...")
        # Reduce iterations slightly for speed but maintain exact requirements
        search = RandomizedSearchCV(model, param_grids[name], n_iter=3, cv=5, scoring='accuracy', random_state=42, n_jobs=-1)
        search.fit(X_train_res, y_train_res)
        best_estimators[name] = search.best_estimator_
        print(f"     Best params: {search.best_params_}")
    
    # 6. Ensemble Technique
    print("8. Training Ensemble (Soft Voting Classifier)...")
    voting_clf = VotingClassifier(
        estimators=[
            ('rf', best_estimators['Random Forest']),
            ('xgb', best_estimators['XGBoost']),
            ('svm', best_estimators['SVM'])
        ],
        voting='soft'
    )
    voting_clf.fit(X_train_res, y_train_res)
    
    # 7. Model Evaluation
    print("9. Evaluating Final Model...")
    y_pred = voting_clf.predict(X_test_scaled)
    y_prob = voting_clf.predict_proba(X_test_scaled)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)
    
    # 9. Output printing
    print("\n==============================")
    print("       FINAL RESULTS          ")
    print("==============================")
    print(f"Best Ensemble Model: Voting Classifier (Random Forest + XGBoost + SVM)")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Generate Feature Importance Chart
    print("\n10. Generating Feature Importance Chart...")
    # Use XGBoost model component inside Voting for importances
    xgb_model = best_estimators['XGBoost']
    importances = xgb_model.feature_importances_
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x=importances, y=selected_features, hue=selected_features, palette="viridis", legend=False)
    plt.title("Feature Importance (XGBoost Component)")
    plt.xlabel("Importance Score")
    plt.ylabel("Features")
    plt.tight_layout()
    plt.savefig("feature_importance_chart.png")
    print("Saved 'feature_importance_chart.png' to local directory.")

if __name__ == "__main__":
    main()

import pytest
import pandas as pd
import numpy as np
from feature_engineering import create_features
from model_training import train_and_select_model
from evaluation import evaluate_model
from xgboost import XGBClassifier

# --- Fixtures ---
@pytest.fixture
def sample_stock_data():
    dates = pd.date_range(start="2020-01-01", periods=200)
    
    # Oscillating price to ensure Target contains both 0 and 1 in early TimeSeriesSplit folds
    x = np.linspace(0, 50, 200)
    close_prices = 150 + x + np.sin(x) * 10
    
    data = {
        'Open': close_prices - 2,
        'High': close_prices + 5,
        'Low': close_prices - 5,
        'Close': close_prices,
        'Volume': np.random.randint(1000, 10000, 200)
    }
    df = pd.DataFrame(data, index=dates)
    return df

@pytest.fixture
def sample_external_factors():
    dates = pd.date_range(start="2020-01-01", periods=200)
    data = {
        'Market_Index': np.random.uniform(3000, 4000, 200),
        'USD_INR': np.random.uniform(70, 85, 200),
        'Gold': np.random.uniform(1500, 2000, 200),
        'Crude_Oil': np.random.uniform(50, 100, 200)
    }
    df = pd.DataFrame(data, index=dates)
    return df

# --- 1. Black Box Testing ---

def test_prediction_binary_output(sample_stock_data, sample_external_factors):
    """Ensure output is binary (0 or 1) and validate predictions using sample input data."""
    df_features = create_features(sample_stock_data, sample_external_factors)
    best_model, scaler, feature_names, models_dict = train_and_select_model(df_features)
    
    sample_input = df_features[feature_names].iloc[-1:]
    scaled_input = scaler.transform(sample_input)
    prediction = best_model.predict(scaled_input)[0]
    
    assert prediction in [0, 1], "Prediction should be binary (0 or 1)"

def test_missing_values(sample_stock_data):
    """Test missing values handling."""
    sample_stock_data.loc[sample_stock_data.index[5], 'Close'] = np.nan
    df_features = create_features(sample_stock_data)
    
    assert not df_features.isnull().values.any(), "Missing values should be handled (dropped or filled)"

def test_extreme_stock_values():
    """Test extreme stock values."""
    dates = pd.date_range(start="2020-01-01", periods=200)
    
    # Needs to oscillate to pass XGBoost class requirement during splits
    x = np.linspace(0, 50, 200)
    base = 1e6
    close_prices = base + np.sin(x) * 1e4
    
    extreme_data = pd.DataFrame({
        'Open': close_prices - 1e3,
        'High': close_prices + 1e4,
        'Low': close_prices - 1e4,
        'Close': close_prices,
        'Volume': np.random.randint(1000, 1e9, 200)
    }, index=dates)
    
    df_features = create_features(extreme_data)
    best_model, scaler, feature_names, _ = train_and_select_model(df_features)
    
    sample_input = df_features[feature_names].iloc[-1:]
    scaled_input = scaler.transform(sample_input)
    prediction = best_model.predict(scaled_input)[0]
    
    assert prediction in [0, 1], "Model should handle extreme values and output binary prediction"

# --- 2. White Box Testing ---

def test_verify_feature_engineering(sample_stock_data):
    """Verify feature engineering functions and dataset preprocessing."""
    df_features = create_features(sample_stock_data)
    
    expected_technical_indicators = ['SMA_10', 'RSI_14', 'MACD', 'Target']
    for indicator in expected_technical_indicators:
        assert indicator in df_features.columns, f"Feature {indicator} is missing from engineered features"

def test_verify_model_training_pipeline(sample_stock_data):
    """Verify model training pipeline."""
    df_features = create_features(sample_stock_data)
    best_model, scaler, feature_names, models_dict = train_and_select_model(df_features)
    
    assert isinstance(best_model, XGBClassifier), "Model should be XGBClassifier instance"
    assert hasattr(scaler, 'transform'), "Scaler should have a transform method"
    assert len(feature_names) <= 10, "SelectKBest should limit to 10 features"

def test_probability_output_format(sample_stock_data):
    """Verify probability output format."""
    df_features = create_features(sample_stock_data)
    best_model, scaler, feature_names, _ = train_and_select_model(df_features)
    
    sample_input = df_features[feature_names].iloc[-5:]
    scaled_input = scaler.transform(sample_input)
    prob_output = best_model.predict_proba(scaled_input)
    
    assert prob_output.shape == (5, 2), "Probability output should have shape (n_samples, 2)"
    assert np.all((prob_output >= 0) & (prob_output <= 1)), "Probabilities should be between 0 and 1"

# --- 3. Performance Testing ---

def test_calculate_accuracy():
    """Calculate accuracy and ensure accuracy is structurally viable."""
    dates = pd.date_range(start="2020-01-01", periods=200)
    
    # Generate an oscillating trend with an upward bias so we get 0s and 1s safely
    x = np.linspace(0, 50, 200)
    close_prices = 100 + x + np.sin(x) * 10
    
    data = pd.DataFrame({
        'Open': close_prices - 1,
        'High': close_prices + 5,
        'Low': close_prices - 5,
        'Close': close_prices,
        'Volume': np.random.randint(1000, 10000, 200)
    }, index=dates)
    
    df_features = create_features(data)
    model, scaler, feature_names, _ = train_and_select_model(df_features)
    
    X = df_features[feature_names]
    y = df_features['Target']
    split_idx = int(len(X) * 0.8)
    X_test, y_test = X.iloc[split_idx:], y.iloc[split_idx:]
    
    X_test_scaled = scaler.transform(X_test)
    metrics, _ = evaluate_model(model, X_test_scaled, y_test)
    
    assert 'Accuracy' in metrics
    assert metrics['Accuracy'] > 0.50, f"Accuracy {metrics['Accuracy']} should be greater than 50% on simple trend"

# --- 4. Stress Testing ---

def test_prediction_large_datasets():
    """Test prediction with large datasets."""
    dates = pd.date_range(start="2000-01-01", periods=5000)
    data = pd.DataFrame({
        'Open': np.random.uniform(10, 500, 5000),
        'High': np.random.uniform(20, 520, 5000),
        'Low': np.random.uniform(5, 490, 5000),
        'Close': np.random.uniform(10, 500, 5000),
        'Volume': np.random.randint(1000, 1000000, 5000)
    }, index=dates)
    
    df_features = create_features(data)
    model, scaler, feature_names, _ = train_and_select_model(df_features)
    
    sample_input = df_features[feature_names].iloc[-1000:]
    scaled_input = scaler.transform(sample_input)
    predictions = model.predict(scaled_input)
    
    assert len(predictions) == 1000, "Should generate predictions for 1000 extreme samples efficiently"

# --- 5. Error Handling ---

def test_invalid_input_format():
    """Ensure invalid input raises proper errors."""
    invalid_data = pd.DataFrame({
        'Random_Col_1': [100, 101],
        'Random_Col_2': [102, 103]
    })
    
    with pytest.raises(KeyError):
        # Missing 'Close' and other critical stock OHLC columns
        create_features(invalid_data)

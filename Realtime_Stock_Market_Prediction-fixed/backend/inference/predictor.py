import numpy as np


def predict_price(model, scaler, df, window: int):
    """
    Predict next price from an LSTM-style model.
    FIX: StandardScaler does NOT have .data_min_ / .data_max_ attributes.
         Use inverse_transform to convert scaled predictions back to price space.
    FIX: Graceful error if DataFrame doesn't have required columns.
    """
    required_cols = ['Close', 'RSI_14', 'EMA_20', 'MACD']
    available = [c for c in required_cols if c in df.columns]

    if len(available) < len(required_cols):
        raise ValueError(
            f"predict_price: missing columns {set(required_cols) - set(available)}. "
            f"Available: {list(df.columns)}"
        )

    features = df[required_cols].values

    # Scale using the fitted scaler
    scaled = scaler.transform(features)

    if len(scaled) < window:
        raise ValueError(
            f"Not enough rows for window={window}. Got {len(scaled)} rows."
        )

    last        = scaled[-window:].reshape(1, window, len(required_cols))
    scaled_pred = float(model.predict(last)[0][0])

    # FIX: Inverse-transform a dummy row to get real price scale.
    # We put the prediction in the first column position (Close) and zeros elsewhere.
    dummy_row              = np.zeros((1, len(required_cols)))
    dummy_row[0, 0]        = scaled_pred
    unscaled               = scaler.inverse_transform(dummy_row)
    predicted_price        = float(unscaled[0, 0])

    return predicted_price

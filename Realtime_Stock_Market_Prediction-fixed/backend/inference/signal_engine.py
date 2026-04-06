def get_signal(current, predicted):
    diff = (predicted - current) / current

    if diff > 0.01:
        return "BUY"
    elif diff < -0.01:
        return "SELL"
    else:
        return "HOLD"

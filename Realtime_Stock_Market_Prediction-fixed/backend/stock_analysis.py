import pandas as pd
import numpy as np
from textblob import TextBlob
import random

def get_news_headlines(ticker):
    """
    Mock function to fetch news headlines.
    """
    # Sample headlines for demonstration
    headlines = [
        f"{ticker} reports quarterly revenue growth, beating expectations.",
        f"Investors optimistic about {ticker}'s new product line.",
        f"Supply chain evaluations continue for {ticker}.",
        f"Global market trends show mixed signals for {ticker} sector.",
        f"Analysts maintain buy rating for {ticker} despite volatility."
    ]
    return headlines

def get_external_factors():
    """
    Mock function to load external factors with percentage changes.
    """
    return {
        "Market Index": random.uniform(-2.5, 2.5),  # Market change %
        "Oil Price": random.uniform(-4.0, 4.0),     # Oil price change %
        "Currency": random.uniform(-1.5, 1.5),      # Currency exchange change %
        "Interest Rate": random.uniform(-0.5, 0.5)  # Interest rate change %
    }

def analyze_sentiment(headlines):
    """
    Analyze sentiment of headlines using TextBlob and Pandas.
    Returns average sentiment score (-1 to 1).
    """
    if not headlines:
        return 0.0
        
    df = pd.DataFrame(headlines, columns=["Headline"])
    
    # Apply sentiment analysis
    df["Sentiment"] = df["Headline"].apply(lambda h: TextBlob(h).sentiment.polarity)
    
    # Calculate average
    avg_score = df["Sentiment"].mean()
    
    return avg_score

def sentiment_label(score):
    if score >= 0.3: return "Positive"
    if score <= -0.3: return "Negative"
    return "Neutral"

def normalize(value, min_val, max_val, reverse=False):
    """
    Normalize value to 0-1 scale.
    If reverse is True, lower values are better (1.0).
    """
    # Clamp value
    clamped = max(min_val, min(value, max_val))
    norm = (clamped - min_val) / (max_val - min_val)
    
    if reverse:
        return 1.0 - norm
    return norm

def get_market_context():
    """
    Simulates advanced market metrics for dynamic weighting.
    """
    return {
        "Volatility": random.uniform(0.1, 0.9),          # 0.1 (Stable) to 0.9 (Chaos)
        "Sentiment_Accuracy": random.uniform(0.4, 0.9),  # Hist. Accuracy of Sentiment Model
        "External_Accuracy": random.uniform(0.5, 0.85)   # Hist. Accuracy of External Model
    }

def calculate_dynamic_alpha(sentiment_score, external_score, context):
    """
    Computes dynamic alpha (Sentiment Weight) based on master rules.
    """
    # 1. Signal Strength Adjustment
    # |S| / (|S| + |E|)
    abs_s = abs(sentiment_score)
    abs_e = abs(external_score) 
    
    # Failsafe for weak signals
    if abs_s < 0.05 and abs_e < 0.05:
        return 0.35, "Default (Weak Signals)"
        
    denominator = abs_s + abs_e
    signal_strength = abs_s / denominator if denominator > 0 else 0.5

    # 2. Volatility Adjustment
    # High Vol -> Increase External (Lower Alpha)
    # Low Vol -> Increase Sentiment (Higher Alpha)
    # We map Volatility (0-1) to an adjustment factor (1-0).
    vol_adj = 1.0 - context["Volatility"]

    # 3. Performance Factor
    # Relative accuracy of sentiment vs external
    total_acc = context["Sentiment_Accuracy"] + context["External_Accuracy"]
    perf_factor = context["Sentiment_Accuracy"] / total_acc if total_acc > 0 else 0.5

    # 4. Final Computation
    # alpha = 0.4 * Signal + 0.3 * Performance + 0.3 * Volatility
    raw_alpha = (0.4 * signal_strength) + (0.3 * perf_factor) + (0.3 * vol_adj)

    # 5. Stability Constraint & Normalization
    # Clamp between 0.1 and 0.9
    alpha = max(0.1, min(raw_alpha, 0.9))
    
    # Analyze Reason
    reasons = []
    if signal_strength > 0.6: reasons.append("Strong Sentiment")
    if vol_adj < 0.4: reasons.append("High Volatility") # High vol means low adj
    if alpha < 0.4: reasons.append("Macro Dominance")
    if not reasons: reasons.append("Balanced Market")
    
    return alpha, reasons[0]

def calculate_impact_score(headlines, factors):
    """
    Core logic to calculate final impact score using Dynamic Weighting.
    """
    # 1. Sentiment Score
    avg_sentiment = analyze_sentiment(headlines)

    # 2. External Score
    # Normalization Rules
    n_market = normalize(factors["Market Index"], -3, 3, reverse=False)
    n_oil = normalize(factors["Oil Price"], -5, 5, reverse=True)
    n_curr = normalize(factors["Currency"], -2, 2, reverse=True)
    n_rate = normalize(factors["Interest Rate"], -1, 1, reverse=True)
    
    external_score = np.mean([n_market, n_oil, n_curr, n_rate])

    # 3. Dynamic Weighting
    context = get_market_context()
    alpha, reason = calculate_dynamic_alpha(avg_sentiment, external_score, context)
    weight_ext = 1.0 - alpha

    # 4. Final Calculation
    final_score = (alpha * avg_sentiment) + (weight_ext * external_score)
    
    return avg_sentiment, external_score, final_score, alpha, weight_ext, reason

def main():
    print("--- Dynamic Adaptive Weighting Engine ---")
    ticker = input("Enter Stock Ticker (e.g., TSLA): ").strip().upper()
    if not ticker: ticker = "TSLA"
    
    print(f"\n[Processing Incoming Data Stream for {ticker}...]")
    headlines = get_news_headlines(ticker)
    factors = get_external_factors()
    
    # Calculate
    s_score, e_score, final, w_sent, w_ext, reason = calculate_impact_score(headlines, factors)

    # STRICT OUTPUT FORMAT
    print("\nDynamic Weight Result")
    print(f"Sentiment Weight (α_t): {w_sent:.4f}")
    print(f"External Weight (1-α_t): {w_ext:.4f}")
    print(f"Reason Category: {reason}")
    print("\nFinal Score")
    print(f"Final_t = {final:.4f}")

if __name__ == "__main__":
    main()

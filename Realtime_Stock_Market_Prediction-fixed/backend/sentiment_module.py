import yfinance as yf
import nltk


class SentimentAnalyzer:
    def __init__(self):
        # FIX: Download vader_lexicon on startup, silently
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon', quiet=True)

        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        self.vader = SentimentIntensityAnalyzer()

    def get_todays_sentiment(self, ticker: str) -> dict:
        """
        Fetches latest news for a ticker and calculates sentiment metrics.
        FIX: Handles both old and new yfinance news formats.
        FIX: Returns safe defaults on any error.
        """
        _default = {"Sentiment_Score": 0.0, "Pos_Neg_Ratio": 1.0, "News_Count": 0}

        try:
            t    = yf.Ticker(ticker)
            news = t.news or []
        except Exception:
            return _default

        if not news:
            return _default

        scores    = []
        pos_count = 0
        neg_count = 0

        for item in news:
            # FIX: Handle both old format {title:...} and new format {content:{title:...}}
            content = item.get('content', {}) if isinstance(item.get('content'), dict) else {}
            title   = content.get('title') or item.get('title', '')
            if not title:
                continue

            score = self.vader.polarity_scores(str(title))['compound']
            scores.append(score)

            if score > 0.05:
                pos_count += 1
            elif score < -0.05:
                neg_count += 1

        count = len(scores)
        if count == 0:
            return _default

        avg_score = sum(scores) / count

        # FIX: Avoid zero-division in ratio
        if neg_count > 0:
            ratio = pos_count / neg_count
        elif pos_count > 0:
            ratio = float(pos_count)
        else:
            ratio = 1.0

        return {
            "Sentiment_Score": round(avg_score, 4),
            "Pos_Neg_Ratio":   round(ratio, 4),
            "News_Count":      count,
        }

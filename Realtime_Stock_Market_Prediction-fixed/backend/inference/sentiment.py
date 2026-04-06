from nltk.sentiment.vader import SentimentIntensityAnalyzer
import yfinance as yf

class MarketSentiment:
    def __init__(self):
        try:
            self.vader = SentimentIntensityAnalyzer()
        except:
            import nltk
            nltk.download('vader_lexicon')
            self.vader = SentimentIntensityAnalyzer()

    def get_stock_sentiment(self, symbol):
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return {"score": 0, "label": "Neutral", "summary": "No recent news found."}

            sentiment_score = 0
            count = 0
            
            headlines = []

            for item in news[:5]: # Analyze top 5 recent news
                # Handle nested content structure (yfinance new format)
                content = item.get('content', {})
                title = content.get('title') or item.get('title', '')
                
                if not title: continue
                
                # VADER Score
                vader_score = self.vader.polarity_scores(title)['compound']
                
                # Financial Keyword Correction
                # VADER often misses financial context (e.g., "correction" is neutral/positive in bad English, negative in finance)
                title_lower = title.lower()
                bearish_words = ['drop', 'fall', 'down', 'loss', 'lower', 'bear', 'bearish', 'weak', 'dip', 'plunge', 'tumble', 'miss', 'concern', 'risk', 'uncertain', 'correction', 'crash']
                bullish_words = ['rise', 'jump', 'gain', 'up', 'high', 'bull', 'bullish', 'strong', 'surge', 'soar', 'beat', 'growth', 'positive', 'rally']
                
                keyword_score = 0
                for w in bearish_words:
                    if w in title_lower:
                        keyword_score -= 0.2
                for w in bullish_words:
                    if w in title_lower:
                        keyword_score += 0.2
                
                # Combined Score (weighted average or simple sum)
                final_item_score = (vader_score + keyword_score)
                # Clamp between -1 and 1
                final_item_score = max(min(final_item_score, 1.0), -1.0)
                
                sentiment_score += final_item_score
                count += 1
                headlines.append({"title": title, "score": final_item_score})

            if count == 0:
                return {"score": 0, "label": "Neutral", "summary": "No scorable news found."}

            avg_score = sentiment_score / count
            
            # Widen the neutral threshold to account for noise
            if avg_score >= 0.1:
                label = "Bullish"
            elif avg_score <= -0.1:
                label = "Bearish"
            else:
                label = "Neutral"

            return {
                "score": round(avg_score, 2),
                "label": label,
                "news_count": count,
                "headline_analysis": headlines
            }

        except Exception as e:
            return {"error": str(e)}

    def analyze_economy(self, market="US"):
        # Proxy for economy: Major Indices News
        symbol = "^GSPC" if market == "US" else "^BSESN"
        return self.get_stock_sentiment(symbol)

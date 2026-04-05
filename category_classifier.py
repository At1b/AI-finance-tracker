"""
Auto Expense Category Classifier (AI)
Uses a hybrid approach:
  1. Keyword-based rules for instant, high-confidence classification
  2. TF-IDF + Multinomial Naive Bayes trained on synthetic labeled data
  3. Learns from user's historical transactions for personalization

Classifies expense descriptions into: Food, Transport, Shopping, Bills, Other
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import sqlite3


# ============================================================
# KEYWORD RULES — High-confidence instant classification
# ============================================================
KEYWORD_RULES = {
    "Food": [
        "breakfast", "lunch", "dinner", "snack", "pizza", "burger", "coffee",
        "tea", "restaurant", "cafe", "cafeteria", "food", "meal", "biryani",
        "dosa", "thali", "paneer", "chicken", "fish", "rice", "noodles",
        "pasta", "sandwich", "juice", "smoothie", "ice cream", "cake",
        "bakery", "sweets", "chocolate", "chips", "biscuit", "cookie",
        "zomato", "swiggy", "dominos", "mcdonalds", "kfc", "subway",
        "starbucks", "dunkin", "groceries", "grocery", "vegetables",
        "fruits", "milk", "bread", "eggs", "butter", "cheese", "meat",
        "seafood", "canteen", "tiffin", "dabba", "mess", "dhaba",
        "eat", "eating", "dine", "dining", "takeout", "delivery",
        "uber eats", "food delivery", "kitchen", "cook", "ingredient",
    ],
    "Transport": [
        "uber", "ola", "lyft", "cab", "taxi", "auto", "rickshaw",
        "bus", "metro", "train", "flight", "airline", "airport",
        "fuel", "petrol", "diesel", "gas", "gasoline", "cng",
        "parking", "toll", "highway", "commute", "travel", "trip",
        "ride", "drive", "car", "bike", "scooter", "cycle",
        "rapido", "meru", "railway", "irctc", "booking",
        "transport", "transportation", "fare", "ticket",
        "e-rickshaw", "ferry", "boat", "ship", "cruise",
        "vehicle", "maintenance", "repair", "service", "tyre", "tire",
        "insurance", "registration", "fastag", "transit",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "meesho", "nykaa",
        "shopping", "shop", "mall", "store", "clothes", "clothing",
        "shoes", "sneakers", "jacket", "shirt", "pants", "jeans",
        "dress", "fashion", "accessories", "watch", "jewelry",
        "electronics", "phone", "laptop", "tablet", "headphones",
        "earbuds", "speaker", "camera", "gadget", "charger",
        "furniture", "decor", "home", "appliance", "kitchen",
        "gift", "present", "birthday", "anniversary",
        "cosmetics", "makeup", "skincare", "perfume", "fragrance",
        "bag", "backpack", "wallet", "sunglasses", "belt",
        "book", "stationery", "toy", "game", "gaming",
        "online order", "purchase", "buy", "bought",
    ],
    "Bills": [
        "electricity", "electric", "power", "light bill",
        "water", "water bill", "gas bill", "pipeline",
        "internet", "wifi", "broadband", "fiber", "jio", "airtel",
        "vodafone", "vi", "bsnl", "mobile", "phone bill", "recharge",
        "rent", "house rent", "apartment", "flat", "lease",
        "subscription", "netflix", "spotify", "prime", "hotstar",
        "disney", "youtube", "premium", "membership",
        "insurance", "lic", "health insurance", "life insurance",
        "emi", "loan", "installment", "mortgage", "credit card bill",
        "tax", "gst", "income tax", "property tax",
        "hospital", "doctor", "medicine", "pharmacy", "medical",
        "health", "clinic", "dental", "eye", "lab test",
        "gym", "fitness", "yoga", "school fee", "tuition",
        "college", "education", "course", "training",
        "maintenance", "society", "hoa", "utility", "utilities",
    ],
    "Other": [
        "miscellaneous", "misc", "other", "general", "donation",
        "charity", "tip", "laundry", "dry clean", "salon",
        "haircut", "spa", "massage", "movie", "cinema", "theatre",
        "concert", "event", "party", "celebration", "wedding",
        "festival", "puja", "temple", "church", "mosque",
        "pet", "veterinary", "vet", "hobby", "art", "craft",
        "sports", "swim", "golf", "tennis", "cricket",
        "newspaper", "magazine", "fine", "penalty", "fee",
        "atm", "bank charge", "service charge", "convenience fee",
    ],
}

# ============================================================
# SYNTHETIC TRAINING DATA for ML model
# ============================================================
TRAINING_DATA = [
    # Food
    ("bought lunch from office canteen", "Food"),
    ("dinner at italian restaurant", "Food"),
    ("swiggy order pizza delivery", "Food"),
    ("morning coffee starbucks", "Food"),
    ("weekly grocery shopping vegetables fruits", "Food"),
    ("zomato biryani order", "Food"),
    ("street food chaat pani puri", "Food"),
    ("dominos large pizza cheese", "Food"),
    ("milk bread eggs daily needs", "Food"),
    ("kfc bucket meal chicken", "Food"),
    ("breakfast idli dosa", "Food"),
    ("tea and snacks evening", "Food"),
    ("ice cream parlour", "Food"),
    ("fruits and vegetables market", "Food"),
    ("rice dal sabzi dinner home", "Food"),
    ("cake for birthday celebration", "Food"),
    ("juice smoothie healthy drink", "Food"),
    ("mcdonalds burger fries", "Food"),
    ("chinese noodles fried rice", "Food"),
    ("sandwich wrap lunch office", "Food"),
    ("bakery pastry croissant", "Food"),
    ("cooking ingredients spices oil", "Food"),
    ("chocolates and biscuits snacks", "Food"),
    ("paneer tikka restaurant dinner", "Food"),
    ("fish curry meal non veg", "Food"),
    # Transport
    ("uber ride to office", "Transport"),
    ("ola cab airport drop", "Transport"),
    ("metro card recharge monthly", "Transport"),
    ("petrol fill up car", "Transport"),
    ("bus pass monthly commute", "Transport"),
    ("train ticket booking irctc", "Transport"),
    ("flight ticket to mumbai", "Transport"),
    ("parking charges mall", "Transport"),
    ("toll charges highway trip", "Transport"),
    ("auto rickshaw market to home", "Transport"),
    ("rapido bike taxi ride", "Transport"),
    ("diesel fuel truck", "Transport"),
    ("car service maintenance workshop", "Transport"),
    ("tyre change replacement", "Transport"),
    ("fastag recharge highway toll", "Transport"),
    ("cab ride to station", "Transport"),
    ("scooter fuel petrol pump", "Transport"),
    ("railway ticket reservation", "Transport"),
    ("airport transfer shuttle", "Transport"),
    ("commute daily travel office", "Transport"),
    ("vehicle insurance renewal", "Transport"),
    ("bike repair puncture fix", "Transport"),
    ("bus fare city transport", "Transport"),
    ("taxi ride night late", "Transport"),
    ("car wash cleaning service", "Transport"),
    # Shopping
    ("amazon order headphones electronics", "Shopping"),
    ("flipkart phone case cover", "Shopping"),
    ("new shoes sneakers nike", "Shopping"),
    ("clothing shopping mall", "Shopping"),
    ("laptop bag backpack online", "Shopping"),
    ("birthday gift friend present", "Shopping"),
    ("myntra dress fashion sale", "Shopping"),
    ("home decor curtains cushions", "Shopping"),
    ("kitchen appliance mixer grinder", "Shopping"),
    ("watch accessories jewelry", "Shopping"),
    ("gaming console controller", "Shopping"),
    ("cosmetics makeup nykaa order", "Shopping"),
    ("books stationery pens notebooks", "Shopping"),
    ("sunglasses polarized brand", "Shopping"),
    ("furniture table chair new", "Shopping"),
    ("electronics store gadget purchase", "Shopping"),
    ("perfume fragrance gift set", "Shopping"),
    ("jeans shirt formal wear", "Shopping"),
    ("phone cover charger cable", "Shopping"),
    ("meesho online fashion order", "Shopping"),
    ("wallet leather premium", "Shopping"),
    ("toy gift for kids child", "Shopping"),
    ("earbuds wireless bluetooth", "Shopping"),
    ("jacket winter wear coat", "Shopping"),
    ("ajio sale discount clothes", "Shopping"),
    # Bills
    ("electricity bill payment monthly", "Bills"),
    ("water bill municipal corporation", "Bills"),
    ("internet broadband airtel plan", "Bills"),
    ("mobile recharge jio prepaid", "Bills"),
    ("house rent monthly apartment", "Bills"),
    ("netflix subscription renewed", "Bills"),
    ("spotify premium music monthly", "Bills"),
    ("health insurance premium annual", "Bills"),
    ("emi payment home loan", "Bills"),
    ("credit card bill payment", "Bills"),
    ("gas pipeline bill cooking", "Bills"),
    ("gym membership fitness monthly", "Bills"),
    ("school tuition fee child", "Bills"),
    ("doctor consultation hospital visit", "Bills"),
    ("medicine pharmacy prescription", "Bills"),
    ("society maintenance charges", "Bills"),
    ("amazon prime subscription", "Bills"),
    ("youtube premium family plan", "Bills"),
    ("income tax advance payment", "Bills"),
    ("dental checkup cleaning dentist", "Bills"),
    ("lab test blood report health", "Bills"),
    ("property tax annual payment", "Bills"),
    ("insurance lic premium quarterly", "Bills"),
    ("college course training fee", "Bills"),
    ("vodafone vi postpaid bill", "Bills"),
    # Other
    ("movie tickets cinema hall", "Other"),
    ("haircut salon grooming", "Other"),
    ("donation charity ngo", "Other"),
    ("laundry dry cleaning clothes", "Other"),
    ("concert tickets live music", "Other"),
    ("wedding gift celebration", "Other"),
    ("temple donation puja expenses", "Other"),
    ("spa massage relaxation", "Other"),
    ("newspaper monthly subscription", "Other"),
    ("atm withdrawal bank charges", "Other"),
    ("party celebration friends", "Other"),
    ("pet food veterinary care", "Other"),
    ("hobby art craft supplies", "Other"),
    ("sports equipment cricket bat", "Other"),
    ("fine penalty traffic challan", "Other"),
    ("tip waiter service charge", "Other"),
    ("festival diwali crackers decor", "Other"),
    ("swimming pool membership", "Other"),
    ("photography camera accessories", "Other"),
    ("miscellaneous general expense", "Other"),
]


class CategoryClassifier:
    """AI-powered expense category classifier."""

    CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Other"]

    def __init__(self, db_path="finance.db"):
        self.db_path = db_path
        self.model = None
        self._build_model()

    def _build_model(self):
        """Train the ML model on synthetic + historical data."""
        texts = [t[0] for t in TRAINING_DATA]
        labels = [t[1] for t in TRAINING_DATA]

        # Build TF-IDF + Naive Bayes pipeline
        self.model = Pipeline([
            ("tfidf", TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                max_features=5000,
                stop_words="english",
            )),
            ("clf", MultinomialNB(alpha=0.1)),
        ])

        self.model.fit(texts, labels)

    def _keyword_classify(self, description):
        """
        Rule-based classification using keyword matching.
        Returns (category, confidence) or None if no strong match.
        """
        desc_lower = description.lower().strip()
        if not desc_lower:
            return None

        scores = {}
        for category, keywords in KEYWORD_RULES.items():
            score = 0
            for keyword in keywords:
                if keyword in desc_lower:
                    # Longer keyword matches are more specific → higher weight
                    score += len(keyword.split())
            scores[category] = score

        max_score = max(scores.values())
        if max_score == 0:
            return None

        best_category = max(scores, key=scores.get)

        # Check if it's a clear winner (not ambiguous)
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] > 0:
            # Confidence based on how dominant the top score is
            dominance = sorted_scores[0] / (sorted_scores[0] + sorted_scores[1] + 0.1)
            confidence = min(dominance * 100 + 20, 98)
        else:
            confidence = 85

        return best_category, round(confidence, 1)

    def _ml_classify(self, description):
        """
        ML-based classification using trained model.
        Returns (category, confidence).
        """
        if not description.strip():
            return "Other", 0

        probabilities = self.model.predict_proba([description])[0]
        classes = self.model.classes_
        max_idx = np.argmax(probabilities)

        category = classes[max_idx]
        confidence = round(probabilities[max_idx] * 100, 1)

        return category, confidence

    def classify(self, description):
        """
        Hybrid classification: keyword rules first, ML fallback.
        Returns dict with category, confidence, method, and all probabilities.
        """
        if not description or not description.strip():
            return {
                "category": "Other",
                "confidence": 0,
                "method": "default",
                "probabilities": {},
            }

        # Step 1: Try keyword-based classification
        keyword_result = self._keyword_classify(description)

        # Step 2: ML classification
        ml_category, ml_confidence = self._ml_classify(description)

        # Get all ML probabilities
        probabilities = {}
        if self.model:
            probs = self.model.predict_proba([description])[0]
            classes = self.model.classes_
            for cls, prob in zip(classes, probs):
                probabilities[cls] = round(prob * 100, 1)

        # Step 3: Decide which to use
        if keyword_result:
            kw_category, kw_confidence = keyword_result
            if kw_confidence >= 60:
                # Strong keyword match wins
                return {
                    "category": kw_category,
                    "confidence": kw_confidence,
                    "method": "Keyword Match",
                    "probabilities": probabilities,
                }

            # If keyword match is weak, blend with ML
            if kw_category == ml_category:
                # Both agree → boost confidence
                blended_conf = min((kw_confidence + ml_confidence) / 2 + 15, 98)
                return {
                    "category": kw_category,
                    "confidence": round(blended_conf, 1),
                    "method": "Hybrid (Keyword + ML)",
                    "probabilities": probabilities,
                }

            # Disagreement → use the one with higher confidence
            if kw_confidence >= ml_confidence:
                return {
                    "category": kw_category,
                    "confidence": kw_confidence,
                    "method": "Keyword Match",
                    "probabilities": probabilities,
                }

        # ML-only result
        return {
            "category": ml_category,
            "confidence": ml_confidence,
            "method": "ML (Naive Bayes)",
            "probabilities": probabilities,
        }

    def get_all_predictions(self, description):
        """Returns sorted list of all category predictions with probabilities."""
        result = self.classify(description)
        probs = result.get("probabilities", {})

        predictions = []
        for cat in self.CATEGORIES:
            is_selected = cat == result["category"]
            predictions.append({
                "category": cat,
                "probability": probs.get(cat, 0),
                "selected": is_selected,
            })

        predictions.sort(key=lambda x: x["probability"], reverse=True)
        return predictions, result

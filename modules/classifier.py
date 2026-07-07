import logging

logger = logging.getLogger(__name__)

class EmailClassifier:
    """
    Classifies emails into exactly one primary business category:
    Sales Lead, Support, Invoice, HR, Internal, or Spam.
    Uses a keyword-based weighted scoring system.
    """
    def __init__(self):
        # Define categories and keyword weight mappings
        # Includes expansion for credit cards, banks, job roles, etc. as noted in SRS
        self.category_keywords = {
            "Invoice": {
                "invoice": 3, "payment": 2, "due": 2, "billing": 2, "receipt": 2,
                "bill": 2, "transaction": 2, "wire transfer": 3, "credit card": 2,
                "bank": 1, "statement": 2, "charge": 1, "amount due": 3, "overdue": 3,
                "payable": 2, "remittance": 3, "finance": 1
            },
            "Support": {
                "issue": 2, "error": 2, "problem": 2, "help": 1, "bug": 3,
                "ticket": 3, "broken": 2, "fail": 1, "failure": 2, "support": 3,
                "crash": 3, "doesn't work": 3, "not working": 2, "down": 1,
                "assistance": 2, "technical": 1, "resolved": 1, "outage": 3
            },
            "Sales Lead": {
                "interested": 2, "pricing": 2, "quote": 3, "inquiry": 2, "demo": 3,
                "proposal": 3, "buy": 2, "purchase": 2, "sales": 2, "product info": 3,
                "services": 1, "partnership": 2, "business opportunity": 3, "quotation": 3,
                "pricing sheet": 3, "schedule call": 2
            },
            "HR": {
                "resume": 3, "application": 2, "cv": 3, "hiring": 2, "job": 2,
                "interview": 3, "applicant": 3, "recruit": 2, "recruitment": 2,
                "cover letter": 3, "role": 1, "position": 1, "career": 2,
                "onboarding": 2, "payroll": 1, "candidate": 2
            },
            "Internal": {
                "meeting": 2, "sync": 2, "memo": 3, "team": 1, "internal": 3,
                "discussion": 1, "colleague": 2, "standup": 3, "all-hands": 4,
                "roadmap": 2, "company policy": 3, "office": 1, "announcement": 2,
                "workspace": 1, "manager": 1
            },
            "Spam": {
                "lottery": 4, "free": 2, "win": 2, "claim": 2, "gift card": 3,
                "prize": 3, "promo": 2, "promotion": 2, "subscribe": 2,
                "unsubscribe": 2, "viagra": 5, "casino": 5, "betting": 4,
                "earn money": 3, "make money": 3, "click here": 3, "urgent action": 2,
                "crypto trading": 3, "investment opportunity": 3, "cash prize": 4
            }
        }
        # Fallback category if all scores are 0
        self.default_category = "Internal"

    def classify(self, subject: str, preprocessed_body: str) -> str:
        """
        Evaluates scores for all categories and returns the category with the highest score.
        Subject keyword occurrences are weighted double compared to body occurrences.
        """
        subject_lower = subject.lower()
        body_lower = preprocessed_body.lower()

        scores = {cat: 0 for cat in self.category_keywords.keys()}

        for cat, keywords in self.category_keywords.items():
            for kw, weight in keywords.items():
                # Count in subject (weighted x2)
                sub_count = subject_lower.count(kw)
                scores[cat] += sub_count * weight * 2

                # Count in preprocessed body
                body_count = body_lower.count(kw)
                scores[cat] += body_count * weight

        # Determine category with highest positive score
        best_category = self.default_category
        max_score = 0

        for cat, score in scores.items():
            if score > max_score:
                max_score = score
                best_category = cat

        logger.debug(f"Email classification scores: {scores} -> Selected: {best_category}")
        return best_category

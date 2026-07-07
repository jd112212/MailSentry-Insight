import re

class TextCleaner:
    """
    Cleans and preprocesses raw email body text for downstream classification.
    """
    def __init__(self, remove_stopwords: bool = True):
        self.remove_stopwords = remove_stopwords
        # Standard english stopwords list
        self.stopwords = {
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
            "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't",
            "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
            "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
            "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how",
            "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
            "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
            "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
            "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the",
            "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
            "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
            "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
            "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
            "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
        }

    def strip_html(self, text: str) -> str:
        """
        Removes HTML tags, styling blocks, and script blocks from a string.
        """
        if not text:
            return ""
        # Remove head, style and script tags content
        clean_pattern = re.compile(r'<head.*?>.*?</head>|<style.*?>.*?</style>|<script.*?>.*?</script>', re.DOTALL | re.IGNORECASE)
        text = clean_pattern.sub('', text)
        # Remove other HTML tags
        html_tags_pattern = re.compile(r'<.*?>')
        text = html_tags_pattern.sub(' ', text)
        return text

    def clean_text(self, text: str) -> str:
        """
        Runs the full text preprocessing pipeline:
        1. Strips HTML
        2. Lowercases
        3. Removes special characters (keeping alphanumerics)
        4. Normalizes whitespaces
        5. Optionally removes stopwords
        """
        if not text:
            return ""

        # Step 1: Strip HTML
        text = self.strip_html(text)

        # Step 2: Lowercase
        text = text.lower()

        # Step 3: Remove special characters (keep words and spaces)
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)

        # Step 4: Normalize whitespace (tabs, newlines, multiple spaces)
        text = re.sub(r'\s+', ' ', text).strip()

        # Step 5: Stopwords removal
        if self.remove_stopwords:
            words = text.split()
            words = [word for word in words if word not in self.stopwords]
            text = ' '.join(words)

        return text

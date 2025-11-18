from typing import Optional, List, Tuple
import re
from sqlalchemy.orm import Session
from app.models import Transaction, Category, MerchantRule


class TransactionCategorizer:
    """
    Intelligent transaction categorization service.

    This service automatically categorizes transactions based on:
    1. User-defined merchant rules
    2. Global/admin-defined rules
    3. Keyword matching
    4. (Future) Machine learning or external API lookups
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self._load_rules()
        self._load_default_keywords()

    def _load_rules(self):
        """Load user and global merchant rules"""
        self.rules = (
            self.db.query(MerchantRule)
            .filter(
                (MerchantRule.user_id == self.user_id) | (MerchantRule.is_global == True)
            )
            .order_by(MerchantRule.priority.desc())
            .all()
        )

    def _load_default_keywords(self):
        """
        Load default keyword patterns for common categories.

        These are fallback patterns when no explicit merchant rules exist.
        """
        self.default_keywords = {
            "Groceries": [
                r'\b(walmart|target|kroger|safeway|whole foods|trader joe|costco|albertsons)\b',
                r'\b(grocery|supermarket|market)\b',
            ],
            "Dining": [
                r'\b(restaurant|cafe|coffee|starbucks|mcdonald|burger|pizza|subway)\b',
                r'\b(doordash|ubereats|grubhub|postmates)\b',
            ],
            "Transport": [
                r'\b(uber|lyft|taxi|gas|shell|chevron|exxon|bp|mobil)\b',
                r'\b(parking|toll)\b',
            ],
            "Shopping": [
                r'\b(amazon|ebay|etsy|shop|store|retail)\b',
            ],
            "Utilities": [
                r'\b(electric|power|gas|water|utility|internet|cable|phone|verizon|at&t)\b',
            ],
            "Entertainment": [
                r'\b(netflix|spotify|hulu|disney|movie|theater|concert|ticket)\b',
            ],
            "Healthcare": [
                r'\b(pharmacy|cvs|walgreens|medical|doctor|hospital|clinic)\b',
            ],
            "Subscriptions": [
                r'\b(subscription|membership|annual fee|monthly fee)\b',
            ],
        }

    def categorize_transaction(
        self, transaction: Transaction, save: bool = True
    ) -> Tuple[Optional[int], float]:
        """
        Categorize a single transaction.

        Args:
            transaction: Transaction object to categorize
            save: Whether to save the category to the database

        Returns:
            Tuple of (category_id, confidence_score)
        """
        merchant = transaction.merchant_name or ""
        description = transaction.description or ""
        search_text = f"{merchant} {description}".lower()

        # Try explicit merchant rules first
        for rule in self.rules:
            if self._matches_rule(search_text, rule):
                if save:
                    transaction.category_id = rule.category_id
                    transaction.category_confidence = float(rule.confidence)
                    self.db.commit()
                return rule.category_id, float(rule.confidence)

        # Try default keyword patterns
        category_id, confidence = self._match_default_keywords(search_text)
        if category_id:
            if save:
                transaction.category_id = category_id
                transaction.category_confidence = confidence
                self.db.commit()
            return category_id, confidence

        # Try merchant enrichment (stub for now)
        category_id, confidence = self._enrich_merchant(merchant)
        if category_id:
            if save:
                transaction.category_id = category_id
                transaction.category_confidence = confidence
                self.db.commit()
            return category_id, confidence

        # No match found
        return None, 0.0

    def _matches_rule(self, search_text: str, rule: MerchantRule) -> bool:
        """Check if search text matches a merchant rule"""
        pattern = rule.pattern
        if not rule.is_case_sensitive:
            pattern = pattern.lower()
            search_text = search_text.lower()

        if rule.pattern_type == "exact":
            return pattern == search_text
        elif rule.pattern_type == "contains":
            return pattern in search_text
        elif rule.pattern_type == "regex":
            try:
                flags = 0 if rule.is_case_sensitive else re.IGNORECASE
                return bool(re.search(pattern, search_text, flags))
            except re.error:
                return False
        return False

    def _match_default_keywords(self, search_text: str) -> Tuple[Optional[int], float]:
        """Match against default keyword patterns"""
        for category_name, patterns in self.default_keywords.items():
            for pattern in patterns:
                if re.search(pattern, search_text, re.IGNORECASE):
                    # Find or create category
                    category = (
                        self.db.query(Category)
                        .filter(Category.name == category_name)
                        .first()
                    )
                    if category:
                        return category.id, 0.7  # Medium confidence for keyword match
        return None, 0.0

    def _enrich_merchant(self, merchant_name: str) -> Tuple[Optional[int], float]:
        """
        Enrich merchant information using external service.

        THIS IS A STUB IMPLEMENTATION.

        In production, this could:
        1. Call an external API (e.g., merchant categorization service)
        2. Use a machine learning model
        3. Search the web for merchant information

        To implement:
        - Add API credentials to environment variables
        - Implement HTTP client to call external service
        - Parse response and map to category
        - Return category_id and confidence score

        Example:
            async def _enrich_merchant(self, merchant_name: str):
                # Call external API
                response = await httpx.get(
                    f"https://api.merchant-lookup.com/categorize",
                    params={"merchant": merchant_name}
                )
                data = response.json()
                category_name = data.get("category")

                # Map to local category
                category = self.db.query(Category).filter(
                    Category.name == category_name
                ).first()

                return category.id if category else None, data.get("confidence", 0.5)
        """
        # Stub: return None (no enrichment)
        return None, 0.0

    def categorize_bulk(self, transactions: List[Transaction], save: bool = True):
        """
        Categorize multiple transactions in bulk.

        Args:
            transactions: List of Transaction objects
            save: Whether to save categories to database
        """
        for transaction in transactions:
            if not transaction.manually_categorized:  # Don't override manual categorizations
                self.categorize_transaction(transaction, save=save)

    def create_rule_from_transaction(
        self, transaction: Transaction, category_id: int, pattern_type: str = "contains"
    ) -> MerchantRule:
        """
        Create a merchant rule based on a transaction.

        This is called when a user manually categorizes a transaction and
        chooses to "always categorize this merchant as X".

        Args:
            transaction: The transaction to base the rule on
            category_id: The category to assign
            pattern_type: Type of pattern matching (exact, contains, regex)

        Returns:
            Created MerchantRule object
        """
        merchant_name = transaction.merchant_name or transaction.description

        # Check if rule already exists
        existing_rule = (
            self.db.query(MerchantRule)
            .filter(
                MerchantRule.user_id == self.user_id,
                MerchantRule.pattern == merchant_name,
            )
            .first()
        )

        if existing_rule:
            # Update existing rule
            existing_rule.category_id = category_id
            self.db.commit()
            return existing_rule

        # Create new rule
        new_rule = MerchantRule(
            user_id=self.user_id,
            category_id=category_id,
            pattern=merchant_name,
            pattern_type=pattern_type,
            is_case_sensitive=False,
            priority=10,  # User-created rules get higher priority
            confidence=1.0,
        )

        self.db.add(new_rule)
        self.db.commit()
        self.db.refresh(new_rule)

        return new_rule

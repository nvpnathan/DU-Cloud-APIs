import os
import sqlite3
import logging
from collections import defaultdict

# Cache configuration
CACHE_DIR = "cache"
SQLITE_DB_PATH = os.path.join(CACHE_DIR, "document_cache.db")
# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Create business_rule_eval table
def create_business_rule_eval_table():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS business_rule_eval (
                document_id TEXT PRIMARY KEY,
                earnings_rule_passed BOOLEAN,
                gross_earnings_period_passed BOOLEAN,
                gross_earnings_ytd_passed BOOLEAN
            )
        """
        )
        conn.commit()
    finally:
        conn.close()


# Populate business_rule_eval table
def insert_business_rule_eval(
    document_id, earnings_rule_passed, gross_period_passed, gross_ytd_passed
):
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO business_rule_eval (document_id, earnings_rule_passed, gross_earnings_period_passed, gross_earnings_ytd_passed)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
                earnings_rule_passed=excluded.earnings_rule_passed,
                gross_earnings_period_passed=excluded.gross_earnings_period_passed,
                gross_earnings_ytd_passed=excluded.gross_earnings_ytd_passed
        """,
            (document_id, earnings_rule_passed, gross_period_passed, gross_ytd_passed),
        )
        conn.commit()
    finally:
        conn.close()


# Process all documents and evaluate business rules
def process_all_documents():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    try:
        # Step 1: Fetch all unique document_ids
        cursor.execute(
            "SELECT DISTINCT document_id FROM extraction WHERE field_id='Paystub > Earnings'"
        )
        document_ids = [
            row[0] for row in cursor.fetchall()
        ]  # Extract document_id from rows

        # Step 2: Loop through each document_id and process
        for document_id in document_ids:
            print(f"Processing document_id: {document_id}")

            # Fetch earnings data for the current document
            earnings_data = fetch_earnings_data(document_id)
            gross_earnings_data = fetch_gross_earnings_data(document_id)

            # Evaluate business rules
            earnings_rule_passed = earnings_business_rule(earnings_data)
            period_passed, ytd_passed = gross_earnings_business_rule(
                earnings_data, gross_earnings_data
            )

            # Populate the business_rule_eval table
            insert_business_rule_eval(
                document_id, earnings_rule_passed, period_passed, ytd_passed
            )
    finally:
        conn.close()


# Database Operations
def fetch_data(query, params):
    """Executes a database query and returns the results."""
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def fetch_earnings_data(document_id):
    query = """
        SELECT field, field_value, is_missing, row_index, column_index
        FROM extraction
        WHERE document_id=? AND field_id='Paystub > Earnings' AND NOT field='Paystub > Earnings'
    """
    rows = fetch_data(query, (document_id,))
    return _organize_data(rows)


def fetch_gross_earnings_data(document_id):
    query = """
        SELECT field, field_value, is_missing, row_index, column_index
        FROM extraction
        WHERE document_id=? AND field IN ('Total Gross earnings this period', 'Total Gross earnings ytd\u200b')
    """
    rows = fetch_data(query, (document_id,))
    return _organize_data(rows)


# Utility Functions
def _normalize_field(field, column_index):
    return field.strip() if field else f"Unknown Field {column_index}"


def _organize_data(rows):
    """Converts raw database rows into a structured dictionary."""
    data = defaultdict(lambda: defaultdict(dict))
    for field, value, is_missing, row_index, column_index in rows:
        normalized_field = _normalize_field(field, column_index)
        data[row_index][normalized_field] = {
            "value": value,
            "is_missing": bool(is_missing),
            "column_index": column_index,
        }
    return data


def sum_of_earnings(earnings_data):
    """Calculates total earnings for this period and YTD."""
    total_earnings, total_earnings_ytd = 0.0, 0.0
    for fields in earnings_data.values():
        if "Earnings this period" in fields:
            value = fields["Earnings this period"].get("value")
            if value and not fields["Earnings this period"]["is_missing"]:
                total_earnings += float(value)

        if "Gross earnings ytd\u200b" in fields:
            value = fields["Gross earnings ytd\u200b"].get("value")
            if value and not fields["Gross earnings ytd\u200b"]["is_missing"]:
                total_earnings_ytd += float(value)
    return total_earnings, total_earnings_ytd


# Business Rules
def earnings_business_rule(data):
    """Checks the earnings rate business rule for all rows."""
    required_fields = [
        "Earnings type",
        "Earnings rate",
        "Earnings hours",
        "Earnings this period",
    ]
    passed = True

    for row_index, fields in data.items():
        field_values = {
            f: fields[f].get("value") for f in required_fields if f in fields
        }
        if any(v is None for v in field_values.values()):
            logger.warning("Row %f failed rate check: %f", row_index, field_values)
            passed = False
            continue

        try:
            rate = float(field_values["Earnings rate"])
            hours = float(field_values["Earnings hours"])
            this_period = float(field_values["Earnings this period"])
            if rate * hours != this_period:
                logger.warning("Row %f failed rate check: %f", row_index, field_values)
                passed = False
        except ValueError as e:
            logger.error("Error processing row %f: %f", row_index, e)
            passed = False

    return passed


def gross_earnings_business_rule(earnings_data, gross_earnings_data):
    """
    Validates gross earnings against calculated totals.

    Args:
        earnings_data (dict): Nested dictionary containing earnings data.
        gross_earnings_data (dict): Nested dictionary containing gross earnings data.

    Returns:
        tuple: (bool, bool) indicating if the period and YTD gross earnings rules passed.
    """
    # Calculate the sum of individual earnings for the period and YTD
    total_earnings, total_earnings_ytd = sum_of_earnings(earnings_data)

    # Initialize gross earnings values
    gross_this_period = None
    gross_ytd = None

    # Extract gross earnings values, accounting for nested structure and missing fields
    for fields in gross_earnings_data.values():
        for field_name, field_details in fields.items():
            if field_name == "Total Gross earnings this period":
                gross_this_period = (
                    float(field_details.get("value", 0))
                    if not field_details.get("is_missing")
                    else None
                )
            elif field_name == "Total Gross earnings ytd\u200b":
                gross_ytd = (
                    float(field_details.get("value", 0))
                    if not field_details.get("is_missing")
                    else None
                )

    # Validate totals against gross earnings values
    period_rule_passed = True
    ytd_rule_passed = True

    if gross_this_period is not None:
        if total_earnings != gross_this_period:
            logger.warning(
                "Mismatch: Total earnings this period (%f) != Gross earnings this period (%f)",
                total_earnings,
                gross_this_period,
            )
            period_rule_passed = False
        else:
            logger.info(
                "Gross earnings this period check passed: %f matches %f",
                total_earnings,
                gross_this_period,
            )

    if gross_ytd is not None:
        if total_earnings_ytd != gross_ytd:
            logger.warning(
                "Mismatch: Total earnings YTD (%f) != Gross earnings YTD (%f)",
                total_earnings_ytd,
                gross_ytd,
            )
            ytd_rule_passed = False
        else:
            logger.info(
                "Gross earnings YTD check passed: %f matches %f",
                total_earnings_ytd,
                gross_ytd,
            )

    return period_rule_passed, ytd_rule_passed


if __name__ == "__main__":
    create_business_rule_eval_table()
    process_all_documents()

import datetime

import pytest

from domain_rag_copilot.schemas.records import (
    make_competitor_price,
    make_document,
    make_price,
    make_product,
    make_promotion,
    make_sale,
)
from domain_rag_copilot.schemas.validation import ValidationError


# small helpers that return a good row each time, so a test can break one field

def good_product():
    return {"product_id": "P001", "product_name": "Orange Juice 1L", "category": "Beverages"}


def good_price():
    return {"product_id": "P001", "price_date": "2026-01-05", "price": "3.20",
            "currency": "USD", "price_type": "regular"}


def good_promotion():
    return {"promotion_id": "PROMO-001", "product_id": "P001", "start_date": "2026-01-19",
            "end_date": "2026-01-25", "discount_type": "percent", "discount_value": "10"}


def good_sale():
    return {"product_id": "P001", "sale_date": "2026-01-05", "units": "100",
            "revenue": "320.00", "currency": "USD"}


def good_competitor():
    return {"observation_id": "CMP-001", "competitor_name": "FreshMart",
            "competitor_product": "Orange Juice 1L", "observed_price": "3.10",
            "currency": "USD", "observation_date": "2026-01-12", "source": "shelf check"}


def good_document():
    return {"document_id": "DOC-001", "title": "A brief", "source_name": "brief.txt",
            "source_type": "promotion_brief", "source_path": "documents/brief.txt",
            "is_synthetic": "true"}


# valid rows

def test_valid_rows_are_accepted():
    assert make_product(good_product()).brand is None
    assert make_price(good_price()).price == 3.20
    assert make_promotion(good_promotion()).end_date == datetime.date(2026, 1, 25)
    assert make_sale(good_sale()).units == 100
    assert make_competitor_price(good_competitor()).observed_price == 3.10
    assert make_document(good_document()).is_synthetic is True


def test_optional_fields_can_be_filled_in():
    row = good_sale()
    row.update({"cost": "210.00", "region": "North", "channel": "store"})
    sale = make_sale(row)
    assert (sale.cost, sale.region, sale.channel) == (210.0, "North", "store")


def test_document_tag_lists_are_split():
    row = good_document()
    row.update({"product_ids": "P001|P002", "promotion_ids": "PROMO-001"})
    document = make_document(row)
    assert document.product_ids == ("P001", "P002")
    assert document.promotion_ids == ("PROMO-001",)


# missing values

def test_missing_required_field():
    row = good_product()
    row["product_name"] = ""
    with pytest.raises(ValidationError, match="product_name is required"):
        make_product(row)


def test_missing_key_is_not_replaced_by_a_default():
    row = good_sale()
    del row["product_id"]
    with pytest.raises(ValidationError, match="product_id is required"):
        make_sale(row)


# wrong types

def test_price_must_be_a_number():
    row = good_price()
    row["price"] = "cheap"
    with pytest.raises(ValidationError, match="price must be a number"):
        make_price(row)


def test_units_must_be_a_whole_number():
    row = good_sale()
    row["units"] = "12.5"
    with pytest.raises(ValidationError, match="units must be a whole number"):
        make_sale(row)


def test_nan_is_rejected():
    row = good_price()
    row["price"] = "nan"
    with pytest.raises(ValidationError, match="normal number"):
        make_price(row)


def test_bad_date_formats_are_rejected():
    for bad_date in ["05/01/2026", "2026-1-5", "2026-13-01", "20260105"]:
        row = good_price()
        row["price_date"] = bad_date
        with pytest.raises(ValidationError, match="YYYY-MM-DD"):
            make_price(row)


def test_currency_must_be_three_uppercase_letters():
    row = good_price()
    row["currency"] = "usd"
    with pytest.raises(ValidationError, match="currency"):
        make_price(row)


def test_is_synthetic_must_be_true_or_false():
    row = good_document()
    row["is_synthetic"] = "maybe"
    with pytest.raises(ValidationError, match="true or false"):
        make_document(row)


# impossible values

def test_price_must_be_above_zero():
    for bad_price in ["0", "-1.50"]:
        row = good_price()
        row["price"] = bad_price
        with pytest.raises(ValidationError, match="price must be greater than 0"):
            make_price(row)


def test_negative_units_and_revenue_are_rejected():
    row = good_sale()
    row["units"] = "-3"
    with pytest.raises(ValidationError, match="units must not be negative"):
        make_sale(row)
    row = good_sale()
    row["revenue"] = "-1"
    with pytest.raises(ValidationError, match="revenue must not be negative"):
        make_sale(row)


def test_revenue_without_units_is_rejected():
    row = good_sale()
    row["units"] = "0"
    with pytest.raises(ValidationError, match="units is 0"):
        make_sale(row)


def test_zero_units_and_zero_revenue_is_allowed():
    row = good_sale()
    row.update({"units": "0", "revenue": "0"})
    assert make_sale(row).units == 0


def test_promotion_end_before_start():
    row = good_promotion()
    row["end_date"] = "2026-01-10"
    with pytest.raises(ValidationError, match="before start_date"):
        make_promotion(row)


def test_one_day_promotion_is_allowed():
    row = good_promotion()
    row["end_date"] = row["start_date"]
    assert make_promotion(row).start_date == make_promotion(row).end_date


def test_percent_discount_over_100():
    row = good_promotion()
    row["discount_value"] = "120"
    with pytest.raises(ValidationError, match="more than 100"):
        make_promotion(row)


def test_fixed_discount_needs_a_currency():
    row = good_promotion()
    row.update({"discount_type": "fixed_amount", "discount_value": "0.50"})
    with pytest.raises(ValidationError, match="currency is required"):
        make_promotion(row)
    row["currency"] = "USD"
    assert make_promotion(row).currency == "USD"


def test_unknown_price_type_and_discount_type():
    row = good_price()
    row["price_type"] = "sale"
    with pytest.raises(ValidationError, match="price_type"):
        make_price(row)
    row = good_promotion()
    row["discount_type"] = "bogo"
    with pytest.raises(ValidationError, match="discount_type"):
        make_promotion(row)


# ids and paths

def test_ids_cannot_contain_spaces_or_separators():
    for bad_id in ["P 001", "P001|P002", "DOC::1"]:
        row = good_product()
        row["product_id"] = bad_id
        with pytest.raises(ValidationError, match="product_id"):
            make_product(row)


def test_tag_list_cannot_repeat_an_id():
    row = good_document()
    row["product_ids"] = "P001|P001"
    with pytest.raises(ValidationError, match="twice"):
        make_document(row)


def test_document_path_must_be_relative_and_stay_inside_the_data_folder():
    for bad_path in ["/etc/notes.txt", "../secret.txt", "C:\\docs\\a.txt", "documents\\a.txt"]:
        row = good_document()
        row["source_path"] = bad_path
        with pytest.raises(ValidationError, match="source_path"):
            make_document(row)

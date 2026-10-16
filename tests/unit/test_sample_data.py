import dataclasses

import pytest

from domain_rag_copilot.config import PROJECT_ROOT, load_settings
from domain_rag_copilot.schemas.loader import check_data, load_sample_data, read_table
from domain_rag_copilot.schemas.validation import ValidationError

SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"


def test_sample_data_loads_and_passes_all_checks():
    data = load_sample_data(SAMPLE_DIR)
    counts = {name: len(rows) for name, rows in data.items()}
    assert counts == {"products": 3, "prices": 32, "promotions": 3, "sales": 32,
                      "competitor_prices": 6, "documents": 3}


def test_default_folder_is_the_stage_1_sample_data_setting():
    settings = load_settings(env_file=None, environ={})
    assert settings.sample_data_dir == SAMPLE_DIR
    assert len(load_sample_data(settings.sample_data_dir)["products"]) == 3


def test_sample_files_are_marked_synthetic():
    data = load_sample_data(SAMPLE_DIR)
    for document in data["documents"]:
        assert document.is_synthetic
        assert "synthetic" in document.source_path
        text = (SAMPLE_DIR / document.source_path).read_text(encoding="utf-8")
        assert text.startswith("SYNTHETIC SAMPLE DOCUMENT")
    for file in SAMPLE_DIR.glob("*.csv"):
        assert file.name.endswith("_synthetic.csv")


def test_every_sale_has_a_price_for_the_same_day_and_place():
    data = load_sample_data(SAMPLE_DIR)
    price_keys = {(p.product_id, p.price_date, p.region, p.channel) for p in data["prices"]}
    for sale in data["sales"]:
        assert (sale.product_id, sale.sale_date, sale.region, sale.channel) in price_keys


def test_each_promotion_week_has_a_promotional_price():
    data = load_sample_data(SAMPLE_DIR)
    promo_prices = {(p.product_id, p.price_date) for p in data["prices"]
                    if p.price_type == "promotional"}
    for promo in data["promotions"]:
        assert (promo.product_id, promo.start_date) in promo_prices


# broken keys and joins. each test copies the good data and breaks one thing

def test_duplicate_sale_is_found():
    data = load_sample_data(SAMPLE_DIR)
    data["sales"].append(data["sales"][0])
    with pytest.raises(ValidationError, match="sales: duplicate key"):
        check_data(data)


def test_duplicate_product_id_is_found():
    data = load_sample_data(SAMPLE_DIR)
    data["products"].append(data["products"][0])
    with pytest.raises(ValidationError, match="products: duplicate key"):
        check_data(data)


def test_sale_for_unknown_product():
    data = load_sample_data(SAMPLE_DIR)
    data["sales"][0] = dataclasses.replace(data["sales"][0], product_id="P999")
    with pytest.raises(ValidationError, match="sales: unknown product_id P999"):
        check_data(data)


def test_promotion_for_unknown_product():
    data = load_sample_data(SAMPLE_DIR)
    data["promotions"][0] = dataclasses.replace(data["promotions"][0], product_id="P999")
    with pytest.raises(ValidationError, match="promotions: unknown product_id P999"):
        check_data(data)


def test_competitor_row_with_unknown_product():
    data = load_sample_data(SAMPLE_DIR)
    data["competitor_prices"][0] = dataclasses.replace(data["competitor_prices"][0], product_id="P999")
    with pytest.raises(ValidationError, match="competitor_prices: unknown product_id P999"):
        check_data(data)


def test_competitor_row_without_product_is_fine():
    data = load_sample_data(SAMPLE_DIR)
    assert any(row.product_id is None for row in data["competitor_prices"])
    check_data(data)


def test_document_tagged_with_unknown_promotion():
    data = load_sample_data(SAMPLE_DIR)
    data["documents"][0] = dataclasses.replace(data["documents"][0], promotion_ids=("PROMO-999",))
    with pytest.raises(ValidationError, match="unknown promotion_id PROMO-999"):
        check_data(data)


def test_document_file_that_does_not_exist():
    data = load_sample_data(SAMPLE_DIR)
    data["documents"][0] = dataclasses.replace(data["documents"][0], source_path="documents/nope.txt")
    with pytest.raises(ValidationError, match="file not found"):
        check_data(data, base_dir=SAMPLE_DIR)


def test_all_problems_are_listed_together():
    data = load_sample_data(SAMPLE_DIR)
    data["sales"][0] = dataclasses.replace(data["sales"][0], product_id="P998")
    data["prices"][0] = dataclasses.replace(data["prices"][0], product_id="P999")
    with pytest.raises(ValidationError) as error:
        check_data(data)
    assert "P998" in str(error.value) and "P999" in str(error.value)


# problems in a csv file

def write_file(tmp_path, text):
    path = tmp_path / "products.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_missing_required_column(tmp_path):
    path = write_file(tmp_path, "product_id,product_name\nP001,Juice\n")
    with pytest.raises(ValidationError, match="missing column.*category"):
        read_table(path, "products")


def test_unknown_column_is_rejected(tmp_path):
    path = write_file(tmp_path, "product_id,product_name,category,brnad\nP001,Juice,Drinks,X\n")
    with pytest.raises(ValidationError, match="unknown column.*brnad"):
        read_table(path, "products")


def test_error_message_has_file_name_and_line_number(tmp_path):
    path = write_file(tmp_path, "product_id,product_name,category\nP001,Juice,Drinks\nP002,,Drinks\n")
    with pytest.raises(ValidationError, match=r"products.csv line 3: product_name is required"):
        read_table(path, "products")


def test_row_with_too_many_values(tmp_path):
    path = write_file(tmp_path, "product_id,product_name,category\nP001,Juice,Drinks,extra\n")
    with pytest.raises(ValidationError, match="line 2.*more values"):
        read_table(path, "products")

import csv
from dataclasses import fields
from pathlib import Path

from domain_rag_copilot.config import load_settings
from domain_rag_copilot.schemas.records import TABLES
from domain_rag_copilot.schemas.validation import ValidationError

SAMPLE_FILES = {
    "products": "products_synthetic.csv",
    "prices": "prices_synthetic.csv",
    "promotions": "promotions_synthetic.csv",
    "sales": "sales_synthetic.csv",
    "competitor_prices": "competitor_prices_synthetic.csv",
    "documents": "documents_synthetic.csv",
}


def check_header(table_name, header):
    info = TABLES[table_name]
    allowed = [field.name for field in fields(info["record"])]
    missing = [name for name in info["required"] if name not in header]
    unknown = [name for name in header if name not in allowed]
    if missing:
        raise ValidationError(f"{table_name}: missing column(s): {', '.join(missing)}")
    if unknown:
        raise ValidationError(f"{table_name}: unknown column(s): {', '.join(unknown)}. "
                              f"Allowed columns: {', '.join(allowed)}")


def read_table(path, table_name):
    """Read one csv file and return a list of validated records."""
    path = Path(path)
    make_record = TABLES[table_name]["make"]
    records = []
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        check_header(table_name, reader.fieldnames or [])
        # line 1 is the header, so the first data row is line 2
        for line_number, row in enumerate(reader, start=2):
            try:
                if None in row:
                    raise ValidationError("row has more values than the header has columns")
                records.append(make_record(row))
            except ValidationError as error:
                raise ValidationError(f"{path.name} line {line_number}: {error}") from None
    return records


def find_duplicates(records, key_function):
    seen = set()
    duplicates = []
    for record in records:
        key = key_function(record)
        if key in seen:
            duplicates.append(key)
        seen.add(key)
    return duplicates


def check_data(data, base_dir=None):
    """Check keys and joins across tables. Raises one error that lists every problem found.

    base_dir is the folder that document source_path values are relative to.
    If it is None the document files are not checked.
    """
    problems = []

    # keys must be unique inside each table
    keys = {
        "products": lambda r: r.product_id,
        "prices": lambda r: (r.product_id, r.price_date, r.region, r.channel),
        "promotions": lambda r: r.promotion_id,
        "sales": lambda r: (r.product_id, r.sale_date, r.region, r.channel),
        "competitor_prices": lambda r: r.observation_id,
        "documents": lambda r: r.document_id,
    }
    for table_name, key_function in keys.items():
        for key in find_duplicates(data[table_name], key_function):
            problems.append(f"{table_name}: duplicate key {key}")

    # ids used in other tables must exist
    product_ids = {p.product_id for p in data["products"]}
    promotion_ids = {p.promotion_id for p in data["promotions"]}

    for table_name in ["prices", "promotions", "sales"]:
        for record in data[table_name]:
            if record.product_id not in product_ids:
                problems.append(f"{table_name}: unknown product_id {record.product_id}")
    for record in data["competitor_prices"]:
        if record.product_id is not None and record.product_id not in product_ids:
            problems.append(f"competitor_prices: unknown product_id {record.product_id}"
                            f" in {record.observation_id}")
    for record in data["documents"]:
        for product_id in record.product_ids:
            if product_id not in product_ids:
                problems.append(f"documents: {record.document_id} has unknown product_id {product_id}")
        for promotion_id in record.promotion_ids:
            if promotion_id not in promotion_ids:
                problems.append(f"documents: {record.document_id} has unknown promotion_id {promotion_id}")
        if base_dir is not None and not (Path(base_dir) / record.source_path).is_file():
            problems.append(f"documents: {record.document_id} file not found: {record.source_path}")

    if problems:
        raise ValidationError("data problems found:\n  " + "\n  ".join(problems))


def load_sample_data(sample_dir=None):
    """Load and check the synthetic sample files. Returns a dict of table name to records."""
    if sample_dir is None:
        sample_dir = load_settings().sample_data_dir
    sample_dir = Path(sample_dir)

    data = {}
    for table_name, file_name in SAMPLE_FILES.items():
        data[table_name] = read_table(sample_dir / file_name, table_name)
    check_data(data, base_dir=sample_dir)
    return data

from dataclasses import dataclass
from datetime import date

from domain_rag_copilot.schemas.validation import (
    ValidationError,
    get_bool,
    get_choice,
    get_currency,
    get_date,
    get_float,
    get_id,
    get_id_list,
    get_int,
    get_text,
)

PRICE_TYPES = ["regular", "promotional"]
DISCOUNT_TYPES = ["percent", "fixed_amount"]


@dataclass(frozen=True)
class Product:
    product_id: str
    product_name: str
    category: str
    brand: str | None = None


@dataclass(frozen=True)
class Price:
    product_id: str
    price_date: date
    price: float
    currency: str
    price_type: str
    region: str | None = None
    channel: str | None = None


@dataclass(frozen=True)
class Promotion:
    promotion_id: str
    product_id: str
    start_date: date
    end_date: date
    discount_type: str
    discount_value: float
    currency: str | None = None
    region: str | None = None
    channel: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class Sale:
    product_id: str
    sale_date: date
    units: int
    revenue: float
    currency: str
    cost: float | None = None
    region: str | None = None
    channel: str | None = None


@dataclass(frozen=True)
class CompetitorPrice:
    observation_id: str
    competitor_name: str
    competitor_product: str
    observed_price: float
    currency: str
    observation_date: date
    source: str
    product_id: str | None = None
    region: str | None = None
    channel: str | None = None


@dataclass(frozen=True)
class DocumentMeta:
    document_id: str
    title: str
    source_name: str
    source_type: str
    source_path: str
    is_synthetic: bool
    effective_date: date | None = None
    version: str | None = None
    product_ids: tuple = ()
    promotion_ids: tuple = ()
    region: str | None = None
    channel: str | None = None


def make_product(row):
    return Product(
        product_id=get_id(row, "product_id"),
        product_name=get_text(row, "product_name"),
        category=get_text(row, "category"),
        brand=get_text(row, "brand", required=False),
    )


def make_price(row):
    return Price(
        product_id=get_id(row, "product_id"),
        price_date=get_date(row, "price_date"),
        price=get_float(row, "price", positive=True),
        currency=get_currency(row, "currency"),
        price_type=get_choice(row, "price_type", PRICE_TYPES),
        region=get_text(row, "region", required=False),
        channel=get_text(row, "channel", required=False),
    )


def make_promotion(row):
    start_date = get_date(row, "start_date")
    end_date = get_date(row, "end_date")
    if end_date < start_date:
        raise ValidationError(f"end_date {end_date} is before start_date {start_date}")

    discount_type = get_choice(row, "discount_type", DISCOUNT_TYPES)
    discount_value = get_float(row, "discount_value", positive=True)
    currency = get_currency(row, "currency", required=False)
    if discount_type == "percent" and discount_value > 100:
        raise ValidationError(f"a percent discount cannot be more than 100, got {discount_value}")
    if discount_type == "fixed_amount" and currency is None:
        raise ValidationError("currency is required when discount_type is fixed_amount")

    return Promotion(
        promotion_id=get_id(row, "promotion_id"),
        product_id=get_id(row, "product_id"),
        start_date=start_date,
        end_date=end_date,
        discount_type=discount_type,
        discount_value=discount_value,
        currency=currency,
        region=get_text(row, "region", required=False),
        channel=get_text(row, "channel", required=False),
        description=get_text(row, "description", required=False),
    )


def make_sale(row):
    units = get_int(row, "units")
    revenue = get_float(row, "revenue")
    if units == 0 and revenue > 0:
        raise ValidationError("revenue is above 0 but units is 0")

    return Sale(
        product_id=get_id(row, "product_id"),
        sale_date=get_date(row, "sale_date"),
        units=units,
        revenue=revenue,
        currency=get_currency(row, "currency"),
        cost=get_float(row, "cost", required=False),
        region=get_text(row, "region", required=False),
        channel=get_text(row, "channel", required=False),
    )


def make_competitor_price(row):
    return CompetitorPrice(
        observation_id=get_id(row, "observation_id"),
        competitor_name=get_text(row, "competitor_name"),
        competitor_product=get_text(row, "competitor_product"),
        observed_price=get_float(row, "observed_price", positive=True),
        currency=get_currency(row, "currency"),
        observation_date=get_date(row, "observation_date"),
        source=get_text(row, "source"),
        product_id=get_id(row, "product_id", required=False),
        region=get_text(row, "region", required=False),
        channel=get_text(row, "channel", required=False),
    )


def make_document(row):
    source_path = get_text(row, "source_path")
    # the path must be relative to the data folder, written with forward slashes
    if source_path.startswith("/") or "\\" in source_path or ":" in source_path \
            or ".." in source_path.split("/"):
        raise ValidationError(f"source_path '{source_path}' must be a relative path like documents/file.txt")

    return DocumentMeta(
        document_id=get_id(row, "document_id"),
        title=get_text(row, "title"),
        source_name=get_text(row, "source_name"),
        source_type=get_text(row, "source_type"),
        source_path=source_path,
        is_synthetic=get_bool(row, "is_synthetic"),
        effective_date=get_date(row, "effective_date", required=False),
        version=get_text(row, "version", required=False),
        product_ids=get_id_list(row, "product_ids"),
        promotion_ids=get_id_list(row, "promotion_ids"),
        region=get_text(row, "region", required=False),
        channel=get_text(row, "channel", required=False),
    )


# every table in one place: its record class, its row function, its required columns.
# any other column of the record class is optional.
TABLES = {
    "products": {
        "record": Product,
        "make": make_product,
        "required": ["product_id", "product_name", "category"],
    },
    "prices": {
        "record": Price,
        "make": make_price,
        "required": ["product_id", "price_date", "price", "currency", "price_type"],
    },
    "promotions": {
        "record": Promotion,
        "make": make_promotion,
        "required": ["promotion_id", "product_id", "start_date", "end_date",
                     "discount_type", "discount_value"],
    },
    "sales": {
        "record": Sale,
        "make": make_sale,
        "required": ["product_id", "sale_date", "units", "revenue", "currency"],
    },
    "competitor_prices": {
        "record": CompetitorPrice,
        "make": make_competitor_price,
        "required": ["observation_id", "competitor_name", "competitor_product",
                     "observed_price", "currency", "observation_date", "source"],
    },
    "documents": {
        "record": DocumentMeta,
        "make": make_document,
        "required": ["document_id", "title", "source_name", "source_type",
                     "source_path", "is_synthetic"],
    },
}

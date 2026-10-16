from domain_rag_copilot.schemas.loader import load_sample_data


def main():
    try:
        data = load_sample_data()
    except (ValueError, FileNotFoundError) as error:
        print(f"sample data problem: {error}")
        return 1

    for table_name, records in data.items():
        print(f"{table_name}: {len(records)} rows")
        print(f"  first row: {records[0]}")
    print("all checks passed")
    return 0


raise SystemExit(main())

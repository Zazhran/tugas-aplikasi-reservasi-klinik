def format_rupiah(nilai: int) -> str:
    return "{:,}".format(nilai).replace(",", ".")


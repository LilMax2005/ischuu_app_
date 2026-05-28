def currency(value: int) -> str:
    return f"$ {value:,.0f}".replace(",", ".")

async def resolve_gene_symbol(symbol: str) -> str:
    return f"gene:{symbol.strip().upper()}"

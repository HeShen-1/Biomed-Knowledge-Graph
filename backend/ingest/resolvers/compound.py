async def resolve_compound(name: str) -> str:
    clean = name.strip().upper()
    return f"compound:{clean}"

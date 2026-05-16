async def resolve_disease(name: str) -> str:
    clean = name.strip().lower()
    return f"disease:{clean}"

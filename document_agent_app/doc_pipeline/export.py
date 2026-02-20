import pandas as pd

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def to_txt_bytes(text: str) -> bytes:
    return (text or "").encode("utf-8")

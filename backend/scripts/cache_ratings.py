"""一次性脚本：分块导出 ratings 为 pickle 文件。"""
import sys, time
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

from backend.app import create_app
app = create_app()
db_url = app.config["SQLALCHEMY_DATABASE_URI"]
engine = create_engine(db_url)
out = Path(__file__).resolve().parents[1] / "artifacts" / "ratings_cache.csv"
out.parent.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print("Exporting to CSV (streaming, chunked)...")
with engine.connect() as conn:
    first = True
    total = 0
    for chunk in pd.read_sql(
        text("SELECT user_id, movie_id, rating, timestamp FROM ratings ORDER BY user_id, timestamp"),
        conn,
        chunksize=1_000_000,
    ):
        chunk.to_csv(out, mode="a", header=first, index=False)
        first = False
        total += len(chunk)
        print(f"  {total:,} rows ({time.time()-t0:.0f}s)")

print(f"Done: {total:,} rows in {time.time()-t0:.0f}s → {out}")

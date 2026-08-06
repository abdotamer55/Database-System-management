from database import engine
from sqlalchemy import text
from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM students"))
    print(result.scalar())
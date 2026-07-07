from fastmcp import FastMCP
import os
import aiosqlite
import asyncio

mcp = FastMCP(name="xyz")

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "expense.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as cur:

        query = """
        CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        date TEXT NOT NULL DEFAULT (date('now')),
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """

        await cur.execute(query)
            




@mcp.tool()
async def get_expense(start_date: str, end_date: str, category: str | None = None) -> dict:
    """Return all expenses between start_date and end_date, optionally filtered by category.

    Args:
        start_date: Start of the date range (YYYY-MM-DD).
        end_date: End of the date range (YYYY-MM-DD), inclusive.
        category: Optional category to filter by (e.g. food, travel). If omitted, returns all categories.
    """
    query = """
    SELECT * FROM expenses
    WHERE date BETWEEN ? AND ?
    """
    params = [start_date, end_date]

    if category:
        query += " AND category = ?"
        params.append(category)

    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(query, params) as cur:
                rows = await cur.fetchall()
                return {
                    "status": "success",
                    "count": len(rows), # type: ignore
                    "expenses": [dict(row) for row in rows],
                }
    except Exception as e:
        return {"status": "error", "message": str(e)}
        
@mcp.tool()
async def insert_expense(description: str, amount: float, category: str) -> dict:
    """Insert an expense entry into the table.

    Args:
        description: What the expense was for.
        amount: The amount spent (in your base currency).
        category: Category the expense belongs to (e.g. food, travel, bills).
    """
    query = """
    INSERT INTO expenses (description, amount, category) VALUES (?, ?, ?)
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(query, (description, amount, category))
            await db.commit()
            return {
                "status": "success",
                "id": cur.lastrowid,
                "description": description,
                "amount": amount,
                "category": category,
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    


if __name__ == "__main__":
    asyncio.run(init_db())
    mcp.run(transport="http", host="0.0.0.0", port=8000)


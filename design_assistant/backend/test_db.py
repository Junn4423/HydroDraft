"""Test script for database initialization"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test_db():
    from database.connection import init_db, check_db_connection, get_db_info
    
    print("Testing database initialization...")
    await init_db()
    
    connected = await check_db_connection()
    print(f"Database connected: {connected}")
    
    info = get_db_info()
    print(f"Database info: {info}")
    
    return connected

if __name__ == "__main__":
    result = asyncio.run(test_db())
    print(f"\nTest {'PASSED' if result else 'FAILED'}")

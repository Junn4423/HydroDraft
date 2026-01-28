"""
HydroDraft - SQLite Database Connection
Offline-first database với SQLite + aiosqlite
"""

import os
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event, text
from typing import AsyncGenerator
from pathlib import Path

from core.config import settings

# Đường dẫn database SQLite
def get_db_path() -> str:
    """Lấy đường dẫn database file"""
    data_dir = Path(settings.DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / "design_data.db")

DATABASE_PATH = get_db_path()
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

# Engine SQLite với cấu hình tối ưu
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={
        "check_same_thread": False,
    },
)

# Bật Foreign Keys cho SQLite
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    """Base class cho tất cả models"""
    pass


async def init_db():
    """Khởi tạo database và tạo bảng"""
    from .models import Base as ModelsBase
    
    print(f"Database path: {DATABASE_PATH}")
    
    # Tạo tất cả bảng
    async with engine.begin() as conn:
        await conn.run_sync(ModelsBase.metadata.create_all)
    
    print("Database tables created")
    
    # Seed dữ liệu mặc định nếu cần
    await seed_default_data()


async def seed_default_data():
    """Seed dữ liệu mặc định (templates, rules)"""
    from .models import Template, Rule
    
    async with async_session() as session:
        # Kiểm tra xem đã có dữ liệu chưa
        result = await session.execute(text("SELECT COUNT(*) FROM templates"))
        count = result.scalar()
        
        if count > 0:
            print("Default data already exists")
            return
        
            print("Seeding default data...")
        
        # Load templates từ JSON files
        templates_dir = Path(settings.TEMPLATE_DIR)
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        template = Template(
                            template_id=data.get('template_id', template_file.stem),
                            name=data.get('name', template_file.stem),
                            category=data.get('category', 'general'),
                            version=data.get('version', '1.0'),
                            data=data
                        )
                        session.add(template)
                        print(f"  Template: {template.name}")
                except Exception as e:
                    print(f"  Error loading template {template_file}: {e}")
        
        # Load rules từ JSON files
        rules_dir = Path(settings.RULES_DIR)
        if rules_dir.exists():
            for rule_file in rules_dir.glob("*.json"):
                try:
                    with open(rule_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        rule = Rule(
                            rule_id=rule_file.stem,
                            name=data.get('name', rule_file.stem),
                            version=data.get('version', '1.0.0'),
                            data=data
                        )
                        session.add(rule)
                        print(f"  Rule: {rule.name}")
                except Exception as e:
                    print(f"  Error loading rule {rule_file}: {e}")
        
        await session.commit()
        print("Default data seeding completed")


async def close_db():
    """Đóng kết nối database"""
    await engine.dispose()
    print("Database connection closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency để lấy database session"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """Kiểm tra kết nối database"""
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False


def get_db_info() -> dict:
    """Lấy thông tin database"""
    db_path = Path(DATABASE_PATH)
    return {
        "path": str(db_path),
        "exists": db_path.exists(),
        "size_mb": round(db_path.stat().st_size / (1024 * 1024), 2) if db_path.exists() else 0,
    }

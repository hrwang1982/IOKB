import asyncio
import sys
import os
from sqlalchemy import text

# Ensure app is in python path
sys.path.append(os.getcwd())

from app.core.database import init_db, async_session_maker
from loguru import logger

async def main():
    logger.info("Starting Schema Repair...")
    
    try:
        # Initialize DB connection (creates engine)
        await init_db()
        
        async with async_session_maker() as db:
            logger.info("Checking data_sources table...")
            
            # Check if column exists
            try:
                # Try to select the column
                await db.execute(text("SELECT extra_config FROM data_sources LIMIT 1"))
                logger.info("Column 'extra_config' already exists.")
            except Exception:
                # If failed, assume missing and try to add
                logger.info("Column 'extra_config' missing. Attempting to add...")
                try:
                    await db.execute(text("ALTER TABLE data_sources ADD COLUMN extra_config JSON COMMENT '额外配置'"))
                    await db.commit()
                    logger.info("Successfully added 'extra_config' column.")
                except Exception as e:
                    logger.error(f"Failed to add column: {e}")
                    # Handle case where error might be different
                    if "Duplicate column" in str(e):
                         logger.info("Column already exists (Duplicate error).")
                    else:
                        raise e
                        
    except Exception as e:
        error_msg = str(e)
        if "2003" in error_msg or "2013" in error_msg or "Name or service not known" in error_msg:
             logger.error("="*60)
             logger.error("CONNECTION FAILED")
             logger.error("Please run with MYSQL_HOST=localhost if running locally:")
             logger.error("    MYSQL_HOST=localhost python3 scripts/add_missing_column.py")
             logger.error("="*60)
        else:
            logger.error(f"Migration failed: {e}")
            raise

    logger.info("Done.")

if __name__ == "__main__":
    asyncio.run(main())

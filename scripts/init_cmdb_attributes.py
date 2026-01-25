import asyncio
import sys
import os

# Ensure app is in python path
sys.path.append(os.getcwd())

from app.core.database import init_db, async_session_maker
from app.core.cmdb.service import ci_type_service
from loguru import logger

async def main():
    logger.info("Starting CMDB Attribute Initialization...")
    
    try:
        # Initialize DB connection
        await init_db()
        
        async with async_session_maker() as db:
            logger.info("Executing init_preset_types...")
            count = await ci_type_service.init_preset_types(db)
            logger.info(f"Processed {count} CI types.")
            
    except Exception as e:
        # Check for connection error
        error_msg = str(e)
        if "2003" in error_msg or "2013" in error_msg or "Name or service not known" in error_msg:
            from app.config import settings
            logger.warning(f"Connection failed: {e}")
            
            if settings.mysql_host == "mysql":
                logger.info("Detected 'mysql' host failing. Retrying with 'localhost' (assuming local execution)...")
                
                # Re-configure engine with localhost
                # Since engine is already created in app.core.database, we need to dispose it and re-create?
                # Actually, simpler to just advise user or hack the settings if we could reload.
                # But app.core.database imports settings at module level.
                
                # Alternative: Print helpful message
                logger.error("="*60)
                logger.error("FAILED TO CONNECT TO DATABASE")
                logger.error("It seems you are running this script locally but the config points to 'mysql' (Docker hostname).")
                logger.error("Please run the command with MYSQL_HOST override:")
                logger.error("")
                logger.error("    MYSQL_HOST=localhost python3 scripts/init_cmdb_attributes.py")
                logger.error("="*60)
                return
        
        logger.error(f"Initialization failed: {e}")
        raise

    logger.info("Done.")

if __name__ == "__main__":
    asyncio.run(main())

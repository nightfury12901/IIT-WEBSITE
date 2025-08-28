#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

from database import SupabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_unknown_years():
    """Fix Unknown years in the database"""
    try:
        db = SupabaseManager()
        conn = db.get_connection()
        
        try:
            with conn.cursor() as cur:
                # Count publications with Unknown/invalid years
                cur.execute("""
                    SELECT COUNT(*) as count 
                    FROM publications 
                    WHERE year IS NULL OR year = 0
                """)
                count_before = cur.fetchone()['count']
                logger.info(f"Found {count_before} publications with NULL/0 years")
                
                # You can also check for any string years that might cause issues
                cur.execute("""
                    SELECT COUNT(*) as count 
                    FROM publications 
                    WHERE year < 1900 OR year > 2030
                """)
                invalid_years = cur.fetchone()['count']
                logger.info(f"Found {invalid_years} publications with invalid years")
                
                # Show some examples
                cur.execute("""
                    SELECT title, year 
                    FROM publications 
                    WHERE year IS NULL 
                    LIMIT 5
                """)
                examples = cur.fetchall()
                
                logger.info("Example publications with NULL years:")
                for pub in examples:
                    logger.info(f"  - {pub['title'][:50]}... (year: {pub['year']})")
                
                logger.info("Database year analysis complete")
                return True
                
        finally:
            db.put_connection(conn)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    fix_unknown_years()

#!/usr/bin/env python3
"""
Bulk sync ALL 1422+ publications from Google Scholar to PostgreSQL database.
This script will take 60-90 minutes due to Google Scholar rate limiting.
"""

from dotenv import load_dotenv
load_dotenv()

import os
import time
import logging
from datetime import datetime
from database import SupabaseManager
from scholar_fetcher import ScholarFetcher

# Configure logging for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bulk_sync_all.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def sync_all_publications():
    """Sync ALL publications from Google Scholar"""
    
    print("=" * 60)
    print("Dr. Abhishek Dixit - COMPLETE Publications Sync")
    print("=" * 60)
    print("This will fetch ALL 1422+ publications from Google Scholar")
    print("Expected time: 60-90 minutes")
    print("Progress will be logged every 50 publications")
    print("=" * 60)
    
    try:
        # Initialize database
        logger.info("INIT: Connecting to PostgreSQL database...")
        db = SupabaseManager()
        logger.info("SUCCESS: Database connection established")
        
        # Initialize Scholar fetcher
        logger.info("INIT: Setting up Google Scholar fetcher...")
        fetcher = ScholarFetcher()
        logger.info("SUCCESS: Scholar fetcher ready")
        
        # Fetch ALL data (this is the long part)
        logger.info("STARTING: Fetching ALL publications from Google Scholar...")
        logger.info("WARNING: This will take 60-90 minutes due to rate limiting")
        
        start_fetch_time = time.time()
        scholar_data = fetcher.fetch_scholar_data('CjJ84BwAAAAJ')
        fetch_duration = int((time.time() - start_fetch_time) / 60)
        
        if not scholar_data:
            logger.error("ERROR: Failed to fetch Scholar data")
            return False
        
        logger.info(f"SUCCESS: Fetched {scholar_data['total_publications']} publications in {fetch_duration} minutes")
        print(f"\nFetch completed: {scholar_data['total_publications']} publications in {fetch_duration} minutes")
        
        # Flatten publications for database storage
        all_publications = []
        for year, pubs in scholar_data['publications_by_year'].items():
            for pub in pubs:
                pub['year'] = int(year) if year.isdigit() else None
                all_publications.append(pub)
        
        logger.info(f"DATABASE: Inserting {len(all_publications)} publications...")
        print(f"Inserting {len(all_publications)} publications into database...")
        
        # Insert publications into PostgreSQL
        insert_start = time.time()
        success = db.bulk_insert_publications(all_publications)
        insert_duration = int((time.time() - insert_start))
        
        if success:
            # Update profile
            logger.info("PROFILE: Updating scholar profile...")
            db.update_profile({
                'name': scholar_data['profile']['name'],
                'affiliation': scholar_data['profile']['affiliation'],
                'scholar_url': scholar_data['profile']['scholar_url'],
                'total_citations': scholar_data['profile']['total_citations'],
                'h_index': scholar_data['profile']['h_index'],
                'i10_index': scholar_data['profile']['i10_index'],
                'total_publications': scholar_data['total_publications']
            })
            
            logger.info("SUCCESS: Complete sync finished!")
            
            # Print final summary
            print("\n" + "=" * 60)
            print("SYNC COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print(f"Total Publications: {len(all_publications)}")
            print(f"Total Citations: {scholar_data['profile']['total_citations']}")
            print(f"H-Index: {scholar_data['profile']['h_index']}")
            print(f"i10-Index: {scholar_data['profile']['i10_index']}")
            print(f"Database Insert Time: {insert_duration} seconds")
            print(f"Total Fetch Time: {fetch_duration} minutes")
            print("=" * 60)
            print("Your publications website is now ready with ALL data!")
            print("Visit: http://localhost:5000")
            print("=" * 60)
            
            return True
        else:
            logger.error("ERROR: Failed to insert publications into database")
            return False
            
    except KeyboardInterrupt:
        logger.info("INTERRUPTED: Sync cancelled by user")
        print("\nSync cancelled by user (Ctrl+C)")
        return False
        
    except Exception as error:
        logger.error(f"ERROR: Bulk sync failed: {str(error)}")
        import traceback
        logger.error(f"TRACEBACK: {traceback.format_exc()}")
        return False

def verify_sync():
    """Verify the sync worked correctly"""
    try:
        db = SupabaseManager()
        conn = db.get_connection()
        
        try:
            with conn.cursor() as cur:
                # Count total publications
                cur.execute("SELECT COUNT(*) as total FROM publications")
                total = cur.fetchone()['total']
                
                # Count by year
                cur.execute("""
                    SELECT year, COUNT(*) as count 
                    FROM publications 
                    WHERE year IS NOT NULL 
                    GROUP BY year 
                    ORDER BY year DESC 
                    LIMIT 10
                """)
                years = cur.fetchall()
                
                # Get profile
                cur.execute("SELECT * FROM scholar_profile ORDER BY last_updated DESC LIMIT 1")
                profile = cur.fetchone()
                
                print("\n" + "=" * 50)
                print("DATABASE VERIFICATION")
                print("=" * 50)
                print(f"Total Publications in DB: {total}")
                
                if profile:
                    print(f"Scholar Name: {profile['name']}")
                    print(f"Total Citations: {profile['total_citations']}")
                    print(f"H-Index: {profile['h_index']}")
                
                print("\nPublications by Year (Top 10):")
                for year_data in years:
                    print(f"  {year_data['year']}: {year_data['count']} publications")
                
                print("=" * 50)
                
                return total > 1400  # Should have 1422+ publications
                
        finally:
            db.put_connection(conn)
            
    except Exception as e:
        print(f"Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting complete publications sync...")
    
    # Confirmation
    confirm = input("\nThis will fetch ALL 1422+ publications (takes 60-90 minutes). Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Sync cancelled.")
        exit(0)
    
    # Start sync
    start_time = time.time()
    success = sync_all_publications()
    total_duration = int((time.time() - start_time) / 60)
    
    if success:
        print(f"\nComplete sync finished in {total_duration} minutes")
        
        # Verify the sync
        print("\nVerifying sync...")
        if verify_sync():
            print(" Verification successful - all data synced correctly!")
        else:
            print("  Verification warning - please check the data")
    else:
        print(f"\nSync failed after {total_duration} minutes")
        print("Check bulk_sync_all.log for detailed error information")

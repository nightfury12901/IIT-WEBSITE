import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
import os
from typing import List, Dict, Optional
import logging
import atexit

logger = logging.getLogger(__name__)

class SupabaseManager:
    def __init__(self):
        # Use direct PostgreSQL connection with transaction pooling
        self.db_url = os.environ.get('DATABASE_URL')
        
        if not self.db_url:
            raise ValueError("DATABASE_URL must be set for direct database connection")
        
        # Create connection pool for better performance
        try:
            self.connection_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=self.db_url,
                cursor_factory=RealDictCursor
            )
            logger.info("✅ PostgreSQL connection pool initialized")
            
            # Register cleanup function
            atexit.register(self.close_all_connections)
            
        except Exception as e:
            logger.error(f"❌ Failed to create connection pool: {e}")
            raise

    def get_connection(self):
        """Get connection from pool"""
        try:
            return self.connection_pool.getconn()
        except Exception as e:
            logger.error(f"❌ Error getting connection from pool: {e}")
            raise

    def put_connection(self, conn):
        """Return connection to pool"""
        try:
            self.connection_pool.putconn(conn)
        except Exception as e:
            logger.error(f"❌ Error returning connection to pool: {e}")

    def close_all_connections(self):
        """Close all connections in pool"""
        if hasattr(self, 'connection_pool'):
            self.connection_pool.closeall()
            logger.info("🔒 All database connections closed")

    def get_publications(self, page: int = 1, per_page: int = 5, year_filter: str = None) -> Dict:
        """Get publications with pagination and optional year filter"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Build WHERE clause
                where_clause = ""
                params = []
                
                if year_filter and year_filter != 'all':
                    if year_filter == 'Unknown':
                        where_clause = "WHERE year IS NULL"
                    else:
                        where_clause = "WHERE year = %s"
                        params.append(int(year_filter))
                
                # Get total count
                count_query = f"SELECT COUNT(*) as total FROM publications {where_clause}"
                cur.execute(count_query, params)
                total = cur.fetchone()['total']
                
                # Get paginated results - Handle NULL years properly
                offset = (page - 1) * per_page
                query = f"""
                    SELECT id, title, authors, venue, 
                        COALESCE(CAST(year AS TEXT), 'Unknown') as year, 
                        citations, scholar_url, pub_number
                    FROM publications 
                    {where_clause}
                    ORDER BY year DESC NULLS LAST, citations DESC 
                    LIMIT %s OFFSET %s
                """
                params.extend([per_page, offset])
                
                cur.execute(query, params)
                publications = cur.fetchall()
                
                return {
                    'publications': [dict(pub) for pub in publications],
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total,
                        'total_pages': (total + per_page - 1) // per_page,
                        'has_next': offset + per_page < total
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Error fetching publications: {e}")
            raise
        finally:
            if conn:
                self.put_connection(conn)


    def get_all_publications(self) -> List[Dict]:
        """Get all publications for admin operations"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                query = """
                    SELECT * FROM publications 
                    ORDER BY year DESC NULLS LAST, citations DESC
                """
                cur.execute(query)
                publications = cur.fetchall()
                
                return [dict(pub) for pub in publications]
                
        except Exception as e:
            logger.error(f"❌ Error fetching all publications: {e}")
            raise
        finally:
            if conn:
                self.put_connection(conn)

    def get_profile(self) -> Dict:
        """Get scholar profile"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM scholar_profile ORDER BY last_updated DESC LIMIT 1")
                result = cur.fetchone()
                
                if result:
                    return dict(result)
                else:
                    # Return default profile if none exists
                    return {
                        'name': 'Dr. Abhishek Dixit',
                        'affiliation': 'Indian Institute of Technology Delhi',
                        'scholar_url': 'https://scholar.google.co.in/citations?user=CjJ84BwAAAAJ&hl=en',
                        'total_citations': 0,
                        'h_index': 0,
                        'i10_index': 0,
                        'total_publications': 0
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error fetching profile: {e}")
            raise
        finally:
            if conn:
                self.put_connection(conn)

    def update_profile(self, profile_data: Dict) -> bool:
        """Update or insert scholar profile"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Check if profile exists
                cur.execute("SELECT id FROM scholar_profile LIMIT 1")
                existing = cur.fetchone()
                
                if existing:
                    # Update existing profile
                    update_query = """
                        UPDATE scholar_profile 
                        SET name = %s, affiliation = %s, scholar_url = %s, 
                            total_citations = %s, h_index = %s, i10_index = %s,
                            total_publications = %s, last_updated = NOW()
                        WHERE id = %s
                    """
                    cur.execute(update_query, (
                        profile_data.get('name'),
                        profile_data.get('affiliation'),
                        profile_data.get('scholar_url'),
                        profile_data.get('total_citations', 0),
                        profile_data.get('h_index', 0),
                        profile_data.get('i10_index', 0),
                        profile_data.get('total_publications', 0),
                        existing['id']
                    ))
                else:
                    # Insert new profile
                    insert_query = """
                        INSERT INTO scholar_profile 
                        (name, affiliation, scholar_url, total_citations, h_index, i10_index, total_publications)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cur.execute(insert_query, (
                        profile_data.get('name'),
                        profile_data.get('affiliation'),
                        profile_data.get('scholar_url'),
                        profile_data.get('total_citations', 0),
                        profile_data.get('h_index', 0),
                        profile_data.get('i10_index', 0),
                        profile_data.get('total_publications', 0)
                    ))
                
                conn.commit()
                logger.info("✅ Profile updated successfully")
                return True
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ Error updating profile: {e}")
            return False
        finally:
            if conn:
                self.put_connection(conn)

    def bulk_insert_publications(self, publications: List[Dict]) -> bool:
        """Bulk insert publications (for initial data load)"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Clear existing publications
                cur.execute("DELETE FROM publications")
                logger.info("🗑️ Cleared existing publications")
                
                # Prepare insert query
                insert_query = """
                    INSERT INTO publications 
                    (title, authors, venue, year, citations, scholar_url, pub_number)
                    VALUES %s
                """
                
                # Prepare data for bulk insert
                values = []
                for pub in publications:
                    values.append((
                        pub.get('title', ''),
                        pub.get('authors', ''),
                        pub.get('venue', ''),
                        pub.get('year') if pub.get('year') and str(pub.get('year')).isdigit() else None,
                        pub.get('citations', 0),
                        pub.get('scholar_url', ''),
                        pub.get('pub_number', 0)
                    ))
                
                # Execute bulk insert in batches
                from psycopg2.extras import execute_values
                batch_size = 100
                
                for i in range(0, len(values), batch_size):
                    batch = values[i:i + batch_size]
                    execute_values(cur, insert_query, batch, template=None, page_size=batch_size)
                    logger.info(f"✅ Inserted batch {i//batch_size + 1}: {len(batch)} publications")
                
                conn.commit()
                logger.info(f"✅ All {len(publications)} publications inserted successfully")
                return True
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ Error bulk inserting publications: {e}")
            return False
        finally:
            if conn:
                self.put_connection(conn)

    def get_years_with_counts(self) -> Dict[str, int]:
        """Get all years with publication counts"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                query = """
                    SELECT 
                        CASE 
                            WHEN year IS NULL THEN 'Unknown'
                            ELSE CAST(year AS TEXT)
                        END as year,
                        COUNT(*) as count
                    FROM publications 
                    GROUP BY year 
                    ORDER BY 
                        CASE WHEN year IS NULL THEN 1 ELSE 0 END,
                        year DESC
                """
                cur.execute(query)
                results = cur.fetchall()
                
                return {row['year']: row['count'] for row in results}
                
        except Exception as e:
            logger.error(f"❌ Error fetching year counts: {e}")
            return {}
        finally:
            if conn:
                self.put_connection(conn)


    def search_publications(self, query: str, page: int = 1, per_page: int = 10) -> Dict:
        """Search publications by title, authors, or venue"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                search_query = f"%{query}%"
                
                # Count total results
                count_sql = """
                    SELECT COUNT(*) as total FROM publications 
                    WHERE title ILIKE %s OR authors ILIKE %s OR venue ILIKE %s
                """
                cur.execute(count_sql, (search_query, search_query, search_query))
                total = cur.fetchone()['total']
                
                # Get paginated results
                offset = (page - 1) * per_page
                search_sql = """
                    SELECT * FROM publications 
                    WHERE title ILIKE %s OR authors ILIKE %s OR venue ILIKE %s
                    ORDER BY year DESC NULLS LAST, citations DESC
                    LIMIT %s OFFSET %s
                """
                cur.execute(search_sql, (search_query, search_query, search_query, per_page, offset))
                results = cur.fetchall()
                
                return {
                    'publications': [dict(pub) for pub in results],
                    'query': query,
                    'total': total,
                    'page': page,
                    'per_page': per_page
                }
                
        except Exception as e:
            logger.error(f"❌ Error searching publications: {e}")
            raise
        finally:
            if conn:
                self.put_connection(conn)

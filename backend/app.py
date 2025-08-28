from dotenv import load_dotenv
# Load environment variables FIRST - before any other imports
load_dotenv()

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            static_folder='../frontend',
            static_url_path='')

# Enable CORS
CORS(app)

# Set secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'scholar-api-secret-key-2024'

# Debug: Verify DATABASE_URL is loaded
db_url = os.environ.get('DATABASE_URL')
logger.info(f"✅ DATABASE_URL loaded: {db_url[:50]}..." if db_url else "❌ DATABASE_URL not found")

# Initialize Database with connection pooling
db = None
try:
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is missing")
    
    logger.info("🔄 Initializing database connection pool...")
    from database import SupabaseManager
    db = SupabaseManager()
    logger.info("✅ PostgreSQL connection pool established successfully")
    
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    logger.error(f"💡 Error type: {type(e).__name__}")
    import traceback
    logger.error(f"🔍 Full traceback:\n{traceback.format_exc()}")
    db = None

@app.route('/')
def home():
    """Serve the publications page"""
    return send_from_directory('../frontend', 'publications.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, images)"""
    try:
        return send_from_directory('../frontend', filename)
    except FileNotFoundError:
        return f"File {filename} not found", 404

@app.route('/api/publications')
def get_publications():
    """Get publications with pagination - SUPER FAST from PostgreSQL"""
    if not db:
        logger.error("🚨 Database not available - connection failed during startup")
        return jsonify({
            'error': 'Database not available',
            'message': 'Database connection failed during server startup. Check server logs.',
            'suggestion': 'Restart the server and check database credentials'
        }), 500
    
    try:
        start_time = time.time()
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 5))
        year_filter = request.args.get('year', 'all')
        
        logger.info(f"📊 Fast DB request - page {page}, per_page {per_page}, year {year_filter}")
        
        # Get publications from database
        result = db.get_publications(page=page, per_page=per_page, year_filter=year_filter)
        
        # Get profile (cached in DB)
        profile = db.get_profile()
        
        response_time = int((time.time() - start_time) * 1000)
        logger.info(f"⚡ Database response time: {response_time}ms")
        
        return jsonify({
            'profile': profile if page == 1 else None,
            'publications': result['publications'],
            'pagination': result['pagination'],
            'response_time': response_time,
            'source': 'postgresql_direct_connection',
            'last_updated': profile.get('last_updated', datetime.now().isoformat())
        })
        
    except Exception as error:
        logger.error(f"❌ Publications API error: {str(error)}")
        return jsonify({
            'error': str(error),
            'message': 'Failed to fetch publications from database'
        }), 500

@app.route('/api/test-db')
def test_database():
    """Test direct database connection"""
    if not db:
        return jsonify({
            'status': 'error',
            'message': 'Database not initialized - connection failed during startup',
            'suggestion': 'Check server logs for database connection errors'
        }), 500
    
    try:
        # Try a simple query
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as total FROM publications")
                result = cur.fetchone()
                
                cur.execute("SELECT version() as db_version")
                version = cur.fetchone()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Direct PostgreSQL connection working!',
                    'connection_type': 'direct_postgresql_transaction_pooling',
                    'total_publications': result['total'],
                    'database_version': version['db_version'][:50] + '...'
                })
        finally:
            db.put_connection(conn)
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'Database test failed: {str(e)}'
        }), 500

@app.route('/api/years')
def get_years():
    """Get all years with publication counts"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        year_counts = db.get_years_with_counts()
        return jsonify(year_counts)
    except Exception as error:
        return jsonify({'error': str(error)}), 500

@app.route('/api/search')
def search_publications():
    """Search publications"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        query = request.args.get('q', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        if not query:
            return jsonify({'error': 'Search query required'}), 400
        
        result = db.search_publications(query, page, per_page)
        return jsonify(result)
    except Exception as error:
        return jsonify({'error': str(error)}), 500

@app.route('/api/admin/sync-scholar', methods=['POST'])
def sync_scholar_data():
    """Admin endpoint to sync data from Google Scholar to PostgreSQL"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        from scholar_fetcher import ScholarFetcher
        
        logger.info("🔄 Starting Scholar data sync to PostgreSQL...")
        
        fetcher = ScholarFetcher()
        scholar_data = fetcher.fetch_scholar_data('CjJ84BwAAAAJ')
        
        if not scholar_data:
            return jsonify({'error': 'Failed to fetch Scholar data'}), 500
        
        # Flatten publications for database storage
        all_publications = []
        for year, pubs in scholar_data['publications_by_year'].items():
            for pub in pubs:
                pub['year'] = int(year) if year.isdigit() else None
                all_publications.append(pub)
        
        # Insert publications into PostgreSQL
        success = db.bulk_insert_publications(all_publications)
        
        if success:
            # Update profile
            db.update_profile({
                'name': scholar_data['profile']['name'],
                'affiliation': scholar_data['profile']['affiliation'],
                'scholar_url': scholar_data['profile']['scholar_url'],
                'total_citations': scholar_data['profile']['total_citations'],
                'h_index': scholar_data['profile']['h_index'],
                'i10_index': scholar_data['profile']['i10_index'],
                'total_publications': scholar_data['total_publications']
            })
            
            logger.info("✅ Scholar data synced to PostgreSQL successfully")
            return jsonify({
                'message': 'Data synced successfully',
                'total_publications': len(all_publications)
            })
        else:
            return jsonify({'error': 'Failed to sync data'}), 500
            
    except Exception as error:
        logger.error(f"❌ Sync error: {str(error)}")
        return jsonify({'error': str(error)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("🚀 Fast PostgreSQL Scholar API Server starting...")
    print(f"📚 Publications page: http://localhost:{port}")
    print(f"⚡ Database: PostgreSQL Direct Connection with Transaction Pooling")
    print(f"🔗 Test DB: http://localhost:{port}/api/test-db")
    
    if db:
        print("✅ Database connection ready")
    else:
        print("❌ Database connection failed - check logs above")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

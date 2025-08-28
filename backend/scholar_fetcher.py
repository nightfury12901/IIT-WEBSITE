import time
import re
from datetime import datetime
from scholarly import scholarly
import logging

logger = logging.getLogger(__name__)

class ScholarFetcher:
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 2.0
        self.max_publications = None  # Remove limit to get ALL publications
    
    def fetch_scholar_data(self, scholar_id):
        """Fetch ALL scholar data with retry logic"""
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"ATTEMPT {attempt}/{self.max_retries}: Fetching scholar data...")
                
                # Add random delay to avoid rate limiting
                delay = self.base_delay + (attempt - 1) * 1.0
                time.sleep(delay)
                
                # Search for author
                author = scholarly.search_author_id(scholar_id)
                author_filled = scholarly.fill(author)
                
                logger.info(f"AUTHOR FOUND: {author_filled.get('name', 'Unknown')}")
                total_pubs = len(author_filled.get('publications', []))
                logger.info(f"TOTAL PUBLICATIONS: {total_pubs}")
                
                # Process ALL publications (no limit)
                publications = self._process_all_publications(author_filled.get('publications', []))
                
                # Create final data structure
                result = self._format_scholar_data(author_filled, publications, scholar_id)
                
                logger.info(f"SUCCESS: Fetched data for {result['profile']['name']}")
                logger.info(f"STATS: {result['total_publications']} pubs, {result['profile']['total_citations']} citations, h-index: {result['profile']['h_index']}")
                
                return result
                
            except Exception as error:
                logger.error(f"ERROR: Attempt {attempt} failed: {str(error)}")
                
                if attempt == self.max_retries:
                    logger.error(f"FAILED: Could not fetch scholar data after {self.max_retries} attempts")
                    return None
                
                # Exponential backoff
                backoff_delay = (2 ** attempt) + time.time() % 1
                logger.info(f"WAITING: {backoff_delay:.1f}s before retry...")
                time.sleep(backoff_delay)
        
        return None
    
    def _process_all_publications(self, publications):
        """Process ALL publications with rate limiting"""
        processed_pubs = []
        total_pubs = len(publications)  # Process ALL publications
        
        logger.info(f"PROCESSING: {total_pubs} publications (this will take 60-90 minutes)")
        
        for i, pub in enumerate(publications):
            try:
                # Progress update every 50 publications
                if (i + 1) % 50 == 0 or i == 0:
                    logger.info(f"PROGRESS: Processing {i + 1}/{total_pubs} publications ({((i+1)/total_pubs)*100:.1f}%)")
                
                # Fill publication details
                pub_filled = scholarly.fill(pub)
                pub_data = pub_filled.get('bib', {})
                
                # Extract and clean data
                title = pub_data.get('title', 'Unknown Title')
                authors = pub_data.get('author', '')
                venue = pub_data.get('venue', '')
                year = str(pub_data.get('pub_year', 'Unknown'))
                citations = pub_filled.get('num_citations', 0)
                scholar_url = pub_filled.get('pub_url', '')
                
                # Bold the author name in authors list
                authors = self._highlight_author_name(authors)
                
                processed_pubs.append({
                    'title': title,
                    'authors': authors,
                    'venue': venue,
                    'year': year,
                    'citations': citations,
                    'scholar_url': scholar_url,
                    'pub_number': i + 1
                })
                
                # Rate limiting delay (important to avoid blocks)
                time.sleep(2.5 + (time.time() % 1))  # 2.5-3.5 second delay
                
            except Exception as pub_error:
                logger.warning(f"WARNING: Error processing publication {i + 1}: {str(pub_error)}")
                continue
        
        logger.info(f"COMPLETED: Processed {len(processed_pubs)} out of {total_pubs} publications")
        return processed_pubs
    
    def _highlight_author_name(self, authors):
        """Highlight Dr. Abhishek Dixit's name in author list"""
        if not authors:
            return authors
        
        # Patterns to match
        patterns = [
            r'\bA Dixit\b',
            r'\bAbhishek Dixit\b',
            r'\bA\. Dixit\b'
        ]
        
        for pattern in patterns:
            authors = re.sub(pattern, '<strong>\\g<0></strong>', authors, flags=re.IGNORECASE)
        
        return authors
    
    def _format_scholar_data(self, author_filled, publications, scholar_id):
        """Format the final scholar data structure"""
        
        # Sort publications by year (descending)
        publications.sort(key=lambda x: int(x['year']) if x['year'].isdigit() else 0, reverse=True)
        
        # Group by year
        publications_by_year = {}
        for pub in publications:
            year = pub['year']
            if year not in publications_by_year:
                publications_by_year[year] = []
            publications_by_year[year].append(pub)
        
        return {
            'profile': {
                'name': author_filled.get('name', 'Dr. Abhishek Dixit'),
                'affiliation': author_filled.get('affiliation', ''),
                'scholar_url': f"https://scholar.google.co.in/citations?user={scholar_id}&hl=en",
                'total_citations': author_filled.get('citedby', 0),
                'h_index': author_filled.get('hindex', 0),
                'i10_index': author_filled.get('i10index', 0)
            },
            'publications_by_year': publications_by_year,
            'total_publications': len(publications),
            'last_updated': datetime.now().isoformat()
        }

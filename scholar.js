class ScholarPublications {
    constructor() {
        this.publications = {};
        this.currentFilter = 'all';
        this.scholarData = null;
        this.apiBaseUrl = '/api';
        this.init();
    }

    async init() {
        try {
            this.setupActionButtons();
            await this.loadScholarData();
            this.hideLoading();
            this.renderPublications();
            this.setupFilters();
        } catch (error) {
            console.error('Error initializing publications:', error);
            this.showError(error);
        }
    }

    setupActionButtons() {
        const refreshBtn = document.getElementById('refresh-btn');
        const clearCacheBtn = document.getElementById('clear-cache-btn');

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }

        if (clearCacheBtn) {
            clearCacheBtn.addEventListener('click', () => this.clearCache());
        }
    }

    async loadScholarData() {
        try {
            this.showLoading();
            console.log('🔄 Loading scholar data from Python backend...');
            
            const startTime = Date.now();
            const response = await fetch(`${this.apiBaseUrl}/scholar-realtime`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const responseTime = Date.now() - startTime;
            console.log(`⏱️ Python API response time: ${responseTime}ms`);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('✅ Scholar data loaded successfully from Python backend');
            console.log('📊 Data source:', data.cached ? 'Cache' : 'Fresh from Scholar');
            
            this.scholarData = data;
            this.publications = data.publications_by_year || {};
            
            this.updateProfileHeader(data.profile, {
                cached: data.cached,
                stale: data.stale,
                responseTime: data.response_time || responseTime
            });
            this.updateLastUpdated(data.last_updated);
            
        } catch (error) {
            console.error('❌ Error loading scholar data from Python backend:', error);
            throw error;
        }
    }

    updateProfileHeader(profile, metadata = {}) {
        const elements = {
            'scholar-name': profile.name || 'Dr. Abhishek Dixit',
            'scholar-affiliation': profile.affiliation || '',
            'total-pubs': this.scholarData.total_publications || 0,
            'total-citations': profile.total_citations || 0,
            'h-index': profile.h_index || 0,
            'i10-index': profile.i10_index || 0
        };

        // Update elements safely
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });

        // Update scholar link
        const scholarLink = document.getElementById('scholar-link');
        if (scholarLink && profile.scholar_url) {
            scholarLink.href = profile.scholar_url;
        }
        
        // Update metadata
        const dataSource = document.getElementById('data-source');
        const responseTime = document.getElementById('response-time');
        
        if (dataSource) {
            if (metadata.cached) {
                dataSource.textContent = metadata.stale ? '📦 Cached (Stale)' : '⚡ Cached';
                dataSource.className = 'data-source cached';
            } else {
                dataSource.textContent = '🔄 Fresh from Scholar';
                dataSource.className = 'data-source fresh';
            }
        }
        
        if (responseTime && metadata.responseTime) {
            responseTime.textContent = `${Math.round(metadata.responseTime)}ms`;
        }
        
        // Show profile section
        const profileSection = document.getElementById('scholar-profile');
        const actionButtons = document.getElementById('action-buttons');
        if (profileSection) profileSection.style.display = 'block';
        if (actionButtons) actionButtons.style.display = 'flex';
    }

    updateLastUpdated(timestamp) {
        if (!timestamp) return;
        
        const date = new Date(timestamp);
        const formattedDate = date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const updateTime = document.getElementById('update-time');
        const lastUpdated = document.getElementById('last-updated');
        
        if (updateTime) updateTime.textContent = formattedDate;
        if (lastUpdated) lastUpdated.style.display = 'block';
    }

    renderPublications() {
        const container = document.getElementById('publications-container');
        if (!container) return;
        
        container.innerHTML = '';

        if (!this.publications || Object.keys(this.publications).length === 0) {
            container.innerHTML = '<p class="no-publications">No publications found.</p>';
            return;
        }

        const years = Object.keys(this.publications).sort((a, b) => {
            if (a === 'Unknown' || b === 'Unknown') return a === 'Unknown' ? 1 : -1;
            return parseInt(b) - parseInt(a);
        });

        years.forEach(year => {
            if (this.currentFilter !== 'all' && this.currentFilter !== year) return;
            
            const yearSection = this.createYearSection(year, this.publications[year]);
            container.appendChild(yearSection);
        });
    }

    createYearSection(year, publications) {
        const yearDiv = document.createElement('div');
        yearDiv.className = 'year-section';
        yearDiv.setAttribute('data-year', year);

        const yearHeader = document.createElement('h3');
        yearHeader.className = 'year-header';
        yearHeader.textContent = `${year} (${publications.length} publications)`;
        yearDiv.appendChild(yearHeader);

        publications.forEach((pub, index) => {
            const pubItem = this.createPublicationItem(pub, index + 1);
            yearDiv.appendChild(pubItem);
        });

        return yearDiv;
    }

    createPublicationItem(pub, index) {
        const pubDiv = document.createElement('div');
        pubDiv.className = 'publication-item gallery-image';
        pubDiv.setAttribute('data-category', pub.year);

        const title = pub.title || 'Unknown Title';
        const authors = pub.authors || 'Unknown Authors';
        const venue = pub.venue || 'Unknown Venue';
        const citations = pub.citations || 0;
        const year = pub.year || 'Unknown';
        const scholarUrl = pub.scholar_url || '';

        pubDiv.innerHTML = `
            <div class="publication-number">[${pub.pub_number || index}]</div>
            <div class="publication-content">
                <h4>${scholarUrl ? `<a href="${scholarUrl}" target="_blank">${title}</a>` : title}</h4>
                <p class="authors">${authors}</p>
                <p class="journal">${venue}</p>
                <div class="publication-meta">
                    <span class="citation-count">Citations: ${citations}</span>
                    <span class="pub-year">${year}</span>
                </div>
                <div class="publication-links">
                    ${scholarUrl ? `<a href="${scholarUrl}" target="_blank" class="pub-link">Google Scholar</a>` : ''}
                </div>
            </div>
        `;

        return pubDiv;
    }

    setupFilters() {
        const filtersContainer = document.getElementById('year-filters');
        if (!filtersContainer || !this.publications) return;
        
        const years = Object.keys(this.publications).sort((a, b) => {
            if (a === 'Unknown' || b === 'Unknown') return a === 'Unknown' ? 1 : -1;
            return parseInt(b) - parseInt(a);
        });

        // Keep the "All Years" button
        const allButton = filtersContainer.querySelector('[data-filter="all"]');
        if (allButton) {
            // Clear container but keep the "All Years" button
            filtersContainer.innerHTML = '';
            filtersContainer.appendChild(allButton);
            
            // Add event listener to "All Years" button
            allButton.addEventListener('click', () => this.filterByYear('all'));
        }

        // Add year-specific filter buttons
        years.forEach(year => {
            const filterBtn = document.createElement('button');
            filterBtn.className = 'filter-btn';
            filterBtn.setAttribute('data-filter', year);
            filterBtn.textContent = `${year} (${this.publications[year].length})`;
            filterBtn.addEventListener('click', () => this.filterByYear(year));
            filtersContainer.appendChild(filterBtn);
        });

        filtersContainer.style.display = 'flex';
    }

    filterByYear(year) {
        this.currentFilter = year;
        
        // Update active button
        document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        const activeBtn = document.querySelector(`[data-filter="${year}"]`);
        if (activeBtn) activeBtn.classList.add('active');
        
        // Re-render publications
        this.renderPublications();
    }

    async refreshData() {
        try {
            const refreshBtn = document.getElementById('refresh-btn');
            if (refreshBtn) {
                refreshBtn.disabled = true;
                refreshBtn.textContent = '🔄 Refreshing...';
            }
            
            await this.clearCache();
            await this.loadScholarData();
            this.hideLoading();
            this.renderPublications();
            this.setupFilters();
            
            console.log('✅ Data refreshed successfully');
            
        } catch (error) {
            console.error('❌ Error refreshing data:', error);
            this.showError(error);
        } finally {
            const refreshBtn = document.getElementById('refresh-btn');
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.textContent = '🔄 Refresh Publications';
            }
        }
    }

    async clearCache() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/clear-cache`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                console.log('🗑️ Python backend cache cleared successfully');
            }
        } catch (error) {
            console.warn('⚠️ Could not clear Python backend cache:', error);
        }
    }

    showLoading() {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.style.display = 'block';
        }
    }

    hideLoading() {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    showError(error) {
        const container = document.getElementById('publications-container');
        if (container) {
            container.innerHTML = `
                <div class="error-message">
                    <h3>⚠️ Unable to load publications</h3>
                    <p><strong>Error:</strong> ${error.message}</p>
                    <p>This could be due to:</p>
                    <ul>
                        <li>Google Scholar rate limiting</li>
                        <li>Network connectivity issues</li>
                        <li>Python backend server issues</li>
                    </ul>
                    <div class="error-actions">
                        <button onclick="location.reload()" class="btn btn-primary">Try Again</button>
                        <a href="https://scholar.google.co.in/citations?user=CjJ84BwAAAAJ&hl=en" target="_blank" class="btn btn-secondary">
                            Visit Google Scholar Directly
                        </a>
                    </div>
                </div>
            `;
        }
        this.hideLoading();
    }
}

// Global function for API status checking
async function checkApiStatus() {
    try {
        const response = await fetch('/api/cache-status');
        const data = await response.json();
        
        const cacheInfo = document.getElementById('cache-info');
        const apiStatus = document.getElementById('api-status');
        
        if (cacheInfo) {
            cacheInfo.textContent = `${data.cache_size}/${data.max_size} items`;
        }
        
        if (apiStatus) {
            apiStatus.style.display = 'block';
        }
        
        console.log('🐍 Python API Cache Status:', data);
    } catch (error) {
        console.error('Error checking API status:', error);
        alert('Could not connect to Python backend');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ScholarPublications();
});

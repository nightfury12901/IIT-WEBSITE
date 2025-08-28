// Add this to your back.js file or create a separate publications.js file

document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const yearSections = document.querySelectorAll('.year-section');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filterValue = this.getAttribute('data-filter');
            
            // Remove active class from all buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            
            // Filter year sections
            yearSections.forEach(section => {
                const sectionYear = section.getAttribute('data-year');
                
                if (filterValue === 'all') {
                    section.style.display = 'block';
                } else if (filterValue === sectionYear) {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            });
        });
    });
});

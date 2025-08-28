document.addEventListener('DOMContentLoaded', () => {
    const gradientSpot = document.getElementById('gradient-spot');
    const galleryImages = document.querySelectorAll('.gallery-image');

    // Enhanced parameters for better detection
    let mouseX = 0;
    let mouseY = 0;
    let currentX = 0;
    let currentY = 0;
    let nearestImage = null;

    const LERP_FACTOR = 0.8;
    const ATTRACTION_RADIUS = 100; // Increased for better detection
    const MAX_ATTRACTION_STRENGTH = 0.4;
    const GLOW_PROXIMITY_RADIUS = 150; // New radius for orb proximity glow

    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    function animateGradientSpot() {
        let actualTargetX = mouseX;
        let actualTargetY = mouseY;
        let minDistance = Infinity;
        let potentialNearestImage = null;

        // Find nearest image for attraction
        galleryImages.forEach(image => {
            const rect = image.getBoundingClientRect();
            const imageCenterX = rect.left + rect.width / 2;
            const imageCenterY = rect.top + rect.height / 2;

            const dist = Math.sqrt(
                Math.pow(mouseX - imageCenterX, 2) +
                Math.pow(mouseY - imageCenterY, 2)
            );

            if (dist < minDistance) {
                minDistance = dist;
                potentialNearestImage = image;
            }
        });

        // Apply attraction effect with RED glow instead of blue
        if (potentialNearestImage && minDistance < ATTRACTION_RADIUS) {
            if (nearestImage && nearestImage !== potentialNearestImage) {
                nearestImage.classList.remove('highlighted');
            }
            nearestImage = potentialNearestImage;
            nearestImage.classList.add('highlighted');

            const rect = nearestImage.getBoundingClientRect();
            const imageCenterX = rect.left + rect.width / 2;
            const imageCenterY = rect.top + rect.height / 2;

            let attractionForce = Math.max(0, Math.min(MAX_ATTRACTION_STRENGTH, 1 - (minDistance / ATTRACTION_RADIUS)));

            actualTargetX = mouseX * (1 - attractionForce) + imageCenterX * attractionForce;
            actualTargetY = mouseY * (1 - attractionForce) + imageCenterY * attractionForce;
        } else {
            if (nearestImage) {
                nearestImage.classList.remove('highlighted');
                nearestImage = null;
            }
        }

        // Additional proximity glow when orb is near (RED glow instead of blue)
        galleryImages.forEach(image => {
            if (image === nearestImage) return; // Skip if already highlighted

            const rect = image.getBoundingClientRect();
            const imageCenterX = rect.left + rect.width / 2;
            const imageCenterY = rect.top + rect.height / 2;

            // Calculate distance from current orb position (not mouse position)
            const orbDistance = Math.sqrt(
                Math.pow(currentX - imageCenterX, 2) +
                Math.pow(currentY - imageCenterY, 2)
            );

            if (orbDistance < GLOW_PROXIMITY_RADIUS) {
                const glowIntensity = 1 - (orbDistance / GLOW_PROXIMITY_RADIUS);
                // Changed to RED glow colors
                image.style.boxShadow = `
                    0 0 ${20 * glowIntensity}px rgba(220, 38, 38, ${0.3 * glowIntensity}),
                    0 0 ${40 * glowIntensity}px rgba(220, 38, 38, ${0.15 * glowIntensity}),
                    0 0 ${60 * glowIntensity}px rgba(220, 38, 38, ${0.05 * glowIntensity})
                `;
                image.style.transform = `translateY(-${3 * glowIntensity}px)`;
            } else {
                // Reset if not hovered and not in proximity
                const isHovered = image.matches(':hover');
                if (!isHovered) {
                    image.style.boxShadow = '';
                    image.style.transform = '';
                }
            }
        });

        // Smooth movement
        currentX += (actualTargetX - currentX) * LERP_FACTOR;
        currentY += (actualTargetY - currentY) * LERP_FACTOR;

        gradientSpot.style.transform = `translate(-50%, -50%) translate3d(${currentX}px, ${currentY}px, 0)`;

        requestAnimationFrame(animateGradientSpot);
    }

    animateGradientSpot();

    // Enhanced hover detection for all gallery images
    galleryImages.forEach(image => {
        image.addEventListener('mouseenter', function() {
            // Additional glow on direct hover
            if (!this.classList.contains('highlighted')) {
                this.style.transition = 'all 0.3s ease';
            }
        });

        image.addEventListener('mouseleave', function() {
            // Reset if not highlighted by orb
            if (!this.classList.contains('highlighted')) {
                this.style.boxShadow = '';
                this.style.transform = '';
            }
        });
    });

    // Rest of your existing JavaScript code (mobile nav, smooth scrolling, etc.)
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });

        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
    }

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -10% 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    galleryImages.forEach(image => {
        image.style.opacity = '0';
        image.style.transform = 'translateY(30px)';
        image.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(image);
    });
});

// Updated background dots code for WHITE background with BLACK dots
const bgCanvas = document.getElementById('interactive-bg');
const ctxBg = bgCanvas.getContext('2d');

let dots = [];
const DOT_COUNT = 200;
const DOT_RADIUS = 2;
const REPULSE_RADIUS = 150;
const ORB_REPULSE_RADIUS = 100;

function randomRange(min, max) {
    return Math.random() * (max - min) + min;
}

function initDots() {
    dots = [];
    for (let i = 0; i < DOT_COUNT; i++) {
        dots.push({
            x: randomRange(0, window.innerWidth),
            y: randomRange(0, window.innerHeight),
            baseX: 0,
            baseY: 0,
            vx: 0,
            vy: 0,
            opacity: randomRange(0.15, 0.35)
        });
    }
    dots.forEach(dot => {
        dot.baseX = dot.x;
        dot.baseY = dot.y;
    });
}

let mousePos = { x: null, y: null };
document.addEventListener('mousemove', (e) => {
    mousePos.x = e.clientX;
    mousePos.y = e.clientY;
});

function getOrbPosition() {
    const orb = document.getElementById('gradient-spot');
    if (orb) {
        const rect = orb.getBoundingClientRect();
        return {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2
        };
    }
    return { x: null, y: null };
}

function drawDots() {
    // Clear with WHITE background instead of transparent
    ctxBg.fillStyle = '#ffffff';
    ctxBg.fillRect(0, 0, bgCanvas.width, bgCanvas.height);
    
    dots.forEach(dot => {
        ctxBg.beginPath();
        ctxBg.arc(dot.x, dot.y, DOT_RADIUS, 0, Math.PI * 2);
        // Made dots MUCH darker - increased opacity and deeper black
        ctxBg.fillStyle = `rgba(0, 0, 0, ${dot.opacity * 0.8 + 0.3})`; // Much darker dots
        ctxBg.shadowColor = 'rgba(0, 0, 0, 0.4)';
        ctxBg.shadowBlur = 1;
        ctxBg.fill();
        ctxBg.shadowBlur = 0;
        ctxBg.closePath();
    });
}


function updateDots() {
    const orbPos = getOrbPosition();
    
    dots.forEach(dot => {
        if (mousePos.x !== null && mousePos.y !== null) {
            let dx = dot.x - mousePos.x;
            let dy = dot.y - mousePos.y;
            let dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < REPULSE_RADIUS && dist > 0) {
                let angle = Math.atan2(dy, dx);
                let force = (REPULSE_RADIUS - dist) / REPULSE_RADIUS;
                let repulseX = Math.cos(angle) * force * 3.0;
                let repulseY = Math.sin(angle) * force * 3.0;
                dot.vx += repulseX;
                dot.vy += repulseY;
            }
        }
        
        if (orbPos.x !== null && orbPos.y !== null) {
            let dxOrb = dot.x - orbPos.x;
            let dyOrb = dot.y - orbPos.y;
            let distOrb = Math.sqrt(dxOrb * dxOrb + dyOrb * dyOrb);

            if (distOrb < ORB_REPULSE_RADIUS && distOrb > 0) {
                let angleOrb = Math.atan2(dyOrb, dxOrb);
                let forceOrb = (ORB_REPULSE_RADIUS - distOrb) / ORB_REPULSE_RADIUS;
                let repulseXOrb = Math.cos(angleOrb) * forceOrb * 2.5;
                let repulseYOrb = Math.sin(angleOrb) * forceOrb * 2.5;
                dot.vx += repulseXOrb;
                dot.vy += repulseYOrb;
            }
        }
        
        dot.x += dot.vx;
        dot.y += dot.vy;
        dot.vx *= 0.92;
        dot.vy *= 0.92;
        
        let dxBase = dot.baseX - dot.x;
        let dyBase = dot.baseY - dot.y;
        dot.x += dxBase * 0.04;
        dot.y += dyBase * 0.04;
        
        if (dot.x < 0) {
            dot.x = 0;
            dot.vx *= -0.3;
        }
        if (dot.x > window.innerWidth) {
            dot.x = window.innerWidth;
            dot.vx *= -0.3;
        }
        if (dot.y < 0) {
            dot.y = 0;
            dot.vy *= -0.3;
        }
        if (dot.y > window.innerHeight) {
            dot.y = window.innerHeight;
            dot.vy *= -0.3;
        }
    });
}

function animateBackground() {
    updateDots();
    drawDots();
    requestAnimationFrame(animateBackground);
}

function resizeCanvas() {
    bgCanvas.width = window.innerWidth;
    bgCanvas.height = window.innerHeight;
}

window.addEventListener('resize', () => {
    resizeCanvas();
    initDots();
});

resizeCanvas();
initDots();
animateBackground();

// Awards page tab functionality
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
});

// Enhanced project filtering
document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const projectCards = document.querySelectorAll('.project-card');
    const consultationCards = document.querySelectorAll('.consultation-card');
    const consultationGrid = document.querySelector('.consultation-grid');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filterValue = this.getAttribute('data-filter');
            
            // Remove active class from all buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            
            // Filter project cards
            projectCards.forEach(card => {
                const categories = card.getAttribute('data-category');
                
                if (filterValue === 'all') {
                    card.style.display = 'block';
                } else if (categories && categories.includes(filterValue)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
            
            // Show/hide consultation section
            if (filterValue === 'consultation' || filterValue === 'all') {
                consultationGrid.style.display = 'grid';
            } else {
                consultationGrid.style.display = 'none';
            }
            
            // Filter consultation cards
            consultationCards.forEach(card => {
                const categories = card.getAttribute('data-category');
                
                if (filterValue === 'all' || filterValue === 'consultation') {
                    card.style.display = 'block';
                } else if (categories && categories.includes(filterValue)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });
});

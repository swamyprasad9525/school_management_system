/**
 * Advanced Animations & Interactive Physics Engine
 * Algions School Management System (Linear / Stripe Inspired)
 */

document.addEventListener('DOMContentLoaded', () => {
    initScrollProgressBar();
    initScrollReveal();
    initCard3DTilt();
    initTopbarScrollBlur();
    initBackToTop();
    initMagneticButtons();
});

/**
 * 1. Top Window Scroll Progress Bar
 */
function initScrollProgressBar() {
    let bar = document.getElementById('scrollProgressBar');
    if (!bar) {
        bar = document.createElement('div');
        bar.id = 'scrollProgressBar';
        bar.className = 'scroll-progress-bar';
        document.body.prepend(bar);
    }

    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
        bar.style.width = `${progress}%`;
    }, { passive: true });
}

/**
 * 2. IntersectionObserver Staggered Scroll Reveal
 */
function initScrollReveal() {
    const revealElements = document.querySelectorAll('.reveal-fade-up, .reveal-scale, .reveal-stagger');
    if (!revealElements.length) return;

    const observerOptions = {
        root: null,
        rootMargin: '0px 0px -60px 0px',
        threshold: 0.12
    };

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                // Trigger child counter if present
                const counters = entry.target.querySelectorAll('.count-up');
                counters.forEach(counter => {
                    if (!counter.dataset.animated) {
                        counter.dataset.animated = 'true';
                        animateSingleCounter(counter);
                    }
                });
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    revealElements.forEach(el => revealObserver.observe(el));
}

function animateSingleCounter(counter) {
    const target = parseInt(counter.getAttribute('data-target'), 10) || 0;
    const duration = 1200;
    const stepTime = 30;
    const totalSteps = duration / stepTime;
    const increment = target / totalSteps;
    let current = 0;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            counter.textContent = target;
            clearInterval(timer);
        } else {
            counter.textContent = Math.round(current);
        }
    }, stepTime);
}

/**
 * 3. 3D Magnetic Card Tilt with Cursor Lighting
 */
function initCard3DTilt() {
    // Only on pointer devices with hover capability
    if (window.matchMedia('(hover: none)').matches) return;

    const tiltCards = document.querySelectorAll('.persona-card, .kpi-card, .spotlight-card, .card-tilt');

    tiltCards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Mouse coordinates for cursor glow
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);

            // Subtle 3D tilt angle (max 4.5 degrees for smooth elegance)
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / centerY) * -4.5;
            const rotateY = ((x - centerX) / centerX) * 4.5;

            card.style.transform = `perspective(900px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-5px)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
            card.style.setProperty('--mouse-x', `-1000px`);
            card.style.setProperty('--mouse-y', `-1000px`);
        });
    });
}

/**
 * 4. Topbar Glassmorphism Elevation on Scroll
 */
function initTopbarScrollBlur() {
    const topbar = document.querySelector('.app-topbar');
    if (!topbar) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 24) {
            topbar.classList.add('topbar-scrolled');
        } else {
            topbar.classList.remove('topbar-scrolled');
        }
    }, { passive: true });
}

/**
 * 5. Floating Back to Top Pill
 */
function initBackToTop() {
    let btn = document.getElementById('backToTopBtn');
    if (!btn) {
        btn = document.createElement('button');
        btn.id = 'backToTopBtn';
        btn.className = 'back-to-top-btn';
        btn.setAttribute('title', 'Return to top');
        btn.innerHTML = '<i class="bi bi-arrow-up-short"></i><span>Top</span>';
        document.body.appendChild(btn);

        btn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    window.addEventListener('scroll', () => {
        if (window.scrollY > 350) {
            btn.classList.add('show');
        } else {
            btn.classList.remove('show');
        }
    }, { passive: true });
}

/**
 * 6. Subtle Magnetic Buttons Physics
 */
function initMagneticButtons() {
    if (window.matchMedia('(hover: none)').matches) return;

    const buttons = document.querySelectorAll('.btn-primary-gradient, .btn-persona, .btn-emerald-gradient');

    buttons.forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            btn.style.transform = `translate(${x * 0.12}px, ${y * 0.12}px) scale(1.02)`;
        });

        btn.addEventListener('mouseleave', () => {
            btn.style.transform = '';
        });
    });
}


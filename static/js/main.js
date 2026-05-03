/* Jay Bn Poultry Farm — main.js */

document.addEventListener('DOMContentLoaded', function () {

  // ── Auto-dismiss alerts after 5 seconds ─────────────────
  const alerts = document.querySelectorAll('.alert.fade.show');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 5000);
  });

  // ── Smooth scroll for anchor links ──────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // ── Navbar active state ──────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(function (link) {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // ── Add to cart AJAX (optional enhancement) ─────────────
  document.querySelectorAll('form[action*="add"]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      // Allow native submit, optionally intercept for AJAX
    });
  });

  // ── Sticky navbar shadow on scroll ──────────────────────
  window.addEventListener('scroll', function () {
    const navbar = document.querySelector('.navbar-farm');
    if (navbar) {
      if (window.scrollY > 10) {
        navbar.style.boxShadow = '0 4px 24px rgba(0,0,0,0.25)';
      } else {
        navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.15)';
      }
    }
  });

  // ── Image lazy loading fallback ──────────────────────────
  document.querySelectorAll('img[loading="lazy"]').forEach(function (img) {
    img.onerror = function () {
      this.style.display = 'none';
    };
  });
  
  // ── Product Hover Video Logic ─────────────────────────────
  const productCards = document.querySelectorAll('.product-card');
  productCards.forEach(card => {
    const video = card.querySelector('.product-hover-video');
    if (video) {
      card.addEventListener('mouseenter', () => {
        video.play().catch(err => {
          console.log("Autoplay blocked or video error:", err);
        });
      });
      
      card.addEventListener('mouseleave', () => {
        video.pause();
        video.currentTime = 0; // Reset to start
      });
    }
  });

});

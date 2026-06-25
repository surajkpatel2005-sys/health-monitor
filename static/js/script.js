/* ==========================================================
   MAIN JAVASCRIPT FILE
   ========================================================== */

// Hide page loader once everything is ready
window.addEventListener('load', function () {
  const loader = document.getElementById('page-loader');
  if (loader) {
    setTimeout(() => loader.classList.add('loaded'), 250);
  }
});

// Auto-dismiss flash alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Set default date inputs to today if empty
  const today = new Date().toISOString().split('T')[0];
  document.querySelectorAll('input[type="date"]').forEach(function (input) {
    if (!input.value) input.value = today;
  });
});

// Toggle password visibility
function togglePassword(fieldId, iconWrapper) {
  const field = document.getElementById(fieldId);
  const icon = iconWrapper.querySelector('i');
  if (field.type === 'password') {
    field.type = 'text';
    icon.classList.replace('bi-eye', 'bi-eye-slash');
  } else {
    field.type = 'password';
    icon.classList.replace('bi-eye-slash', 'bi-eye');
  }
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
  anchor.addEventListener('click', function (e) {
    const targetId = this.getAttribute('href');
    if (targetId.length > 1) {
      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    }
  });
});

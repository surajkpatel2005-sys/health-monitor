/* ==========================================================
   DASHBOARD JAVASCRIPT
   Handles dashboard-specific interactivity (progress bar
   animation, health-tip rotation, etc.)
   ========================================================== */

document.addEventListener('DOMContentLoaded', function () {
  // Animate progress bars on load
  document.querySelectorAll('.progress-thin-bar').forEach(function (bar) {
    const targetWidth = bar.style.width;
    bar.style.width = '0%';
    setTimeout(() => { bar.style.width = targetWidth; }, 200);
  });

  // Rotating motivational health tips (if element exists)
  const tips = [
    "Drink a glass of water as soon as you wake up.",
    "Aim for at least 7-8 hours of sleep tonight.",
    "Take a 10-minute walk after meals.",
    "Stretch for 5 minutes to start your day right.",
    "Track today's meals to stay mindful of your goals."
  ];
  const tipEl = document.getElementById('rotating-tip');
  if (tipEl) {
    let i = 0;
    setInterval(() => {
      i = (i + 1) % tips.length;
      tipEl.style.opacity = 0;
      setTimeout(() => {
        tipEl.textContent = tips[i];
        tipEl.style.opacity = 1;
      }, 300);
    }, 6000);
  }
});

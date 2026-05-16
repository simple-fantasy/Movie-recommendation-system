function createParticles() {
  const container = document.getElementById('particles');
  if (!container) return;

  const particleCount = 30;
  for (let i = 0; i < particleCount; i += 1) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.left = `${Math.random() * 100}%`;
    particle.style.animationDelay = `${Math.random() * 20}s`;
    particle.style.animationDuration = `${15 + Math.random() * 10}s`;
    container.appendChild(particle);
  }
}

function initPortal() { createParticles(); }
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPortal);
} else {
  initPortal();
}

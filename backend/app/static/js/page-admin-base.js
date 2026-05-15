document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('.sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');
  const menuToggle = document.getElementById('menuToggle');

  if (!sidebar || !sidebarOverlay || !menuToggle) return;

  function showSidebar() {
    sidebar.classList.add('show');
    sidebarOverlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function hideSidebar() {
    sidebar.classList.remove('show');
    sidebarOverlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  menuToggle.addEventListener('click', showSidebar);
  sidebarOverlay.addEventListener('click', hideSidebar);

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && sidebar.classList.contains('show')) {
      hideSidebar();
    }
  });
});

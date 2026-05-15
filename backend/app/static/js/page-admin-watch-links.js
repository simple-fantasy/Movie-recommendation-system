document.addEventListener('DOMContentLoaded', () => {
  const statusFilter = document.querySelector('.js-watchlink-status-filter');
  const deleteForms = document.querySelectorAll('form.js-watchlink-delete-confirm');

  if (statusFilter && statusFilter.form) {
    statusFilter.addEventListener('change', () => statusFilter.form.submit());
  }

  deleteForms.forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!confirm('确定要删除这条链接吗？')) {
        event.preventDefault();
      }
    });
  });
});

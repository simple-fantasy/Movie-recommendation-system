document.addEventListener('DOMContentLoaded', () => {
  const statusFilter = document.querySelector('.js-review-status-filter');
  const deleteForms = document.querySelectorAll('form.js-review-delete-confirm');

  if (statusFilter && statusFilter.form) {
    statusFilter.addEventListener('change', () => statusFilter.form.submit());
  }

  deleteForms.forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!confirm('确定要删除这条评论吗？')) {
        event.preventDefault();
      }
    });
  });
});

document.addEventListener('DOMContentLoaded', () => {
  const btnExportUserData = document.getElementById('btnExportUserData');
  const btnExportMovieData = document.getElementById('btnExportMovieData');
  const btnExportSystemStats = document.getElementById('btnExportSystemStats');
  const btnExportSystemBackup = document.getElementById('btnExportSystemBackup');

  const userDataFormat = document.getElementById('userDataFormat');
  const movieDataFormat = document.getElementById('movieDataFormat');
  const includeMovieRatings = document.getElementById('includeMovieRatings');
  const statsFormat = document.getElementById('statsFormat');

  if (btnExportUserData) {
    btnExportUserData.addEventListener('click', () => {
      const format = userDataFormat?.value || 'json';
      window.open(`/api/export/user-data?format=${encodeURIComponent(format)}`, '_blank');
    });
  }

  if (btnExportMovieData) {
    btnExportMovieData.addEventListener('click', () => {
      const format = movieDataFormat?.value || 'json';
      const includeRatings = includeMovieRatings?.checked ? 'true' : 'false';
      window.open(`/api/export/movie-data?format=${encodeURIComponent(format)}&include_ratings=${includeRatings}`, '_blank');
    });
  }

  if (btnExportSystemStats) {
    btnExportSystemStats.addEventListener('click', () => {
      const format = statsFormat?.value || 'json';
      window.open(`/api/export/system-stats?format=${encodeURIComponent(format)}`, '_blank');
    });
  }

  if (btnExportSystemBackup) {
    btnExportSystemBackup.addEventListener('click', () => {
      if (!confirm('确定要创建系统完整备份吗？此操作可能需要较长时间。')) {
        return;
      }
      window.open('/api/export/backup', '_blank');
    });
  }
});

const page = document.getElementById('movie-list-page');
const listId = page ? Number(page.dataset.listId) : null;
let listData = null;
let isLiked = false;

async function loadList() {
  try {
    const response = await fetch(`/api/movie-lists/${listId}`);
    const data = await response.json();

    if (data.movie_list) {
      listData = data.movie_list;
      displayList(data.movie_list);
    }
  } catch (error) {
    console.error('加载影单失败:', error);
    alert('加载影单失败，请稍后重试');
  } finally {
    const loadingEl = document.getElementById('loading');
    const contentEl = document.getElementById('content');
    if (loadingEl) loadingEl.style.setProperty('display', 'none', 'important');
    if (contentEl) contentEl.style.setProperty('display', 'block', 'important');
  }
}

function displayList(list) {
  document.getElementById('list-name').textContent = list.name;
  document.getElementById('list-description').textContent = list.description || '暂无描述';
  document.getElementById('creator').textContent = `创建者: ${list.username}`;
  document.getElementById('movie-count').textContent = list.movie_count;
  document.getElementById('view-count').textContent = list.view_count;
  document.getElementById('like-count').textContent = list.like_count;

  if (list.cover_image) {
    const coverImage = document.getElementById('cover-image');
    if (coverImage) coverImage.src = list.cover_image;
  }

  checkOwnership(list.user_id);
  displayMovies(list.items || []);
  loadComments();
}

function checkOwnership(userId) {
  // 根据实际需求判断当前用户是否为影单创建者
}

function displayMovies(movies) {
  const container = document.getElementById('movies-container');
  if (!container) return;

  if (!movies || movies.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>这个影单还没有电影</p>
      </div>
    `;
    return;
  }

  movies.sort((a, b) => a.order - b.order);

  container.innerHTML = '';
  movies.forEach((item, index) => {
    const card = document.createElement('div');
    card.className = 'movie-card';
    const posterUrl = item.movie_poster || '';
    const posterEl = hasValidPoster(posterUrl)
      ? `<img src="${posterUrl}" alt="${item.movie_title}" class="movie-poster" onerror="this.style.display='none';this.nextElementSibling.style.display=''" />`
      : '';
    const fallbackEl = posterEl
      ? `<div class="poster-gradient" style="display:none;width:100px;height:150px;${posterGradientStyle(item.movie_title)}"><span class="poster-initial">${posterInitial(item.movie_title)}</span></div>`
      : `<div class="poster-gradient" style="width:100px;height:150px;${posterGradientStyle(item.movie_title)}"><span class="poster-initial">${posterInitial(item.movie_title)}</span></div>`;
    card.innerHTML = `
      <span class="text-muted mr-2">#${index + 1}</span>
      ${posterEl}${fallbackEl}
      <div class="movie-info">
        <h5 class="movie-title">${item.movie_title}</h5>
        <p class="movie-year">📅 ${item.movie_year || '未知年份'}</p>
        ${item.note ? `<p class="movie-note">📝 ${item.note}</p>` : ''}
      </div>
    `;
    container.appendChild(card);
  });
}

async function loadComments() {
  try {
    const response = await fetch(`/api/movie-lists/${listId}/comments`);
    const data = await response.json();

    if (data.comments) {
      displayComments(data.comments);
    }
  } catch (error) {
    console.error('加载评论失败:', error);
  }
}

function displayComments(comments) {
  const container = document.getElementById('comments-container');
  if (!container) return;

  if (!comments || comments.length === 0) {
    container.innerHTML = '<p class="text-muted text-center">暂无评论</p>';
    return;
  }

  container.innerHTML = '';
  comments.forEach(comment => {
    const card = document.createElement('div');
    card.className = 'comment-card';
    card.innerHTML = `
      <div class="comment-header">
        <span class="comment-author">${comment.username}</span>
        <span class="comment-time">${comment.created_at}</span>
      </div>
      <p class="comment-content">${comment.content}</p>
      ${comment.replies && comment.replies.length > 0 ? `
        <div class="mt-2 pt-2 border-top">
          ${comment.replies.map(reply => `
            <div class="small bg-light p-2 rounded mb-1">
              <span class="font-weight-bold">${reply.username}:</span> ${reply.content}
            </div>
          `).join('')}
        </div>
      ` : ''}
    `;
    container.appendChild(card);
  });
}

async function toggleLike() {
  try {
    const response = await fetch(`/api/movie-lists/${listId}/like`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    const data = await response.json();

    if (data.success) {
      isLiked = data.liked;
      const likeIcon = document.getElementById('like-icon');
      const likeCount = document.getElementById('like-count');
      if (likeIcon) likeIcon.textContent = isLiked ? '❤️' : '🤍';
      if (likeCount) likeCount.textContent = data.like_count;
    }
  } catch (error) {
    console.error('点赞失败:', error);
    alert('操作失败，请稍后重试');
  }
}

async function submitComment() {
  const input = document.getElementById('comment-input');
  if (!input) return;

  const content = input.value.trim();
  if (!content) {
    alert('请输入评论内容');
    return;
  }

  try {
    const response = await fetch(`/api/movie-lists/${listId}/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ content })
    });
    const data = await response.json();

    if (data.success) {
      input.value = '';
      loadComments();
    } else {
      alert('评论失败: ' + (data.error || '请稍后重试'));
    }
  } catch (error) {
    console.error('评论失败:', error);
    alert('评论失败，请稍后重试');
  }
}

function initListDetail() {
  if (!listId) return;
  var commentButton = document.getElementById('comment-submit-btn');
  if (commentButton) commentButton.addEventListener('click', submitComment);
  var likeButton = document.getElementById('like-btn');
  if (likeButton) likeButton.addEventListener('click', toggleLike);
  loadList();
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initListDetail);
} else {
  initListDetail();
}

(function() {
  const searchInput = document.getElementById('search-input');
  const filterYear = document.getElementById('filter-year');
  const filterSubject = document.getElementById('filter-subject');
  const papersList = document.getElementById('papers-list');
  const countLabel = document.getElementById('paper-count');
  const themeToggle = document.getElementById('theme-toggle');
  const cards = Array.from(document.querySelectorAll('.paper-card'));

  function updateCount(n) {
    countLabel.textContent = '共 ' + n + ' 篇论文';
  }

  function filterPapers() {
    const term = searchInput.value.trim().toLowerCase();
    const year = filterYear.value;
    const subject = filterSubject.value;
    let visible = 0;

    cards.forEach(card => {
      const text = card.innerText.toLowerCase();
      const cardYear = card.dataset.year || '';
      const cardSubject = card.dataset.subject || '';
      const matchText = !term || text.includes(term);
      const matchYear = !year || cardYear === year;
      const matchSubject = !subject || cardSubject === subject;
      const show = matchText && matchYear && matchSubject;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    updateCount(visible);
  }

  searchInput.addEventListener('input', filterPapers);
  filterYear.addEventListener('change', filterPapers);
  filterSubject.addEventListener('change', filterPapers);

  window.toggleAbstract = function(btn, slug) {
    const el = document.getElementById('abs-' + slug);
    if (!el) return;
    const isHidden = el.style.display === 'none';
    el.style.display = isHidden ? 'block' : 'none';
    btn.textContent = isHidden ? '🔼 收起' : 'ℹ️ 详情';
  };

  /* Theme toggle */
  const storedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  function applyTheme(dark) {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    themeToggle.textContent = dark ? '☀️' : '🌙';
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }
  applyTheme(storedTheme ? storedTheme === 'dark' : prefersDark);
  themeToggle.addEventListener('click', () => {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    applyTheme(!isDark);
  });
})();

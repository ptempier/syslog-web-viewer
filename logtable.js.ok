let refreshTimer = null;

function getCurrentFilters() {
  return {
    host: document.getElementById('host_select')?.value || "",
    facility: document.getElementById('facility_select')?.value || "",
    level: document.getElementById('level_select')?.value || "",
    program: document.getElementById('program_select')?.value || "",
    pid: document.getElementById('pid_select')?.value || "",
    refresh: document.getElementById('refresh_select')?.value || "",
    num_lines: document.getElementById('num_lines_select')?.value || "",
    msgonly_filter: document.getElementById('msgonly_filter')?.value || ""
  };
}

function buildApiUrlWithFilters() {
  const filters = getCurrentFilters();
  const url = new URL('/api/table', window.location.origin);
  for (const [key, val] of Object.entries(filters)) {
    if (val) url.searchParams.set(key, val);
  }
  return url.toString();
}

function updateTableAndStats(data) {
  // Update table body
  const tbody = document.getElementById('log-tbody');
  tbody.innerHTML = '';
  data.rows.forEach(row => {
    const tr = document.createElement('tr');
    row.forEach(col => {
      const td = document.createElement('td');
      td.textContent = col;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  // Update stats
  document.getElementById('total_rows').textContent = data.total_rows;
  const fill = data.fill_level, max = data.max_size;
  document.getElementById('buffer_fill').textContent = `${fill}/${max} (${(100 * fill / max).toFixed(1)}%)`;
}

function pollWithRefreshInterval() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
  const refreshValue = document.getElementById('refresh_select')?.value;
  if (!refreshValue || refreshValue === "off") return;
  const interval = parseInt(refreshValue, 10);
  if (isNaN(interval) || interval < 500) return;
  refreshTimer = setInterval(() => {
    fetch(buildApiUrlWithFilters())
      .then(resp => resp.json())
      .then(data => updateTableAndStats(data))
      .catch(err => {
        // Optionally show an error, but don't stop the timer
        console.error("Refresh fetch error:", err);
      });
  }, interval);
}

function onDropdownChange() {
  // When changing filters/refresh, reload the page (to update dropdowns etc.)
  window.location.href = buildUrlWithFilters();
}

function buildUrlWithFilters(extra) {
  const url = new URL(window.location.href.split('?')[0], window.location.origin);
  const filters = getCurrentFilters();
  for (const [key, val] of Object.entries(filters)) {
    if (val) url.searchParams.set(key, val);
  }
  if (extra) {
    for (const [key, val] of Object.entries(extra)) {
      url.searchParams.set(key, val);
    }
  }
  return url.toString();
}

function filterFormSubmit(e) {
  e.preventDefault();
  onDropdownChange();
}

window.onload = function() {
  // Set up polling if refresh is enabled
  pollWithRefreshInterval();
  // Also: update polling interval if refresh select changes (without page reload)
  const refreshSelect = document.getElementById('refresh_select');
  if (refreshSelect) {
    refreshSelect.addEventListener('change', pollWithRefreshInterval);
  }
};

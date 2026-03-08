// ── SIDEBAR TOGGLE ─────────────────────────────────────────
const sidebar       = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const overlay       = document.getElementById('sidebarOverlay');

if (sidebarToggle) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', (e) => {
  if (window.innerWidth <= 1024 && sidebar && sidebar.classList.contains('open')) {
    if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  }
});

// ── MODALS ─────────────────────────────────────────────────
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
}

// Close modal on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal(overlay.id);
  });
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => {
      m.classList.remove('open');
      document.body.style.overflow = '';
    });
  }
});

// ── AUTO-DISMISS ALERTS ─────────────────────────────────────
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    alert.style.opacity = '0';
    alert.style.transform = 'translateY(-8px)';
    alert.style.transition = 'all 0.3s ease';
    setTimeout(() => alert.remove(), 300);
  }, 5000);
});

// ── COPY TO CLIPBOARD ───────────────────────────────────────
function copyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.innerHTML;
    btn.innerHTML = '✓ Copied!';
    btn.style.color = 'var(--success)';
    setTimeout(() => {
      btn.innerHTML = original;
      btn.style.color = '';
    }, 2000);
  });
}

// ── CONFIRM DIALOGS ─────────────────────────────────────────
function confirmAction(message, formId) {
  if (confirm(message)) {
    document.getElementById(formId).submit();
  }
}

// ── LIVE SEARCH FILTER ──────────────────────────────────────
function liveSearch(inputId, tableId) {
  const input = document.getElementById(inputId);
  const table = document.getElementById(tableId);
  if (!input || !table) return;

  input.addEventListener('input', () => {
    const query = input.value.toLowerCase();
    table.querySelectorAll('tbody tr').forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(query) ? '' : 'none';
    });
  });
}

// ── STATUS FILTER ───────────────────────────────────────────
function filterByStatus(selectId, tableId, colIndex) {
  const select = document.getElementById(selectId);
  const table  = document.getElementById(tableId);
  if (!select || !table) return;

  select.addEventListener('change', () => {
    const val = select.value.toLowerCase();
    table.querySelectorAll('tbody tr').forEach(row => {
      if (!val) { row.style.display = ''; return; }
      const cell = row.cells[colIndex];
      const text = cell ? cell.textContent.toLowerCase() : '';
      row.style.display = text.includes(val) ? '' : 'none';
    });
  });
}

// ── FORM VALIDATION ─────────────────────────────────────────
function validatePasswords(p1Id, p2Id) {
  const p1  = document.getElementById(p1Id);
  const p2  = document.getElementById(p2Id);
  const err = document.getElementById(p2Id + '_error');
  if (!p1 || !p2) return true;

  if (p1.value !== p2.value) {
    if (err) { err.textContent = 'Passwords do not match.'; err.style.display = 'block'; }
    p2.style.borderColor = 'var(--danger)';
    return false;
  }
  if (err) { err.style.display = 'none'; }
  p2.style.borderColor = '';
  return true;
}

// ── INVITE CODE VALIDATOR ───────────────────────────────────
const inviteInput = document.getElementById('invite_code');
if (inviteInput) {
  inviteInput.addEventListener('blur', async () => {
    const code    = inviteInput.value.trim();
    const info    = document.getElementById('invite_info');
    if (!code || !info) return;

    try {
      const res  = await fetch(`/api/v1/auth/invite/${code}/`);
      const data = await res.json();
      if (data.valid) {
        info.style.color   = 'var(--success)';
        info.textContent   = `✓ Valid invite for ${data.estate_name} (${data.role})`;
        const slugInput    = document.getElementById('id_estate_slug');
        if (slugInput) slugInput.value = data.estate_slug;
      } else {
        info.style.color = 'var(--danger)';
        info.textContent = '✗ ' + data.detail;
      }
    } catch {
      info.style.color = 'var(--text-muted)';
      info.textContent = 'Could not validate invite.';
    }
  });
}

// ── SLUG AUTO-FILL ──────────────────────────────────────────
const nameInput = document.getElementById('id_name');
const slugInput = document.getElementById('id_slug');
if (nameInput && slugInput && !slugInput.value) {
  nameInput.addEventListener('input', () => {
    slugInput.value = nameInput.value.toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-');
  });
}

// ── INIT ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  liveSearch('searchInput', 'mainTable');
  filterByStatus('statusFilter', 'mainTable', 3);
  console.log('ResidentialOS loaded');
});
// ============================================================================
// Agentic AI Security Intelligence — Frontend
// ============================================================================

const CATEGORY_COLORS = {
  agentic_ai_core: '#8b5cf6',
  red_team_offensive: '#ef4444',
  identity_access: '#3b82f6',
  runtime_infra_defense: '#10b981',
  soc_detection: '#f59e0b',
  data_governance: '#ec4899',
  supply_chain_code: '#6366f1',
};

const CATEGORY_LABELS = {
  agentic_ai_core: 'Agentic AI Core',
  red_team_offensive: 'Red Team & Offensive AI',
  identity_access: 'Identity & Access',
  runtime_infra_defense: 'Runtime / Infra Defense',
  soc_detection: 'SOC / Detection & Response',
  data_governance: 'Data & Governance',
  supply_chain_code: 'Supply Chain & Code',
};

const BAR_COLORS = ['#8b5cf6','#3b82f6','#10b981','#f59e0b','#ec4899','#ef4444','#6366f1','#06b6d4','#84cc16','#f97316'];

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
  loadQuickDomains();
  setupAutocomplete();
  document.getElementById('domainInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') analyzeDomain();
  });
});

async function loadQuickDomains() {
  try {
    const res = await fetch('/api/domains');
    const domains = await res.json();
    const el = document.getElementById('quickDomains');
    el.innerHTML = domains.slice(0, 20).map(d =>
      `<span class="domain-chip" onclick="analyzeDomain('${d.domain}')">${d.name || d.domain}</span>`
    ).join('');
  } catch(e) { console.error(e); }
}

// --- Autocomplete ---
let acTimer = null;
function setupAutocomplete() {
  const input = document.getElementById('domainInput');
  const dd = document.getElementById('acDropdown');
  input.addEventListener('input', () => {
    clearTimeout(acTimer);
    const q = input.value.trim();
    if (q.length < 2) { dd.classList.remove('show'); return; }
    acTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search-domain?q=${encodeURIComponent(q)}`);
        const items = await res.json();
        if (!items.length) { dd.classList.remove('show'); return; }
        dd.innerHTML = items.map(i => `
          <div class="ac-item" onclick="analyzeDomain('${i.domain}')">
            <div><span class="ac-domain">${i.domain}</span> <span class="ac-name">${i.name}</span></div>
            <span class="ac-count">${i.job_count} jobs</span>
          </div>`).join('');
        dd.classList.add('show');
      } catch(e) { dd.classList.remove('show'); }
    }, 250);
  });
  document.addEventListener('click', e => {
    if (!e.target.closest('.search-wrapper')) dd.classList.remove('show');
  });
}

// --- Analyze ---
async function analyzeDomain(domain) {
  domain = domain || document.getElementById('domainInput').value.trim();
  if (!domain) return;
  document.getElementById('domainInput').value = domain;
  document.getElementById('acDropdown').classList.remove('show');

  const loader = document.getElementById('loader');
  const results = document.getElementById('results');
  const errorEl = document.getElementById('errorMsg');
  const btn = document.getElementById('analyzeBtn');

  results.classList.remove('show');
  results.innerHTML = '';
  errorEl.textContent = '';
  loader.classList.add('show');
  btn.disabled = true;

  try {
    const res = await fetch(`/api/analyze/${encodeURIComponent(domain)}`);
    const data = await res.json();
    loader.classList.remove('show');
    btn.disabled = false;

    if (data.error) {
      errorEl.textContent = data.error;
      return;
    }
    renderResults(data);
  } catch(e) {
    loader.classList.remove('show');
    btn.disabled = false;
    errorEl.textContent = 'Analysis failed: ' + e.message;
  }
}

// --- Render ---
function renderResults(data) {
  const el = document.getElementById('results');
  const p = data.profile || {};
  const s = data.summary || {};

  let html = '';

  // Company header
  html += `<div class="company-header fade-in">
    <div>
      <h2>${esc(s.company_name || data.company_name)}</h2>
      <div class="domain-badge">${esc(data.domain)}</div>
      <div class="company-stats">
        <div class="stat-item"><div class="stat-value">${data.jds_analyzed}</div><div class="stat-label">JDs Analyzed</div></div>
        <div class="stat-item"><div class="stat-value">${s.total_jobs || 0}</div><div class="stat-label">Total Jobs</div></div>
        <div class="stat-item"><div class="stat-value">${s.active_jobs || 0}</div><div class="stat-label">Active Jobs</div></div>
        <div class="stat-item"><div class="stat-value">${p.total_jds_analyzed || data.jds_analyzed}</div><div class="stat-label">Extracted</div></div>
      </div>
    </div>
  </div>`;

  // Compound signals
  if (data.compound_signals && data.compound_signals.length) {
    data.compound_signals.forEach(cs => {
      html += `<div class="compound-banner fade-in">
        <span class="icon">⚡</span>
        <div><div class="label">${esc(cs.description)}</div>
        <div class="desc">${esc(cs.implication)}</div></div>
      </div>`;
    });
  }

  // Composite profile
  if (p.composite_profile) {
    html += `<div class="compound-banner fade-in">
      <span class="icon">🎯</span>
      <div><div class="label">${esc(p.composite_profile.description || p.composite_profile.key)}</div>
      <div class="desc">Match: ${esc(p.composite_profile.match_strength || '')}. ${(p.composite_profile.signals_about || []).join(' • ')}</div></div>
    </div>`;
  }

  html += '<div class="sections-grid">';

  // --- PROJECTS (full width) ---
  html += '<div class="section-card full-width fade-in stagger-1">';
  html += '<div class="section-title"><span class="dot" style="background:var(--accent-purple)"></span>Projects Detected</div>';
  const projectsByCat = p.projects_by_category || {};
  if (Object.keys(projectsByCat).length) {
    for (const [catKey, projects] of Object.entries(projectsByCat)) {
      const color = CATEGORY_COLORS[catKey] || '#666';
      const label = CATEGORY_LABELS[catKey] || catKey;
      html += `<div class="category-header"><span class="cat-dot" style="background:${color}"></span><h4>${esc(label)}</h4></div>`;
      projects.forEach(proj => {
        html += renderProjectCard(proj, color);
      });
    }
  } else if (p.projects && p.projects.length) {
    p.projects.forEach(proj => html += renderProjectCard(proj, '#8b5cf6'));
  } else {
    html += '<p style="color:var(--text-muted)">No projects detected from JD analysis.</p>';
  }
  html += '</div>';

  // --- TEAMS ---
  html += '<div class="section-card fade-in stagger-2">';
  html += '<div class="section-title"><span class="dot" style="background:var(--accent-blue)"></span>Teams Identified</div>';
  const teams = p.teams || [];
  if (teams.length) {
    const maxMentions = Math.max(...teams.map(t => t.mentions));
    teams.forEach((t, i) => {
      const pct = Math.max(8, (t.mentions / maxMentions) * 100);
      const color = BAR_COLORS[i % BAR_COLORS.length];
      html += `<div class="team-bar-row">
        <span class="team-bar-label">${esc(t.canonical)}</span>
        <div class="team-bar-track"><div class="team-bar-fill" style="width:${pct}%;background:${color}">${t.mentions}</div></div>
      </div>`;
    });
  } else {
    html += '<p style="color:var(--text-muted)">No team signals detected.</p>';
  }
  html += '</div>';

  // --- TECH FUNCTION BREAKDOWN (from ClickHouse) ---
  html += '<div class="section-card fade-in stagger-3">';
  html += '<div class="section-title"><span class="dot" style="background:var(--accent-green)"></span>Tech Functions (DB)</div>';
  const tfs = data.tech_function_breakdown || [];
  if (tfs.length) {
    const maxTf = Math.max(...tfs.map(t => t.count));
    tfs.slice(0, 12).forEach((tf, i) => {
      const pct = Math.max(8, (tf.count / maxTf) * 100);
      const color = BAR_COLORS[i % BAR_COLORS.length];
      html += `<div class="tf-row">
        <span class="tf-label">${esc(tf.function)}</span>
        <div class="tf-bar"><div class="tf-fill" style="width:${pct}%;background:${color}">${tf.count}</div></div>
      </div>`;
    });
  } else {
    html += '<p style="color:var(--text-muted)">No tech function data.</p>';
  }
  html += '</div>';

  // --- TECH STACK ---
  html += '<div class="section-card fade-in stagger-2">';
  html += '<div class="section-title"><span class="dot" style="background:var(--accent-blue)"></span>Tech Stack (Extracted)</div>';
  const tech = p.tech_stack || {};
  if (Object.keys(tech).length) {
    for (const [cat, tools] of Object.entries(tech)) {
      html += `<div class="tech-category">
        <div class="tech-category-label">${esc(cat.replace(/_/g, ' '))}</div>
        <div class="tech-chips">${tools.map(t => `<span class="tech-chip">${esc(t)}</span>`).join('')}</div>
      </div>`;
    }
  } else {
    html += '<p style="color:var(--text-muted)">No tech signals detected.</p>';
  }
  html += '</div>';

  // --- PEOPLE ---
  html += '<div class="section-card fade-in stagger-3">';
  html += '<div class="section-title"><span class="dot" style="background:var(--accent-pink)"></span>People Signals</div>';
  const ppl = p.people || {};
  html += '<div class="people-grid">';
  html += `<div class="people-stat"><div class="ps-val">${ppl.total_roles || 0}</div><div class="ps-label">Total Roles</div></div>`;
  html += `<div class="people-stat"><div class="ps-val">${ppl.founding_team_roles || 0}</div><div class="ps-label">Founding Roles</div></div>`;
  const senMix = ppl.seniority_mix || {};
  for (const [level, count] of Object.entries(senMix)) {
    html += `<div class="people-stat"><div class="ps-val">${count}</div><div class="ps-label">${esc(level)}</div></div>`;
  }
  const leadMix = ppl.leadership_mix || {};
  for (const [level, count] of Object.entries(leadMix)) {
    html += `<div class="people-stat"><div class="ps-val" style="color:var(--accent-amber)">${count}</div><div class="ps-label">${esc(level)}</div></div>`;
  }
  html += '</div></div>';

  // --- CONTEXT ---
  html += '<div class="section-card fade-in stagger-4">';
  html += '<div class="section-title"><span class="dot" style="background:var(--accent-amber)"></span>Context Signals</div>';
  const ctx = p.context || {};
  if (Object.keys(ctx).length) {
    for (const [family, matches] of Object.entries(ctx)) {
      html += `<div class="context-group"><div class="context-label">${esc(family.replace(/_/g, ' '))}</div>`;
      (matches || []).forEach(m => {
        html += `<span class="context-badge">${esc(m.canonical)}${m.implication ? ` <span class="cb-impl">— ${esc(m.implication)}</span>` : ''}</span>`;
      });
      html += '</div>';
    }
  } else {
    html += '<p style="color:var(--text-muted)">No context signals detected.</p>';
  }
  html += '</div>';

  // --- VELOCITY ---
  const vel = p.velocity_signals || [];
  if (vel.length) {
    html += '<div class="section-card fade-in stagger-5">';
    html += '<div class="section-title"><span class="dot" style="background:var(--accent-green)"></span>Velocity Signals</div>';
    vel.forEach(v => {
      html += `<div class="context-group"><span class="context-badge">${esc(v.canonical)} <span class="cb-impl">— ${esc(v.implication)}</span></span></div>`;
    });
    html += '</div>';
  }

  html += '</div>'; // close sections-grid

  // --- JD TABLE ---
  html += '<div class="section-card full-width fade-in stagger-5" style="margin-top:0">';
  html += '<div class="section-title"><span class="dot" style="background:var(--text-muted)"></span>Individual JDs Analyzed</div>';
  html += renderJDTable(data.jd_details || []);
  html += '</div>';

  el.innerHTML = html;
  el.classList.add('show');
}

function renderProjectCard(proj, color) {
  const confClass = proj.score >= 4 ? 'confirmed' : 'candidate';
  const confLabel = proj.score >= 4 ? 'Confirmed' : 'Candidate';
  let evTags = '';
  const ev = proj.evidence || {};
  // For company-aggregated projects we may not have full evidence
  if (proj.proofs && proj.proofs.length) {
    evTags += proj.proofs.map(p => `<div style="color:var(--text-secondary);font-size:.85rem;margin-top:6px;line-height:1.5">${esc(p)}</div>`).join('');
  }
  if (proj.personas_hired && proj.personas_hired.length) {
    evTags += '<div style="margin-top:6px">' + proj.personas_hired.map(p => `<span class="evidence-tag persona">${esc(p)}</span>`).join('') + '</div>';
  }

  return `<div class="project-card" onclick="this.classList.toggle('expanded')" style="border-left:3px solid ${color}">
    <div class="pc-header">
      <span class="pc-name">${esc(proj.canonical)}</span>
      <span class="pc-score ${confClass}">${confLabel} · ${proj.score}pts</span>
    </div>
    <div class="pc-meta">
      <span>📂 ${esc(CATEGORY_LABELS[proj.parent_category] || proj.parent_category)}</span>
      ${proj.maturity && proj.maturity !== 'unspecified' ? `<span>🔬 ${esc(proj.maturity)}</span>` : ''}
      ${proj.jds_count ? `<span>📄 ${proj.jds_count} JDs</span>` : ''}
    </div>
    <div class="pc-evidence">${evTags || '<span style="color:var(--text-muted)">Click to expand details</span>'}</div>
  </div>`;
}

function renderJDTable(jds) {
  if (!jds.length) return '<p style="color:var(--text-muted)">No JDs to display.</p>';
  let html = `<div style="overflow-x:auto"><table class="jd-table">
    <thead><tr>
      <th>Title</th><th>Department</th><th>Level</th><th>Tech Function</th><th>Projects Detected</th><th>Teams</th><th>Active</th>
    </tr></thead><tbody>`;
  jds.forEach(jd => {
    const projTags = (jd.extracted_projects || []).map(p =>
      `<span class="mini-tag">${esc(p.canonical)} (${p.score})</span>`
    ).join(' ');
    const teamTags = (jd.extracted_teams || []).join(', ');
    html += `<tr>
      <td>${esc(jd.title)}</td>
      <td>${esc(jd.department)}</td>
      <td>${esc(jd.seniority || jd.level)}</td>
      <td>${esc(jd.tech_function)}</td>
      <td class="jd-projects-cell">${projTags || '—'}</td>
      <td>${esc(teamTags) || '—'}</td>
      <td>${jd.is_active ? '✅' : '—'}</td>
    </tr>`;
  });
  html += '</tbody></table></div>';
  return html;
}

function esc(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = String(s);
  return d.innerHTML;
}

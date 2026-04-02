/**
 * app.js — application state, API calls, and UI event wiring.
 * Imports rendering helpers from render.js; no DOM templates live here.
 */

import { detectCategory, formatTimestamp } from './utils.js';
import {
  renderGrid, renderNoResults, renderEmpty,
  renderLoading, renderError, renderCategoryFilters,
} from './render.js';
import { initGlitter } from './glitter.js';

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let allEvents    = [];
let activeCity   = 'all';
let activeCategory = 'all';

// ---------------------------------------------------------------------------
// Filtering
// ---------------------------------------------------------------------------
function filteredEvents() {
  return allEvents.filter(e => {
    const cityOk = activeCity === 'all' || e.city === activeCity;
    const catOk  = activeCategory === 'all' || detectCategory(e) === activeCategory;
    return cityOk && catOk;
  });
}

function categoryCounts() {
  // Count per category scoped to the active city (not the active category)
  const cityFiltered = allEvents.filter(e => activeCity === 'all' || e.city === activeCity);
  const counts = { all: cityFiltered.length };
  for (const e of cityFiltered) {
    const cat = detectCategory(e);
    counts[cat] = (counts[cat] || 0) + 1;
  }
  return counts;
}

// ---------------------------------------------------------------------------
// Rendering helpers (thin wrappers that pass current state)
// ---------------------------------------------------------------------------
function renderEvents() {
  const events = filteredEvents();
  if (allEvents.length === 0) return renderEmpty();
  if (events.length === 0)    return renderNoResults();
  renderGrid(events);
}

function refreshFilters() {
  const counts = categoryCounts();
  const categories = Object.keys(counts).filter(k => k !== 'all').sort();
  renderCategoryFilters(categories, activeCategory, counts, cat => {
    activeCategory = cat;
    renderEvents();
  });
}

// ---------------------------------------------------------------------------
// Status indicators
// ---------------------------------------------------------------------------
function setStatus(state) {
  document.getElementById('statusDot').className =
    'status-dot' + (state === 'loading' ? ' loading' : state === 'error' ? ' error' : '');
}

function showToast(msg, type = 'success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type} show`;
  setTimeout(() => { el.className = 'toast'; }, 3500);
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------
async function loadEvents() {
  setStatus('loading');
  try {
    const res = await fetch('/api/events');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    allEvents = data.events ?? [];

    document.getElementById('lastUpdated').textContent =
      formatTimestamp(data.scraped_at);

    refreshFilters();
    renderEvents();
    setStatus('ok');
  } catch (err) {
    setStatus('error');
    console.error(err);
    renderError();
  }
}

// ---------------------------------------------------------------------------
// City pill wiring
// ---------------------------------------------------------------------------
function initCityPills() {
  document.querySelectorAll('.city-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      activeCity = pill.dataset.city;
      document.querySelectorAll('.city-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      refreshFilters();
      renderEvents();
    });
  });
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  initGlitter();
  initCityPills();
  loadEvents();
});

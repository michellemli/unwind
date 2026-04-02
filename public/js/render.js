/**
 * render.js — all DOM rendering. Reads state from app.js, writes to the DOM.
 * No fetch calls or state mutations here.
 */

import { escapeHTML, cityClass, detectCategory } from './utils.js';

const CATEGORY_ICONS = {
  'Wellness':             '🧘',
  'Arts & Crafts':        '🎨',
  'Outdoor & Fitness':    '🌿',
  'Music & Entertainment':'🎵',
  'Food & Drink':         '🍽️',
  'Culture & Learning':   '🏛️',
  'Social':               '🥂',
  'Other':                '✨',
  'default':              '✨',
};

const CITY_PLACEHOLDER = {
  'Boston, MA':       '🏙️',
  'Cambridge, MA':    '🎓',
  'New York City, NY':'🗽',
  'Jersey City, NJ':  '🌆',
  'Hoboken, NJ':      '🌃',
  'Newark, NJ':       '🏛️',
  'Pittsburgh, PA':   '🌉',
};

// SVG icons reused across cards
const ICON_CALENDAR = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
  <line x1="16" y1="2" x2="16" y2="6"></line>
  <line x1="8"  y1="2" x2="8"  y2="6"></line>
  <line x1="3"  y1="10" x2="21" y2="10"></line>
</svg>`;

const ICON_PIN = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
  <circle cx="12" cy="10" r="3"></circle>
</svg>`;

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/** Render the full event grid from a filtered list. */
export function renderGrid(events) {
  const grid = document.getElementById('eventsGrid');
  grid.innerHTML = events.map((e, i) => cardHTML(e, i)).join('');
  document.getElementById('eventCount').innerHTML =
    `Showing <strong>${events.length}</strong> event${events.length !== 1 ? 's' : ''}`;
}

/** Render an empty-filter state (events exist but nothing matches). */
export function renderNoResults() {
  document.getElementById('eventsGrid').innerHTML =
    `<div class="empty-state"><div style="font-size:2rem">🔍</div><span>No events found for this filter.</span></div>`;
  document.getElementById('eventCount').innerHTML = '<strong>0</strong> events found';
}

/** Render the zero-events state with fallback search links. */
export function renderEmpty() {
  const links = [
    ['Eventbrite Boston',     'https://www.eventbrite.com/d/ma--boston/events/'],
    ['Eventbrite NYC',        'https://www.eventbrite.com/d/ny--new-york-city/events/'],
    ['Eventbrite NJ',         'https://www.eventbrite.com/d/nj--new-jersey/events/'],
    ['Luma NYC',              'https://lu.ma/nyc'],
    ['Eventbrite Pittsburgh', 'https://www.eventbrite.com/d/pa--pittsburgh/events/'],
  ].map(([label, href]) =>
    `<a href="${href}" target="_blank" rel="noopener"
        style="padding:8px 14px;background:var(--surface2);border:1px solid var(--border);
               border-radius:8px;color:var(--text);text-decoration:none;font-size:0.8rem">
      ${label} →
    </a>`
  ).join('');

  document.getElementById('eventsGrid').innerHTML = `
    <div class="empty-state">
      <div style="font-size:2.5rem">📭</div>
      <div style="font-weight:600;color:var(--text)">No events loaded yet</div>
      <div style="text-align:center;line-height:1.6;max-width:360px">
        The scraper couldn't retrieve live events right now (sites may be rate-limiting).
        Click <strong>Refresh</strong> to try again, or browse directly:
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:4px">
        ${links}
      </div>
    </div>`;
  document.getElementById('eventCount').innerHTML = '<strong>0</strong> events found';
}

/** Render a spinner while loading. */
export function renderLoading(message = 'Fetching events…') {
  document.getElementById('eventsGrid').innerHTML =
    `<div class="loading-state"><div class="spinner"></div><span>${escapeHTML(message)}</span></div>`;
}

/** Render a fatal error state. */
export function renderError() {
  document.getElementById('eventsGrid').innerHTML =
    `<div class="error-state"><div style="font-size:2rem">⚠️</div>
     <span>Failed to load events. Check the server is running.</span></div>`;
}

/**
 * Build the category filter buttons from the full event list.
 * @param {string[]} categories - sorted unique category names
 * @param {string} active - currently selected category key ('all' or a name)
 * @param {function} onSelect - callback(category: string)
 */
export function renderCategoryFilters(categories, active, counts, onSelect) {
  const el = document.getElementById('categoryFilters');
  el.innerHTML = ['all', ...categories].map(c => {
    const label = c === 'all' ? 'All' : c;
    const count = counts[c] ?? 0;
    const cls = active === c ? 'cat-btn active' : 'cat-btn';
    return `<button class="${cls}" data-cat="${escapeHTML(c)}">${escapeHTML(label)} <span class="cat-count">${count}</span></button>`;
  }).join('');

  el.querySelectorAll('.cat-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      el.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      onSelect(btn.dataset.cat);
    });
  });
}

// ---------------------------------------------------------------------------
// Card template
// ---------------------------------------------------------------------------

function cardHTML(event, index) {
  const category    = detectCategory(event);
  const icon        = CATEGORY_ICONS[category] ?? CATEGORY_ICONS.default;
  const placeholder = CITY_PLACEHOLDER[event.city] ?? '📍';
  const delay       = (index % 12) * 40;

  const imageHTML = event.img
    ? `<img class="card-image" src="${escapeHTML(event.img)}" alt="" loading="lazy"
            onerror="this.parentElement.innerHTML='<div class=\\'card-image-placeholder\\'>${placeholder}</div>'">`
    : `<div class="card-image-placeholder">${placeholder}</div>`;

  const dateHTML = event.date
    ? `<div class="card-date">${ICON_CALENDAR} ${escapeHTML(event.date)}</div>` : '';

  const locationHTML = event.location
    ? `<div class="card-location">${ICON_PIN} ${escapeHTML(event.location)}</div>` : '';

  const linkHTML = event.link
    ? `<a class="card-link" href="${escapeHTML(event.link)}" target="_blank" rel="noopener noreferrer">View Details →</a>` : '';

  return `
    <div class="event-card" style="animation-delay:${delay}ms">
      ${imageHTML}
      <div class="card-body">
        <div class="card-meta">
          <span class="city-badge ${cityClass(event.city)}">${escapeHTML(event.city ?? '')}</span>
          <span class="source-badge">${escapeHTML(event.source ?? '')}</span>
        </div>
        <div class="card-title">${escapeHTML(event.title)}</div>
        <span class="card-category">${icon} ${escapeHTML(category)}</span>
        <div class="card-info">${dateHTML}${locationHTML}</div>
        ${linkHTML}
      </div>
    </div>`;
}

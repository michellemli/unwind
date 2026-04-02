/**
 * utils.js — pure helper functions with no DOM side-effects.
 * Imported by render.js and app.js.
 */

/** Escape a value for safe insertion into HTML attribute or text content. */
export function escapeHTML(str) {
  return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/**
 * Map a city label to a CSS class name.
 * "New York" → "newyork", "New Jersey" → "newjersey"
 */
export function cityClass(city) {
  return (city ?? '').toLowerCase().replace(/[^a-z0-9]/g, '');
}

/**
 * Infer a category from an event's title and location text.
 * Returns one of the keys in CATEGORY_ICONS, or 'Event' as a fallback.
 */
export function detectCategory(event) {
  if (event.category) return event.category;
  const t = `${event.title} ${event.description} ${event.location}`.toLowerCase();
  if (/yoga|meditat|mindful|sound bath|breathwork|spa|wellness|reiki|pilates|stretch|relax|self.care|journaling/.test(t))                          return 'Wellness';
  if (/paint|pottery|craft|ceramics|knit|sew|sketch|drawing|watercolor|collage|candle|floral/.test(t))                                            return 'Arts & Crafts';
  if (/hike|trail|outdoor|walk|run|bike|cycle|kayak|climb|fitness|bootcamp|swim/.test(t))                                                         return 'Outdoor & Fitness';
  if (/concert|music|jazz|band|dj|festival|show|performance|comedy|stand.up|improv|pops|symphony/.test(t))                                        return 'Music & Entertainment';
  if (/cooking class|food tour|food festival|culinary|baking class|chef|mixology|cocktail class|wine dinner|cheese tasting|restaurant week|farmers market/.test(t)) return 'Food & Drink';
  if (/wine tasting|wine|beer tasting|craft beer|cocktail|brunch|dinner|tasting|dining|coffee|market|restaurant/.test(t))                         return 'Food & Drink';
  if (/museum|gallery|exhibit|film|cinema|theater|theatre|book club|book|lecture|talk|tour|culture/.test(t))                                      return 'Culture & Learning';
  if (/social|mixer|happy hour|get.together|meetup|networking|community/.test(t))                                                                  return 'Social';
  return 'Other';
}

/** Format an ISO timestamp for display in the header. */
export function formatTimestamp(isoStr) {
  return 'Updated ' + new Date(isoStr).toLocaleTimeString('en-US', {
    hour: 'numeric', minute: '2-digit',
  });
}

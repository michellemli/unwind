/**
 * glitter.js — animated sparkle/glitter background.
 *
 * Creates a fixed layer of twinkling dots and star glints
 * behind all page content. Called once on DOMContentLoaded.
 */

const COLORS  = ['#fff', '#ffb3cc', '#ff8fab', '#ffd700', '#ff2d78', '#c724b1', '#e8d5ff'];
const N_DOTS  = 180;   // tiny circular glitter dots
const N_STARS = 25;    // larger ✦ star glints

export function initGlitter() {
  const bg = document.createElement('div');
  bg.className = 'glitter-bg';
  bg.setAttribute('aria-hidden', 'true');
  document.body.insertBefore(bg, document.body.firstChild);

  // Tiny twinkling dots
  for (let i = 0; i < N_DOTS; i++) {
    const el  = document.createElement('div');
    el.className = 'g-dot';
    const size  = Math.random() * 2.8 + 0.4;
    const color = COLORS[Math.floor(Math.random() * COLORS.length)];
    Object.assign(el.style, {
      left:              Math.random() * 100 + 'vw',
      top:               Math.random() * 100 + 'vh',
      width:             size + 'px',
      height:            size + 'px',
      background:        color,
      boxShadow:         `0 0 ${size * 2.5}px ${color}`,
      animationDelay:    (Math.random() * 7).toFixed(2) + 's',
      animationDuration: (Math.random() * 3 + 2).toFixed(2) + 's',
    });
    bg.appendChild(el);
  }

  // Larger ✦ star glints
  for (let i = 0; i < N_STARS; i++) {
    const el  = document.createElement('div');
    el.className  = 'g-star';
    el.textContent = '✦';
    const color = COLORS[Math.floor(Math.random() * COLORS.length)];
    Object.assign(el.style, {
      left:              Math.random() * 100 + 'vw',
      top:               Math.random() * 100 + 'vh',
      color:             color,
      fontSize:          (Math.random() * 12 + 6).toFixed(1) + 'px',
      textShadow:        `0 0 10px ${color}, 0 0 20px ${color}`,
      animationDelay:    (Math.random() * 9).toFixed(2) + 's',
      animationDuration: (Math.random() * 4 + 3).toFixed(2) + 's',
    });
    bg.appendChild(el);
  }
}

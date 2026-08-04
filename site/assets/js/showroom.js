/* Katalog-Showroom — Index-Tracking, Filter, Reveal, Chat, Präsentation (kein Framework) */
(function () {
  'use strict';
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var spreads = Array.prototype.slice.call(document.querySelectorAll('.spread'));
  var rows = Array.prototype.slice.call(document.querySelectorAll('.irow'));
  var byId = {};
  rows.forEach(function (r) { byId[r.getAttribute('href').slice(1)] = r; });

  /* aktiver Index-Eintrag */
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        rows.forEach(function (r) { r.classList.remove('on'); });
        var r = byId[e.target.id];
        if (r) {
          r.classList.add('on');
          if (r.scrollIntoViewIfNeeded) r.scrollIntoViewIfNeeded(false);
          else r.scrollIntoView({ block: 'nearest' });
        }
        if (history.replaceState) history.replaceState(null, '', '#' + e.target.id);
      });
    }, { rootMargin: '-45% 0px -45% 0px' });
    spreads.forEach(function (s) { io.observe(s); });
  }

  /* Filter Software/Hardware */
  var fbtns = Array.prototype.slice.call(document.querySelectorAll('.fbtn'));
  fbtns.forEach(function (b) {
    b.addEventListener('click', function () {
      fbtns.forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      var f = b.dataset.f;
      document.querySelectorAll('.spread.product').forEach(function (s) {
        s.style.display = (f === 'all' || s.dataset.cat === f) ? '' : 'none';
      });
      rows.forEach(function (r) {
        if (!r.dataset.cat) return;
        r.classList.toggle('dim', !(f === 'all' || r.dataset.cat === f));
      });
    });
  });

  /* Mobile: Index auf/zu */
  var mb = document.getElementById('menubtn'), rw = document.getElementById('railwrap');
  if (mb && rw) {
    mb.addEventListener('click', function () {
      var open = rw.classList.toggle('open');
      mb.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    rw.addEventListener('click', function (e) {
      if (e.target.closest('a')) { rw.classList.remove('open'); mb.setAttribute('aria-expanded', 'false'); }
    });
  }

  /* Reveal je Spread */
  if (!reduce && 'IntersectionObserver' in window) {
    spreads.forEach(function (s) {
      var els = s.querySelectorAll('.stage, .pinfo > *, .introgrid > *, .cover-title, .cover-sub, .phead');
      Array.prototype.forEach.call(els, function (el, i) {
        el.classList.add('rv');
        el.style.setProperty('--d', Math.min(i * 0.06, 0.35) + 's');
      });
    });
    var rio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.querySelectorAll('.rv').forEach(function (el) { el.classList.add('in'); });
        rio.unobserve(e.target);
      });
    }, { threshold: 0.12 });
    spreads.forEach(function (s) { rio.observe(s); });
  }

  /* Chat abspielen */
  if ('IntersectionObserver' in window) {
    var pio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('play'); pio.unobserve(e.target); }
      });
    }, { threshold: 0.35 });
    document.querySelectorAll('.chatpanel').forEach(function (el) { pio.observe(el); });
  }

  /* Klapp-Listen */
  document.querySelectorAll('.fmore').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var list = btn.previousElementSibling;
      var open = list.classList.toggle('open');
      btn.textContent = open ? btn.dataset.less : btn.dataset.more;
    });
  });

  /* Präsentationsmodus */
  var idx = 0, wake = null, idleT = null;
  function visSpreads() {
    return spreads.filter(function (s) { return s.style.display !== 'none'; });
  }
  function cur() {
    var v = visSpreads(), y = scrollY + innerHeight / 2;
    for (var i = v.length - 1; i >= 0; i--) if (v[i].offsetTop <= y) return i;
    return 0;
  }
  function go(i) {
    var v = visSpreads();
    idx = Math.max(0, Math.min(v.length - 1, i));
    v[idx].scrollIntoView({ behavior: reduce ? 'auto' : 'smooth' });
  }
  function requestWake() {
    if (navigator.wakeLock) navigator.wakeLock.request('screen').then(function (w) { wake = w; }).catch(function () {});
  }
  function present(on) {
    document.body.classList.toggle('presenting', on);
    if (on) {
      idx = cur();
      if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen({ navigationUI: 'hide' }).catch(function () {});
      requestWake();
    } else {
      if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen().catch(function () {});
      if (wake) { wake.release().catch(function () {}); wake = null; }
      document.body.classList.remove('black', 'idle');
    }
  }
  document.addEventListener('fullscreenchange', function () {
    if (!document.fullscreenElement && document.body.classList.contains('presenting')) present(false);
  });
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden && document.body.classList.contains('presenting')) requestWake();
  });
  var pbtn = document.getElementById('present');
  if (pbtn) pbtn.addEventListener('click', function () { present(true); });
  document.addEventListener('keydown', function (e) {
    var p = document.body.classList.contains('presenting');
    if ((e.key === 'f' || e.key === 'F') && !e.metaKey && !e.ctrlKey) { if (!p) { e.preventDefault(); present(true); } return; }
    if (!p) return;
    switch (e.key) {
      case 'ArrowRight': case 'ArrowDown': case 'PageDown': case ' ': e.preventDefault(); go(idx + 1); break;
      case 'ArrowLeft': case 'ArrowUp': case 'PageUp': e.preventDefault(); go(idx - 1); break;
      case 'Home': e.preventDefault(); go(0); break;
      case 'End': e.preventDefault(); go(visSpreads().length - 1); break;
      case '.': e.preventDefault(); document.body.classList.toggle('black'); break;
      case 'Escape': present(false); break;
    }
  });
  document.addEventListener('mousemove', function () {
    if (!document.body.classList.contains('presenting')) return;
    document.body.classList.remove('idle');
    clearTimeout(idleT);
    idleT = setTimeout(function () { document.body.classList.add('idle'); }, 3000);
  });
})();

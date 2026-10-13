/* Knot Atlas: catalogue filters, learned ticks, basics tabs and the rope-anatomy figure. */
(function () {
  'use strict';
  function learned() { try { return JSON.parse(localStorage.getItem('knotatlas:learned') || '[]'); } catch (e) { return []; } }

  /* ---------- catalogue ---------- */
  var grid = document.getElementById('grid');
  if (grid) {
    var cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
    var chBtns = Array.prototype.slice.call(document.querySelectorAll('.chiprow button'));
    var act = document.getElementById('act'), q = document.getElementById('q'), count = document.getElementById('count');
    var ch = 'all';
    var valid = chBtns.map(function (b) { return b.getAttribute('data-ch'); });
    var h = (location.hash || '').slice(1);
    if (valid.indexOf(h) > -1) ch = h;
    var done = learned();
    cards.forEach(function (c) {
      var slug = c.querySelector('a').getAttribute('href').split('/')[1];
      var t = c.querySelector('.tick');
      if (t) t.hidden = done.indexOf(slug) < 0;
    });
    function apply() {
      var a = act.value, s = q.value.trim().toLowerCase(), n = 0;
      chBtns.forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-ch') === ch)); });
      cards.forEach(function (c) {
        var ok = (ch === 'all' || c.getAttribute('data-ch') === ch) &&
          (!a || c.getAttribute('data-acts').split(' ').indexOf(a) > -1) &&
          (!s || c.getAttribute('data-name').indexOf(s) > -1);
        c.hidden = !ok; if (ok) n++;
      });
      count.textContent = n === cards.length ? n + ' knots' : n + ' of ' + cards.length + ' knots';
    }
    chBtns.forEach(function (b) {
      b.addEventListener('click', function () {
        ch = b.getAttribute('data-ch');
        try { history.replaceState(null, '', ch === 'all' ? location.pathname : '#' + ch); } catch (e) { /* ignore */ }
        apply();
      });
    });
    act.addEventListener('change', apply);
    q.addEventListener('input', apply);
    apply();
  }

  /* ---------- basics: construction tabs ---------- */
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tabs [role="tab"]'));
  tabs.forEach(function (t, i) {
    function select() {
      tabs.forEach(function (o) {
        var on = o === t;
        o.setAttribute('aria-selected', String(on));
        o.tabIndex = on ? 0 : -1;
        document.getElementById(o.getAttribute('aria-controls')).hidden = !on;
      });
    }
    t.tabIndex = i === 0 ? 0 : -1;
    t.addEventListener('click', select);
    t.addEventListener('keydown', function (e) {
      var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (!d) return;
      var n = tabs[(i + d + tabs.length) % tabs.length];
      n.focus(); n.click(); e.preventDefault();
    });
  });

  /* ---------- basics: rope anatomy ---------- */
  var anat = document.getElementById('anat');
  if (anat) {
    var btns = Array.prototype.slice.call(anat.querySelectorAll('[data-term]'));
    var lines = Array.prototype.slice.call(anat.querySelectorAll('.hl'));
    var pick = function (term) {
      btns.forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-term') === term)); });
      lines.forEach(function (l) { l.classList.toggle('on', l.getAttribute('data-term') === term); });
    };
    btns.forEach(function (b) {
      b.addEventListener('click', function () { pick(b.getAttribute('data-term')); });
      b.addEventListener('mouseenter', function () { pick(b.getAttribute('data-term')); });
    });
    pick('standing');
  }
})();

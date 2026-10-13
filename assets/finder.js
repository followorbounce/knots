/* Knot Atlas: knot finder. Ranks knots in this guide for a job and a setting. */
(function () {
  'use strict';
  var data = JSON.parse(document.getElementById('finder-data').textContent);
  var job = document.getElementById('job'), where = document.getElementById('where'), undo = document.getElementById('undo');
  var out = document.getElementById('answers');
  var easyUntie = { 'Easy': 1 };

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function run() {
    var j = job.value, w = where.value, u = undo.checked;
    var list = data.filter(function (k) { return k.jobs.indexOf(j) > -1; });
    var dropped = 0;
    if (u) {
      var keep = list.filter(function (k) { return easyUntie[k.untie]; });
      dropped = list.length - keep.length;
      list = keep;
    }
    list.forEach(function (k) {
      k._score = (w && k.acts.indexOf(w) > -1 ? 0 : 10) + (k.jobs[0] === j ? 0 : 3) + k.difficulty + (easyUntie[k.untie] ? 0 : 1.5);
    });
    list.sort(function (a, b) { return a._score - b._score; });
    if (!list.length) {
      out.innerHTML = '<p>No knot in the guide so far fits all of that.' + (dropped ? ' Try without the easy-to-untie condition.' : '') + '</p>';
      return;
    }
    out.innerHTML = list.slice(0, 4).map(function (k, i) {
      var extra = [];
      extra.push('Security: ' + k.security.toLowerCase());
      extra.push('untying: ' + k.untie.toLowerCase());
      if (w && k.acts.indexOf(w) < 0) extra.push('not a usual choice for ' + w.toLowerCase());
      return '<div class="ans"><span class="rank">' + (i === 0 ? 'Best' : 'Also') + '</span><div>' +
        '<a href="../knots/' + k.slug + '/index.html">' + esc(k.name) + '</a>' +
        '<p>' + esc(k.brief) + '</p><p>' + esc(extra.join(', ')) + '.</p></div></div>';
    }).join('');
  }
  [job, where, undo].forEach(function (el) { el.addEventListener('change', run); });
  document.getElementById('fq').addEventListener('submit', function (e) { e.preventDefault(); });
  run();
})();

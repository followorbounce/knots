/* Knot Atlas: the 3D tying bench on every knot page.
   Reads #knot-data (ropes as sampled centrelines, objects, steps with
   per-rope visible fractions and over/under tags) and drives three.js. */
(function () {
  'use strict';
  var D = JSON.parse(document.getElementById('knot-data').textContent);
  var N = D.steps.length;
  var $ = function (id) { return document.getElementById(id); };
  var stage = $('stage'), view3d = $('view3d'), view2d = $('view2d');
  var scrub = $('scrub'), stepno = $('stepno');
  var stepBtns = Array.prototype.slice.call(document.querySelectorAll('#steps .step'));
  var figs = Array.prototype.slice.call(view2d.querySelectorAll('.dg'));
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  var ROPE = { a: 0xd39a2c, b: 0x2f7f8a, c: 0xb5523a };
  function col(hex) { return new THREE.Color(hex).convertSRGBToLinear(); }
  var state = { pos: N - 1, target: N - 1, playing: false, mirror: false, flat: false, settledAt: 0 };
  var gl = null;

  function visAt(pos) {
    var i = Math.max(0, Math.min(N - 1, Math.floor(pos)));
    var f = pos - i;
    var a = D.steps[i].vis, b = D.steps[Math.min(N - 1, i + 1)].vis;
    return a.map(function (v, k) { return v + (b[k] - v) * f; });
  }

  /* ---------- three.js scene ---------- */
  function stripeTexture() {
    var cv = document.createElement('canvas');
    cv.width = 128; cv.height = 64;
    var g = cv.getContext('2d');
    g.fillStyle = '#fff'; g.fillRect(0, 0, 128, 64);
    g.lineWidth = 9; g.strokeStyle = 'rgba(0,0,0,.22)';
    for (var x = -128; x < 256; x += 128 / 3) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x + 64, 64); g.stroke(); }
    g.lineWidth = 2; g.strokeStyle = 'rgba(255,255,255,.35)';
    for (x = -128; x < 256; x += 128 / 3) { g.beginPath(); g.moveTo(x + 12, 0); g.lineTo(x + 76, 64); g.stroke(); }
    var t = new THREE.CanvasTexture(cv);
    t.encoding = THREE.sRGBEncoding;
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    return t;
  }

  function initGL() {
    var T = window.THREE;
    if (!T || !T.OrbitControls) throw new Error('three.js not loaded');
    var renderer = new T.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    renderer.outputEncoding = T.sRGBEncoding;
    view3d.insertBefore(renderer.domElement, view3d.firstChild);
    var scene = new T.Scene();
    var camera = new T.PerspectiveCamera(32, 1, 0.1, 400);
    scene.add(new T.HemisphereLight(0xffffff, 0x3b4a50, 0.8));
    var d1 = new T.DirectionalLight(0xffffff, 0.8); d1.position.set(4, 7, 10); scene.add(d1);
    var d2 = new T.DirectionalLight(0xffffff, 0.3); d2.position.set(-6, -3, 5); scene.add(d2);
    var group = new T.Group(); scene.add(group);
    var controls = new T.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true; controls.enablePan = false;
    controls.minDistance = 3; controls.maxDistance = 80;

    var tex = stripeTexture();
    var r = D.r;
    var ropes = D.ropes.map(function (rp) {
      var p = rp.pts, pts = [];
      for (var i = 0; i < p.length; i += 3) pts.push(new T.Vector3(p[i], p[i + 1], p[i + 2]));
      var curve = new T.CatmullRomCurve3(pts, false, 'centripetal');
      var segs = Math.max(8, pts.length * 2);
      var geo = new T.TubeGeometry(curve, segs, r, 12, false);
      var t = tex.clone(); t.needsUpdate = true;
      t.repeat.set(curve.getLength() / (r * 6), 1);
      var mat = new T.MeshStandardMaterial({ color: col(ROPE[rp.color] || ROPE.a), map: t, roughness: 0.78, metalness: 0, side: T.DoubleSide });
      var mesh = new T.Mesh(geo, mat); group.add(mesh);
      var capMat = new T.MeshStandardMaterial({ color: col(ROPE[rp.color] || ROPE.a), roughness: 0.8 });
      var c0 = new T.Mesh(new T.SphereGeometry(r * 0.99, 16, 12), capMat); c0.position.copy(pts[0]); group.add(c0);
      var c1 = new T.Mesh(new T.SphereGeometry(r * 1.05, 16, 12), new T.MeshStandardMaterial({ color: col(0x1d2a2d), roughness: 0.6 }));
      group.add(c1);
      return { mesh: mesh, curve: curve, segs: segs, c0: c0, c1: c1, last: pts[pts.length - 1] };
    });
    D.objects.forEach(function (ob) {
      var m;
      if (ob.type === 'pole') {
        m = new T.Mesh(new T.CylinderGeometry(ob.radius, ob.radius, ob.len, 40, 1),
          new T.MeshStandardMaterial({ color: col(0xcfb07a), roughness: 0.85 }));
        if (ob.axis === 'x') m.rotation.z = Math.PI / 2;
        if (ob.axis === 'z') m.rotation.x = Math.PI / 2;
      } else if (ob.type === 'ring') {
        m = new T.Mesh(new T.TorusGeometry(ob.radius, ob.tube, 20, 80),
          new T.MeshStandardMaterial({ color: col(0x9aa3a6), roughness: 0.35, metalness: 0.7 }));
      } else if (ob.type === 'arc') {
        var a0 = ob.a0, len = ((ob.a1 - ob.a0) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI);
        m = new T.Mesh(new T.TorusGeometry(ob.radius, ob.tube, 16, 64, len),
          new T.MeshStandardMaterial({ color: col(0x9aa3a6), roughness: 0.35, metalness: 0.7 }));
        m.rotation.z = a0;
      }
      if (m && ob.rope) {
        var rt = tex.clone(); rt.needsUpdate = true; rt.repeat.set(ob.len / (ob.radius * 1.4), 3);
        m.material = new T.MeshStandardMaterial({ color: col(0xe2bf7e), map: rt, roughness: 0.85 });
      }
      if (m && ob.metal) m.material = new T.MeshStandardMaterial({ color: col(0x9aa3a6), roughness: 0.35, metalness: 0.7 });
      if (m) { m.position.set(ob.c[0], ob.c[1], ob.c[2]); group.add(m); }
    });

    var box = new T.Box3().setFromObject(group);
    var tags = [];
    var tagLayer = document.createElement('div'); tagLayer.className = 'tags'; view3d.appendChild(tagLayer);

    function fit() {
      var c = box.getCenter(new T.Vector3()), s = box.getSize(new T.Vector3());
      var w = view3d.clientWidth || 600, h = view3d.clientHeight || 400, asp = w / h;
      var fov = camera.fov * Math.PI / 180;
      var need = Math.max(s.y, s.x / asp) * 0.54 / Math.tan(fov / 2) + s.z * 0.5;
      controls.target.copy(c);
      var el = ((D.view && D.view.elev) || 6) * Math.PI / 180;
      camera.position.set(c.x + need * 0.06, c.y + need * Math.sin(el), c.z + need * Math.cos(el));
      camera.near = need / 50; camera.far = need * 10; camera.updateProjectionMatrix();
      controls.update();
    }
    function resize() {
      var w = view3d.clientWidth, h = view3d.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
    }
    resize(); fit();
    window.addEventListener('resize', resize);

    function setTags(list) {
      tagLayer.innerHTML = '';
      tags = list.map(function (t) {
        var el = document.createElement('span');
        el.className = 'tag ' + (t.over ? 'over' : 'under');
        el.textContent = t.over ? 'Over' : 'Under';
        tagLayer.appendChild(el);
        return { el: el, p: new T.Vector3(t.p[0], t.p[1], t.p[2]) };
      });
    }
    function draw(vis, showTags) {
      ropes.forEach(function (rp, k) {
        var n = Math.round(Math.max(0, Math.min(1, vis[k])) * rp.segs);
        rp.mesh.geometry.setDrawRange(0, n * 12 * 6);
        rp.mesh.visible = n > 0; rp.c0.visible = n > 0;
        rp.c1.visible = n > 0;
        if (n > 0) rp.c1.position.copy(rp.curve.getPointAt(Math.min(1, n / rp.segs)));
        rp.c1.material.color.copy(col(n >= rp.segs ? (ROPE[D.ropes[k].color] || ROPE.a) : 0x1d2a2d));
      });
      group.scale.x = state.mirror ? -1 : 1;
      controls.update();
      renderer.render(scene, camera);
      var w = view3d.clientWidth, h = view3d.clientHeight;
      tags.forEach(function (t) {
        var v = t.p.clone(); v.x *= state.mirror ? -1 : 1;
        v.project(camera);
        t.el.style.left = ((v.x + 1) / 2 * w) + 'px';
        t.el.style.top = ((1 - v.y) / 2 * h) + 'px';
        t.el.style.opacity = showTags ? 1 : 0;
      });
    }
    return { draw: draw, fit: fit, setTags: setTags };
  }

  /* ---------- UI ---------- */
  function setStepUI(i) {
    stepBtns.forEach(function (b, k) {
      b.classList.toggle('on', k === i);
      b.classList.toggle('done', k < i);
      b.setAttribute('aria-current', k === i ? 'step' : 'false');
    });
    stepno.textContent = i + 1;
    figs.forEach(function (f, k) { f.hidden = k !== i; });
    if (gl) gl.setTags(D.steps[i].tags || []);
  }

  function go(i, instant) {
    i = Math.max(0, Math.min(N - 1, i));
    state.target = i;
    if (instant || reduce) state.pos = i;
    setStepUI(i);
  }

  var last = 0;
  function tick(now) {
    requestAnimationFrame(tick);
    var dt = Math.min(0.05, (now - last) / 1000 || 0); last = now;
    var diff = state.target - state.pos;
    if (Math.abs(diff) > 1e-4) {
      var speed = Math.max(0.9, Math.abs(diff) * 2.5);
      state.pos += Math.sign(diff) * Math.min(Math.abs(diff), speed * dt);
      state.settledAt = 0;
    } else {
      state.pos = state.target;
      if (!state.settledAt) state.settledAt = now;
    }
    if (document.activeElement !== scrub) scrub.value = Math.round(state.pos * 100);
    if (state.playing && state.settledAt && now - state.settledAt > 1100) {
      if (state.target < N - 1) { go(state.target + 1); state.settledAt = 0; }
      else { state.playing = false; $('play').textContent = 'Play again'; }
    }
    if (gl && !state.flat) gl.draw(visAt(state.pos), state.pos === state.target);
  }

  stepBtns.forEach(function (b, k) {
    b.addEventListener('click', function (e) {
      if (e.target.closest('a')) return;
      state.playing = false; $('play').textContent = 'Play'; go(k);
    });
    b.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); state.playing = false; $('play').textContent = 'Play'; go(k); }
    });
  });
  scrub.addEventListener('input', function () {
    state.playing = false; $('play').textContent = 'Play';
    var v = scrub.value / 100;
    state.pos = v; state.target = Math.round(v);
    setStepUI(Math.round(v));
  });
  scrub.addEventListener('change', function () { go(Math.round(scrub.value / 100)); });
  $('play').addEventListener('click', function () {
    if (state.playing) { state.playing = false; this.textContent = 'Play'; return; }
    if (state.target >= N - 1) go(0, true);
    state.playing = true; state.settledAt = 0; this.textContent = 'Pause';
  });
  $('mirror').addEventListener('click', function () {
    state.mirror = !state.mirror;
    this.setAttribute('aria-pressed', String(state.mirror));
    view2d.classList.toggle('mirrored', state.mirror);
  });
  $('reset').addEventListener('click', function () { if (gl) gl.fit(); });
  function setFlat(on) {
    state.flat = on;
    $('flat').setAttribute('aria-pressed', String(on));
    view3d.hidden = on; view2d.hidden = !on;
    $('reset').disabled = on;
  }
  $('flat').addEventListener('click', function () { setFlat(!state.flat); });
  document.addEventListener('keydown', function (e) {
    var t = e.target.tagName;
    if (t === 'INPUT' || t === 'SELECT' || t === 'TEXTAREA') return;
    if (e.key === 'ArrowRight') { state.playing = false; go(state.target + 1); e.preventDefault(); }
    if (e.key === 'ArrowLeft') { state.playing = false; go(state.target - 1); e.preventDefault(); }
  });

  /* learned */
  var slug = document.querySelector('.knot').getAttribute('data-slug');
  var learnBtn = $('learn');
  function learned() { try { return JSON.parse(localStorage.getItem('knotatlas:learned') || '[]'); } catch (e) { return []; } }
  function showLearned() {
    var on = learned().indexOf(slug) > -1;
    learnBtn.setAttribute('aria-pressed', String(on));
    learnBtn.textContent = on ? 'Learned ✓' : 'Mark as learned';
  }
  learnBtn.addEventListener('click', function () {
    var l = learned(), i = l.indexOf(slug);
    if (i > -1) l.splice(i, 1); else l.push(slug);
    try { localStorage.setItem('knotatlas:learned', JSON.stringify(l)); } catch (e) { /* storage blocked */ }
    showLearned();
  });
  showLearned();

  try { gl = initGL(); } catch (err) { gl = null; }
  if (!gl) {
    setFlat(true);
    $('flat').disabled = true; $('mirror').disabled = false;
    $('hint').textContent = '3D view is not available in this browser, so the flat diagrams are shown.';
  }
  if (/^#flat$/.test(location.hash) && gl) setFlat(true);
  go(N - 1, true);
  if (gl) gl.draw(visAt(state.pos), true);
  requestAnimationFrame(tick);
})();

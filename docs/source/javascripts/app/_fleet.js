// Animated "live fleet" visual for the docs landing page.
//
// Mirrors the changelog visual on the marketing site so the SDK docs
// open with the same mental picture: a small grid of sandbox cards
// cycling through boot → run → paused / deleting. Vanilla JS, no
// dependencies, mounts into #anyframe-fleet when present.

(function () {
  var SLOTS = 6;
  var TICK_MS = 60;
  var SPAWN_INTERVAL_MS = 700;
  var BOOT_DUR_MS = 600;
  var RUN_DUR_MS = 1600;
  var PAUSE_HOLD_MS = 1000;
  var DELETE_DUR_MS = 380;

  var HARNESS = {
    claude: { name: 'claude code', accent: '#d97757' },
    cursor: { name: 'cursor',      accent: '#5db4f7' },
    codex:  { name: 'codex cli',   accent: '#a3a3a3' }
  };

  var JOBS = [
    { job: 'tests',    harness: 'claude', cpu: 8,  mem: 16 },
    { job: 'scrape',   harness: 'cursor', cpu: 2,  mem: 4  },
    { job: 'sql',      harness: 'codex',  cpu: 2,  mem: 4  },
    { job: 'render',   harness: 'claude', cpu: 16, mem: 32 },
    { job: 'refactor', harness: 'cursor', cpu: 4,  mem: 8  },
    { job: 'eval',     harness: 'codex',  cpu: 8,  mem: 16 },
    { job: 'build',    harness: 'claude', cpu: 4,  mem: 8  },
    { job: 'lint',     harness: 'cursor', cpu: 2,  mem: 4  },
    { job: 'deploy',   harness: 'codex',  cpu: 2,  mem: 4  }
  ];

  function randId() {
    return 'fr_' + Math.random().toString(36).slice(2, 6);
  }

  function phaseColor(phase) {
    if (phase === 'boot')    return '#5db4f7';
    if (phase === 'run')     return '#6ee7b7';
    if (phase === 'paused')  return '#fbbf24';
    if (phase === 'deleting') return '#f87171';
    return '#1f1f1f';
  }

  function phaseLabel(phase) {
    if (phase === 'boot')    return 'BOOT';
    if (phase === 'run')     return 'RUN';
    if (phase === 'paused')  return 'PAUSED';
    if (phase === 'deleting') return 'DEL';
    return 'IDLE';
  }

  function emptySlot() {
    return { id: null, phase: 'idle', job: '', harness: 'claude', cpu: 0, mem: 0, progress: 0, bornAt: 0 };
  }

  function buildShell(root) {
    root.innerHTML = ''
      + '<div class="fleet-bar">'
      +   '<div class="fleet-bar-left">'
      +     '<span class="fleet-dot dim"></span>'
      +     '<span class="fleet-dot dim"></span>'
      +     '<span class="fleet-dot dim"></span>'
      +     '<span class="fleet-title">live fleet</span>'
      +     '<span class="fleet-pulse"></span>'
      +   '</div>'
      +   '<div class="fleet-bar-right">'
      +     '<span><span class="fleet-tag-spawn">+</span> spawned <span class="fleet-count" data-count="spawned">0</span></span>'
      +     '<span><span class="fleet-tag-paused">&#8214;</span> paused <span class="fleet-count" data-count="paused">0</span></span>'
      +     '<span><span class="fleet-tag-deleted">&#215;</span> deleted <span class="fleet-count" data-count="deleted">0</span></span>'
      +   '</div>'
      + '</div>'
      + '<div class="fleet-grid"></div>';

    var grid = root.querySelector('.fleet-grid');
    var cards = [];
    for (var i = 0; i < SLOTS; i++) {
      var card = document.createElement('div');
      card.className = 'fleet-card idle';
      card.innerHTML = ''
        + '<div class="fleet-card-top">'
        +   '<span class="fleet-card-id">&mdash;</span>'
        +   '<span class="fleet-card-state">IDLE</span>'
        + '</div>'
        + '<div class="fleet-card-job">'
        +   '<span class="fleet-card-accent"></span>'
        +   '<span class="fleet-card-job-name"></span>'
        + '</div>'
        + '<div class="fleet-card-meta"></div>'
        + '<div class="fleet-card-progress"><div class="fleet-card-bar"></div></div>';
      grid.appendChild(card);
      cards.push(card);
    }
    return {
      cards: cards,
      counts: {
        spawned: root.querySelector('[data-count="spawned"]'),
        paused: root.querySelector('[data-count="paused"]'),
        deleted: root.querySelector('[data-count="deleted"]')
      }
    };
  }

  function paint(card, slot) {
    var isIdle = slot.phase === 'idle';
    var color = phaseColor(slot.phase);
    var label = phaseLabel(slot.phase);

    card.className = 'fleet-card ' + (isIdle ? 'idle' : 'active phase-' + slot.phase);
    card.style.borderColor = isIdle ? '' : color + '55';
    card.style.opacity = slot.phase === 'deleting' ? slot.progress : 1;

    card.querySelector('.fleet-card-id').textContent = slot.id || '—';
    var stateEl = card.querySelector('.fleet-card-state');
    stateEl.textContent = label;
    stateEl.style.color = color;

    var accent = card.querySelector('.fleet-card-accent');
    var jobName = card.querySelector('.fleet-card-job-name');
    if (isIdle) {
      accent.style.background = 'transparent';
      jobName.textContent = '';
    } else {
      accent.style.background = HARNESS[slot.harness].accent;
      jobName.textContent = slot.job;
    }

    var meta = card.querySelector('.fleet-card-meta');
    meta.textContent = isIdle ? '' : (slot.cpu + ' vCPU · ' + slot.mem + ' GB · ' + HARNESS[slot.harness].name);

    var bar = card.querySelector('.fleet-card-bar');
    if (isIdle || slot.phase === 'deleting') {
      bar.style.width = '0%';
    } else {
      bar.style.width = (slot.progress * 100) + '%';
      bar.style.background = color;
      bar.style.opacity = slot.phase === 'paused' ? 0.4 : 1;
    }
  }

  function start(root) {
    var shell = buildShell(root);
    var slots = [];
    for (var i = 0; i < SLOTS; i++) slots.push(emptySlot());
    var counts = { spawned: 0, paused: 0, deleted: 0 };

    var startedAt = performance.now();
    var lastSpawn = 0;
    var jobIdx = 0;

    var timer = setInterval(function () {
      var now = performance.now() - startedAt;
      for (var i = 0; i < slots.length; i++) {
        var s = slots[i];
        if (s.phase === 'idle') continue;
        var age = now - s.bornAt;

        if (s.phase === 'boot') {
          s.progress = Math.min(1, age / BOOT_DUR_MS);
          if (age >= BOOT_DUR_MS) { s.phase = 'run'; s.progress = 0; s.bornAt = now; }
        } else if (s.phase === 'run') {
          s.progress = Math.min(1, age / RUN_DUR_MS);
          if (age >= RUN_DUR_MS) {
            if (Math.random() < 0.55) { s.phase = 'paused'; counts.paused += 1; }
            else                      { s.phase = 'deleting'; counts.deleted += 1; }
            s.bornAt = now;
          }
        } else if (s.phase === 'paused') {
          if (age >= PAUSE_HOLD_MS) {
            s.phase = 'deleting'; counts.deleted += 1; s.bornAt = now;
          }
        } else if (s.phase === 'deleting') {
          s.progress = 1 - Math.min(1, age / DELETE_DUR_MS);
          if (age >= DELETE_DUR_MS) {
            slots[i] = emptySlot();
          }
        }
      }

      if (now - lastSpawn >= SPAWN_INTERVAL_MS) {
        for (var k = 0; k < slots.length; k++) {
          if (slots[k].phase === 'idle') {
            var j = JOBS[jobIdx % JOBS.length];
            jobIdx += 1;
            slots[k] = {
              id: randId(),
              phase: 'boot',
              job: j.job,
              harness: j.harness,
              cpu: j.cpu,
              mem: j.mem,
              progress: 0,
              bornAt: now
            };
            counts.spawned += 1;
            lastSpawn = now;
            break;
          }
        }
      }

      for (var c = 0; c < slots.length; c++) paint(shell.cards[c], slots[c]);
      shell.counts.spawned.textContent = counts.spawned;
      shell.counts.paused.textContent = counts.paused;
      shell.counts.deleted.textContent = counts.deleted;
    }, TICK_MS);

    // Pause when the tab is hidden so we don't waste CPU off-screen.
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) {
        clearInterval(timer);
      }
    });
  }

  function mount() {
    var root = document.getElementById('anyframe-fleet');
    if (!root || root.dataset.fleetMounted === '1') return;
    root.dataset.fleetMounted = '1';
    start(root);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();

/* Quizzes (_includes/quiz.html). The page works without this script: each
   answer is folded in a <details>. With it, options become buttons, answers
   are scored and saved in localStorage, and `data-mode="deck"` quizzes show
   one question at a time with filters, shuffle, a retry pile, a breakdown,
   and, when the quiz has a decision tree, a "walk the tree" way to answer. */
(function () {
  'use strict';

  var make = function (tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  };
  var button = function (cls, text) {
    var b = make('button', cls, text);
    b.type = 'button';
    return b;
  };
  var shuffle = function (list) {
    for (var i = list.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = list[i]; list[i] = list[j]; list[j] = t;
    }
    return list;
  };

  document.querySelectorAll('.quiz').forEach(function (root) {
    var key = 'quiz:' + root.dataset.storage;
    var deck = root.dataset.mode === 'deck';
    var state;
    try { state = JSON.parse(localStorage.getItem(key)) || {}; } catch (e) { state = {}; }
    var answers = state.answers || {};
    var persist = function () {
      try { localStorage.setItem(key, JSON.stringify({ answers: answers })); } catch (e) { /* private mode */ }
    };

    var items = [].slice.call(root.querySelectorAll('.quiz-item'));
    var legend = root.querySelector('.quiz-legend');
    var shared = legend ? [].slice.call(legend.querySelectorAll('.quiz-choices > li')) : null;

    // The decision tree, if any: steps by id, and each choice's path through them.
    var stepList = root.querySelector('.quiz-steps');
    var steps = {};
    if (stepList) {
      stepList.querySelectorAll(':scope > li').forEach(function (li) {
        steps[li.dataset.step] = {
          q: li.querySelector('.quiz-step-q').textContent,
          short: li.dataset.short,
          opts: [].map.call(li.querySelectorAll('[data-opt]'), function (o) { return [o.dataset.opt, o.textContent]; })
        };
      });
    }
    var paths = shared && stepList ? shared.map(function (li) {
      return li.dataset.path.split(',').map(function (p) { return p.split('='); });
    }) : null;

    root.classList.add('is-live');
    var status = make('p', 'quiz-status');
    status.setAttribute('role', 'status');
    var bar = make('div', 'quiz-bar');
    var score = make('p', 'quiz-score');
    var tools = make('div', 'quiz-tools');
    bar.append(score, tools);
    root.insertBefore(bar, root.querySelector('.quiz-items'));
    root.append(status);

    // Read from the buttons: the original option list is gone once they exist.
    var label = function (item, i) {
      var b = item.querySelector('.quiz-opt[data-i="' + i + '"]');
      return (b.querySelector('.quiz-opt-label') || b.querySelector('.quiz-opt-body')).textContent.trim();
    };
    var accepted = function (item) {
      var list = [Number(item.dataset.answer)];
      (item.dataset.also || '').split(',').forEach(function (a) { if (a) list.push(Number(a)); });
      return list;
    };

    // ---- each question: options become buttons ----
    items.forEach(function (item) {
      var own = item.querySelector('.quiz-options');
      var source = own ? [].slice.call(own.children) : shared;
      var group = make('div', 'quiz-buttons');
      group.setAttribute('role', 'group');
      group.setAttribute('aria-label', 'Answers');
      source.forEach(function (li, i) {
        var b = button('quiz-opt');
        b.dataset.i = i;
        b.append(make('kbd', null, String(i + 1)));
        var body = make('span', 'quiz-opt-body');
        body.innerHTML = li.innerHTML;
        b.append(body);
        group.append(b);
      });
      var details = item.querySelector('.quiz-answer');
      if (own) own.replaceWith(group); else item.insertBefore(group, details);
      item.insertBefore(make('p', 'quiz-feedback'), details);
      item.tabIndex = -1;

      group.addEventListener('click', function (e) {
        var b = e.target.closest('.quiz-opt');
        if (b && !b.disabled) choose(item, Number(b.dataset.i));
      });
      var summary = details.querySelector('summary');
      details.addEventListener('toggle', function () {
        summary.textContent = details.open ? 'Hide answer' : 'Show answer';
        // Opening the answer before choosing one counts as a skip.
        if (details.open && !answers[item.dataset.n]) choose(item, -1);
      });
      paint(item, false);
    });

    function choose(item, i, note) {
      var n = item.dataset.n;
      if (answers[n]) return;
      answers[n] = { c: i, ok: accepted(item).indexOf(i) >= 0 };
      persist();
      paint(item, true, note);
      update();
      var a = answers[n];
      var right = label(item, Number(item.dataset.answer));
      status.textContent = a.c < 0 ? 'Skipped. The answer is ' + right + '.'
        : a.ok ? 'Correct.' : 'Not quite. The answer is ' + right + '.';
      if (deck) next.focus({ preventScroll: true });
    }

    function paint(item, open, note) {
      var a = answers[item.dataset.n];
      var ok = accepted(item);
      var right = Number(item.dataset.answer);
      item.classList.toggle('is-right', !!a && a.ok);
      item.classList.toggle('is-wrong', !!a && !a.ok && a.c >= 0);
      item.classList.toggle('is-skipped', !!a && a.c < 0);
      item.querySelectorAll('.quiz-opt').forEach(function (b) {
        var i = Number(b.dataset.i);
        b.disabled = !!a;
        b.classList.toggle('is-key', !!a && i === right);
        b.classList.toggle('is-also', !!a && i !== right && ok.indexOf(i) >= 0);
        b.classList.toggle('is-picked', !!a && i === a.c);
      });
      var fb = item.querySelector('.quiz-feedback');
      fb.textContent = !a ? '' : a.c < 0 ? 'Skipped.'
        : a.ok ? (a.c === right ? 'Correct.' : 'Accepted: an alternative answer.')
        : 'Not quite.';
      if (a && note) fb.append(' ', note);
      var details = item.querySelector('.quiz-answer');
      if (a && open) details.open = true;
      if (!a) details.open = false;
    }

    function clear(list) {
      list.forEach(function (item) { delete answers[item.dataset.n]; paint(item, false); });
      persist();
    }

    // ---- score, and the end-of-quiz summary ----
    var done = make('div', 'quiz-done');
    done.hidden = true;
    var doneText = make('p');
    var doneTools = make('div', 'quiz-tools');
    done.append(doneText, doneTools);
    done.tabIndex = -1;
    root.insertBefore(done, status);

    // The bar and the summary each get their own pair of buttons.
    var retryMissed = function () {
      var missed = scope().filter(function (item) { var a = answers[item.dataset.n]; return a && !a.ok; });
      clear(missed);
      if (deck) { order = missed; pos = 0; show(); order[0].focus({ preventScroll: true }); }
      else { update(); missed[0].focus(); }
    };
    var startOver = function (b) {
      // Clearing a long quiz takes a second click.
      if (scope().length > 20 && !b.armed) {
        b.armed = setTimeout(function () { b.armed = null; b.textContent = 'Start over'; }, 3000);
        b.textContent = 'Click again to clear';
        return;
      }
      clearTimeout(b.armed); b.armed = null; b.textContent = 'Start over';
      clear(scope());
      if (deck) build(); else update();
      var first = deck ? order[0] : items[0];
      if (first) first.focus({ preventScroll: !deck });
    };
    var pair = function () {
      var r = button('quiz-btn', 'Retry missed');
      var s = button('quiz-btn', 'Start over');
      r.addEventListener('click', retryMissed);
      s.addEventListener('click', function () { startOver(s); });
      return [r, s];
    };
    var barButtons = pair();
    var doneButtons = pair();
    var retry = barButtons[0], again = barButtons[1];
    doneTools.append(doneButtons[0], doneButtons[1]);

    function update() {
      var list = scope();
      var seen = 0, right = 0, missed = 0;
      list.forEach(function (item) {
        var a = answers[item.dataset.n];
        if (!a) return;
        seen++;
        if (a.ok) right++; else missed++;
      });
      score.textContent = right + ' correct · ' + seen + ' of ' + list.length + ' answered';
      var finished = list.length > 0 && (deck ? pos >= order.length : seen === list.length);
      done.hidden = !finished;
      if (finished) {
        // A deck reports on the round just played, which may be a retry pile.
        var round = deck ? order : list;
        var got = round.filter(function (i) { var a = answers[i.dataset.n]; return a && a.ok; }).length;
        var left = round.filter(function (i) { var a = answers[i.dataset.n]; return a && !a.ok; }).length;
        doneText.textContent = 'You got ' + got + ' of ' + round.length +
          (left ? ', with ' + left + ' to review.' : '. All correct.');
      }
      retry.hidden = doneButtons[0].hidden = !missed;
      if (deck) {
        var answered = order.filter(function (i) { return answers[i.dataset.n]; }).length;
        fill.style.width = order.length ? (100 * answered / order.length) + '%' : '0';
        stats();
      }
    }

    // Everything counts in a list; in a deck, the questions the filters allow.
    var scope = function () { return deck ? filtered() : items; };

    if (!deck) {
      tools.append(retry, again);
      update();
      root.addEventListener('keydown', function (e) {
        var item = e.target.closest && e.target.closest('.quiz-item');
        var i = Number(e.key) - 1;
        if (item && i >= 0 && !e.altKey && !e.ctrlKey && !e.metaKey) {
          var b = item.querySelectorAll('.quiz-opt')[i];
          if (b && !b.disabled) { e.preventDefault(); choose(item, i); }
        }
      });
      return;
    }

    // ---- deck: one question at a time ----
    var order = [], pos = 0, walk = false;
    var filters = root.querySelector('.quiz-filters');
    var selects = filters ? [].slice.call(filters.querySelectorAll('select')) : [];
    if (filters) { filters.hidden = false; tools.append(filters); }

    var nav = make('div', 'quiz-nav');
    var prev = button('quiz-btn', '← Previous');
    var count = make('span', 'quiz-count');
    var next = button('quiz-btn quiz-next', 'Next →');
    var progress = make('div', 'quiz-progress');
    var fill = make('span');
    progress.append(fill);
    nav.append(prev, count, next);
    root.insertBefore(nav, done);
    bar.append(progress);

    var shuffler = button('quiz-btn', 'Shuffle');
    var modes;
    if (paths) {
      modes = make('div', 'quiz-modes');
      modes.setAttribute('role', 'group');
      modes.setAttribute('aria-label', 'How to answer');
      ['Pick the answer', 'Walk the tree'].forEach(function (t, i) {
        var b = button('quiz-btn', t);
        b.setAttribute('aria-pressed', String(i === 0));
        b.addEventListener('click', function () {
          walk = i === 1;
          modes.querySelectorAll('button').forEach(function (m, j) { m.setAttribute('aria-pressed', String(j === i)); });
          root.classList.toggle('is-walking', walk);
          show();
        });
        modes.append(b);
      });
    }
    var actions = make('div', 'quiz-actions');
    if (modes) actions.append(modes);
    actions.append(shuffler, retry, again);
    tools.append(actions);

    var statsBox = make('details', 'quiz-stats');
    statsBox.append(make('summary', null, 'Your breakdown'));
    var statsBody = make('div', 'quiz-stats-body');
    statsBox.append(statsBody);
    root.insertBefore(statsBox, status);

    function filtered() {
      return items.filter(function (item) {
        return selects.every(function (s) { return !s.value || item.dataset[s.dataset.field] === s.value; });
      });
    }

    function build() {
      order = filtered();
      pos = order.findIndex(function (item) { return !answers[item.dataset.n]; });
      if (pos < 0) pos = 0;
      show();
    }

    function show() {
      items.forEach(function (item) { item.hidden = true; });
      var item = order[pos];
      if (item) {
        item.hidden = false;
        if (answers[item.dataset.n]) item.querySelector('.quiz-answer').open = true;
        if (walk) startWalk(item);
      }
      count.textContent = !order.length ? 'No questions match these filters'
        : pos >= order.length ? 'Finished' : 'Question ' + (pos + 1) + ' of ' + order.length;
      prev.disabled = pos === 0;
      next.disabled = pos >= order.length;
      next.textContent = pos === order.length - 1 ? 'Finish' : 'Next →';
      update();
    }

    var go = function (step) {
      pos = Math.max(0, Math.min(order.length, pos + step));
      show();
      var target = order[pos] || done;
      target.focus({ preventScroll: true });
      if (root.getBoundingClientRect().top < 0) bar.scrollIntoView({ block: 'start' });
    };
    prev.addEventListener('click', function () { go(-1); });
    next.addEventListener('click', function () { go(1); });
    shuffler.addEventListener('click', function () {
      // Unanswered questions first, in a new order.
      var open = order.filter(function (i) { return !answers[i.dataset.n]; });
      var seen = order.filter(function (i) { return answers[i.dataset.n]; });
      order = shuffle(open.length ? open : seen.slice());
      if (open.length) order = order.concat(seen);
      pos = 0;
      show();
    });
    selects.forEach(function (s) { s.addEventListener('change', build); });

    root.addEventListener('keydown', function (e) {
      if (e.altKey || e.ctrlKey || e.metaKey || /^(SELECT|INPUT|TEXTAREA)$/.test(e.target.tagName)) return;
      var item = order[pos];
      if (e.key === 'ArrowRight' && !next.disabled) { e.preventDefault(); go(1); return; }
      if (e.key === 'ArrowLeft' && !prev.disabled) { e.preventDefault(); go(-1); return; }
      var i = Number(e.key) - 1;
      if (!item || answers[item.dataset.n] || !(i >= 0)) return;
      var b = item.querySelectorAll(walk ? '.quiz-walk-opts button' : '.quiz-opt')[i];
      if (b) { e.preventDefault(); b.click(); }
    });

    // ---- breakdown by correct answer and by question type ----
    function stats() {
      var groups = [];
      var add = function (title, keyOf, nameOf) {
        var rows = {};
        filtered().forEach(function (item) {
          var a = answers[item.dataset.n];
          if (!a) return;
          var k = keyOf(item);
          rows[k] = rows[k] || { name: nameOf(item), seen: 0, right: 0 };
          rows[k].seen++;
          if (a.ok) rows[k].right++;
        });
        var keys = Object.keys(rows);
        if (keys.length) groups.push([title, keys.map(function (k) { return rows[k]; })]);
      };
      // Answer indexes only line up across questions that share one set of choices.
      if (shared) {
        add('By correct answer', function (item) { return item.dataset.answer; },
          function (item) { return label(item, Number(item.dataset.answer)); });
      }
      var kind = selects.filter(function (s) { return s.dataset.field === 'kind'; })[0];
      if (kind) {
        add('By question type', function (item) { return item.dataset.kind; }, function (item) {
          var o = kind.querySelector('option[value="' + item.dataset.kind + '"]');
          return o ? o.textContent : item.dataset.kind;
        });
      }
      statsBox.hidden = !groups.length;
      statsBody.replaceChildren();
      groups.forEach(function (g) {
        var table = make('table');
        var head = make('tr');
        head.append(make('th', null, g[0]), make('th', null, 'Correct'), make('th', null, ''));
        table.append(head);
        g[1].forEach(function (r) {
          var tr = make('tr');
          var meter = make('span', 'quiz-meter');
          var m = make('span');
          m.style.width = (100 * r.right / r.seen) + '%';
          meter.append(m);
          var cell = make('td');
          cell.append(meter);
          tr.append(make('td', null, r.name), make('td', null, r.right + ' / ' + r.seen), cell);
          table.append(tr);
        });
        statsBody.append(table);
      });
    }

    // ---- walk the tree: answer the questions instead of naming the type ----
    function startWalk(item) {
      var old = item.querySelector('.quiz-walk');
      if (old) old.remove();
      if (answers[item.dataset.n]) return;
      var box = make('div', 'quiz-walk');
      var trail = make('ol', 'quiz-walk-trail');
      var ask = make('p', 'quiz-walk-q');
      var opts = make('div', 'quiz-walk-opts');
      box.append(trail, ask, opts);
      item.insertBefore(box, item.querySelector('.quiz-feedback'));
      var taken = [];

      var step = function () {
        var fits = paths.map(function (p, i) { return [p, i]; }).filter(function (x) {
          return taken.every(function (t, j) { return x[0][j] && x[0][j][0] === t[0] && x[0][j][1] === t[1]; });
        });
        var end = fits.filter(function (x) { return x[0].length === taken.length; })[0];
        if (end) { finish(end[1]); return; }
        var id = fits[0][0][taken.length][0];
        var s = steps[id];
        ask.textContent = s.q;
        opts.replaceChildren();
        s.opts.forEach(function (o, i) {
          var b = button('quiz-opt');
          b.append(make('kbd', null, String(i + 1)), make('span', 'quiz-opt-body', o[1]));
          b.addEventListener('click', function () {
            taken.push([id, o[0]]);
            var li = make('li');
            li.append(make('span', null, s.short), make('b', null, o[1]));
            trail.append(li);
            step();
          });
          opts.append(b);
        });
      };

      var finish = function (i) {
        ask.remove();
        opts.remove();
        var li = make('li', 'end', label(item, i));
        trail.append(li);
        // Where the walk left the right path, if it did.
        var want = paths[Number(item.dataset.answer)];
        var note;
        for (var j = 0; j < taken.length; j++) {
          if (!want[j] || want[j][1] !== taken[j][1]) {
            if (want[j]) {
              var s = steps[want[j][0]];
              var opt = s.opts.filter(function (o) { return o[0] === want[j][1]; })[0];
              note = 'The walk went off course at "' + s.short + '": the answer there is ' + opt[1] + '.';
            }
            break;
          }
        }
        choose(item, i, accepted(item).indexOf(i) < 0 ? note : null);
      };
      step();
    }

    build();
  });
})();

"""Tests for client-side wizard polling safeguards."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


WIZARD_JS_PATH = Path(__file__).resolve().parents[1] / "web" / "static" / "wizard.js"


def _run_wizard_js(statuses: list[dict[str, str]]) -> dict[str, str | int]:
    script = f"""
const fs = require('fs');
const vm = require('vm');

const source = fs.readFileSync({json.dumps(str(WIZARD_JS_PATH))}, 'utf8');
const statuses = {json.dumps(statuses)};
let fetchCalls = 0;
const queued = [];
const statusEl = {{
  _textContent: '',
  _innerHTML: '',
  set textContent(value) {{
    this._textContent = value;
    this._innerHTML = value;
  }},
  get textContent() {{
    return this._textContent;
  }},
  set innerHTML(value) {{
    this._innerHTML = value;
    this._textContent = value.replace(/<[^>]+>/g, '');
  }},
  get innerHTML() {{
    return this._innerHTML;
  }},
}};

const context = {{
  console,
  encodeURIComponent,
  window: {{
    jobScoutPolling: {{ jobId: 'job-123' }},
    location: {{ href: '' }},
  }},
  document: {{
    getElementById(id) {{
      return id === 'search-status-message' ? statusEl : null;
    }},
  }},
  fetch: async () => {{
    const status = statuses[Math.min(fetchCalls, statuses.length - 1)];
    fetchCalls += 1;
    return {{
      ok: true,
      json: async () => status,
    }};
  }},
  setTimeout: (fn) => {{
    queued.push(fn);
    return queued.length;
  }},
}};

vm.createContext(context);
vm.runInContext(source, context);

(async () => {{
  let guard = 0;
  while (queued.length > 0 && guard < 500) {{
    const fn = queued.shift();
    await fn();
    guard += 1;
  }}
  if (guard >= 500) {{
    throw new Error('polling queue did not drain');
  }}
  process.stdout.write(JSON.stringify({{
    href: context.window.location.href,
    fetchCalls,
    textContent: statusEl.textContent,
    innerHTML: statusEl.innerHTML,
  }}));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""

    result = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_wizard_js_redirects_on_any_redirect() -> None:
    result = _run_wizard_js(
        [{"status": "unknown", "redirect": "/wizard/configure", "message": "Expired search"}]
    )

    assert result["href"] == "/wizard/configure"
    assert result["fetchCalls"] == 1


def test_wizard_js_stops_after_max_retries_without_redirect() -> None:
    result = _run_wizard_js([{"status": "unknown", "message": "Search session expired."}])

    assert result["href"] == ""
    assert result["fetchCalls"] == 60
    assert "Restart" in str(result["innerHTML"])
    assert "/wizard/configure" in str(result["innerHTML"])

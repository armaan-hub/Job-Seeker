(function () {
  const rolesInput = document.getElementById("roles");
  const tagsContainer = document.getElementById("roles-tags");

  function renderTags() {
    if (!rolesInput || !tagsContainer) return;
    const roles = rolesInput.value
      .split(",")
      .map((r) => r.trim())
      .filter(Boolean);
    tagsContainer.innerHTML = "";
    roles.forEach(function (r) {
      const span = document.createElement("span");
      span.textContent = r;
      span.style.cssText =
        "display:inline-block;background:#e2e8f0;padding:2px 8px;border-radius:999px;margin:3px;";
      tagsContainer.appendChild(span);
    });
  }

  if (rolesInput) {
    rolesInput.addEventListener("blur", renderTags);
    renderTags();
  }

  const polling = window.jobScoutPolling;
  if (polling && polling.jobId) {
    const statusEl = document.getElementById("search-status-message");
    const maxAttempts = 60;
    let attempts = 0;

    const showPollingError = () => {
      if (!statusEl) return;
      statusEl.innerHTML =
        'Search is taking longer than expected or the session expired. <a href="/wizard/configure">Restart search</a>.';
    };

    const tick = async () => {
      attempts += 1;
      try {
        const resp = await fetch(`/wizard/search-status?job_id=${encodeURIComponent(polling.jobId)}`);
        if (!resp.ok) {
          throw new Error(`Unexpected status code: ${resp.status}`);
        }
        const status = await resp.json();
        if (status.redirect) {
          window.location.href = status.redirect;
          return;
        }
        if (statusEl) {
          statusEl.textContent =
            status.status === "running"
              ? "Searching job sources and scoring matches..."
              : status.message || `Unexpected status: ${status.status}. Retrying...`;
        }
        if (status.status !== "running" && attempts >= maxAttempts) {
          showPollingError();
          return;
        }
      } catch (error) {
        if (attempts >= maxAttempts) {
          showPollingError();
          return;
        }
        if (statusEl) statusEl.textContent = "Still working...";
      }
      if (attempts >= maxAttempts) {
        showPollingError();
        return;
      }
      setTimeout(tick, 2000);
    };
    setTimeout(tick, 400);
  }
})();

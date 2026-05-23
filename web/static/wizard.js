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
    const tick = async () => {
      try {
        const resp = await fetch(`/wizard/search-status?job_id=${encodeURIComponent(polling.jobId)}`);
        const status = await resp.json();
        if (statusEl) {
          statusEl.textContent =
            status.status === "running"
              ? "Searching job sources and scoring matches..."
              : status.message || `Status: ${status.status}`;
        }
        if (status.redirect && (status.status === "done" || status.status === "error")) {
          window.location.href = status.redirect;
          return;
        }
      } catch (error) {
        if (statusEl) statusEl.textContent = "Still working...";
      }
      setTimeout(tick, 2000);
    };
    setTimeout(tick, 400);
  }
})();

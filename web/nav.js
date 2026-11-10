// Shared navigation. TO ADD A PAGE: add one line to PAGES and nothing else.
//
// Pages are normally shown inside the shell (app.html): it keeps the navigation bar and one frame per page, so moving between pages
// does not reload everything. A page opened on its own redirects into the shell; add ?noshell=1 to see it standalone (used for screenshots).
window.ET_PAGES = [
  ["live.html", "Live"],
  ["levels.html", "Levels"],
  ["priorities.html?kind=killers", "Killer priorities"],
  ["priorities.html?kind=survivors", "Survivor priorities"],
  ["killer.html", "Killer sheet"],
  ["survivor_builds.html", "Survivor builds"],
  ["loadout.html", "Random loadout"],
  ["buildmaker.html", "Build creator"],
];
// Setup (first launch) becomes Settings, at the far right, once the setup is finished
window.ET_SETUP_PAGE = "setup.html";
window.ET_STATE = fetch("/api/shell", { cache: "no-store" }).then((r) => r.json()).catch(() => ({ setup_done: true }));
window.setupLabel = (done) => (done ? "⚙ Settings" : "Setup");

// Shown next to page titles: the game's live patch, and the patch label of Otzdarva's data when it differs.
window.patchLabel = (d) => {
  const r = d && d.patch, g = d && d.livePatch;
  if (g && r && g !== r) return `Game patch ${g} · Otzdarva's data is labelled ${r}`;
  return g || r ? "Patch " + (g || r) : "";
};

(function () {
  if (document.documentElement.dataset.shell === "1") return;  // the shell draws its own bar
  const framed = window.top !== window.self;
  const standalone = new URLSearchParams(location.search).has("noshell");

  if (!framed && !standalone) {  // opened directly: continue inside the shell
    const file = decodeURIComponent(location.pathname.split("/").pop() || "live.html");
    location.replace("/app.html#" + file + location.search + location.hash);
    return;
  }

  if (framed) {  // inside the shell: links to other pages are handled by the shell, and the shell draws the bar
    document.addEventListener("click", (e) => {
      const a = e.target.closest && e.target.closest("a[href]");
      if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || a.target === "_blank") return;
      if ((a.getAttribute("href") || "").startsWith("#")) return;
      const u = new URL(a.href, location.href);
      if (u.origin !== location.origin || !u.pathname.endsWith(".html") || !window.parent.etShell) return;
      e.preventDefault();
      window.parent.etShell.go(decodeURIComponent(u.pathname.split("/").pop()) + u.search);
    });
    return;
  }

  // standalone (?noshell=1)
  const q = new URLSearchParams(location.search);
  q.delete("noshell");
  const here = decodeURIComponent(location.pathname.split("/").pop() || "live.html") + (q.toString() ? "?" + q.toString() : "");
  const bar = document.createElement("div");
  bar.className = "topbar";
  bar.innerHTML = '<nav class="nav">' + window.ET_PAGES.map(([h, t]) => {
    const on = h.includes("?") ? here === h : here.split("?")[0] === h;
    return `<a href="${h}${h.includes("?") ? "&" : "?"}noshell=1"${on ? ' class="on"' : ""}>${t}</a>`;
  }).join("") + `<a class="set${here.split("?")[0] === window.ET_SETUP_PAGE ? " on" : ""}" href="${window.ET_SETUP_PAGE}?noshell=1">Setup</a></nav>`;
  document.body.prepend(bar);
  window.ET_STATE.then((s) => { bar.querySelector("a.set").textContent = window.setupLabel(s.setup_done); });
})();

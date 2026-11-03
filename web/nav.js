// Shared navigation bar. TO ADD A PAGE: add one line to PAGES and nothing else.
// Shown next to page titles: the game's live patch, and the patch label of Otzdarva's data when it differs.
window.patchLabel = (d) => {
  const r = d && d.patch, g = d && d.livePatch;
  if (g && r && g !== r) return `Game patch ${g} · Otzdarva's data is labelled ${r}`;
  return g || r ? "Patch " + (g || r) : "";
};
(function () {
  const PAGES = [
    ["live.html", "Live"],
    ["levels.html", "Levels"],
    ["priorities.html?kind=killers", "Killer priorities"],
    ["priorities.html?kind=survivors", "Survivor priorities"],
    ["killer.html", "Killer sheet"],
    ["survivor_builds.html", "Survivor builds"],
    ["loadout.html", "Random loadout"],
    ["setup.html", "Setup"],
  ];
  const here = (decodeURIComponent(location.pathname.split("/").pop() || "live.html") + location.search).replace(/&.*/, "");
  const bar = document.createElement("div");
  bar.className = "topbar";
  bar.innerHTML = '<nav class="nav">' + PAGES.map(([h, t]) => {
    const on = h.includes("?") ? here === h : here.split("?")[0] === h;
    return `<a href="${h}"${on ? ' class="on"' : ""}>${t}</a>`;
  }).join("") + "</nav>";
  document.body.prepend(bar);
})();

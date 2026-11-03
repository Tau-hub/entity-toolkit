// "Import levels from screenshots": a drop zone + review table, shared by the Levels and Setup pages.
// mountScan(element, { onDone(message) }) fills the element; onDone runs after the levels were saved.
(function () {
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const post = (url, body) => fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "X-Requested-With": "EntityToolkit" }, body: JSON.stringify(body || {}) }).then((r) => r.json());
  const readB64 = (f) => new Promise((res) => { const r = new FileReader(); r.onload = () => res(String(r.result).split(",")[1]); r.readAsDataURL(f); });

  window.mountScan = function (root, opts) {
    opts = opts || {};
    root.innerHTML = `<p class="scan-help">In the game, open the killer (or survivor) selection screen, where every character card shows its level badge, and take screenshots of the grid (scroll to cover everyone; several screenshots can overlap). Drop them here: the toolkit recognises each character and reads its level, then you review before anything is saved. A character shown with a level is marked as owned.</p>
      <div class="drop">Drop screenshots here, or <label>choose files<input type="file" accept="image/*" multiple hidden></label></div>
      <div class="scan-status"></div><div class="scan-out"></div>`;
    const drop = root.querySelector(".drop"), input = root.querySelector("input[type=file]"), status = root.querySelector(".scan-status"), out = root.querySelector(".scan-out");
    let scanned = {};

    async function scanFiles(files) {
      files = [...files].filter((f) => f.type.startsWith("image/"));
      if (!files.length) return;
      scanned = {}; out.innerHTML = "";
      let unknown = 0, cards = 0;
      for (let i = 0; i < files.length; i++) {
        status.textContent = `Reading screenshot ${i + 1} of ${files.length}…`;
        const r = await post("/api/levels/scan", { image: await readB64(files[i]) });
        if (r.error) { status.textContent = `${files[i].name}: ${r.error}`; continue; }
        r.cards.forEach((c) => {
          cards++;
          if (!c.name || c.level == null) { unknown++; return; }
          const k = c.kind + "|" + c.name;
          if (!scanned[k] || c.matches > scanned[k].matches) scanned[k] = c;
        });
      }
      const n = Object.keys(scanned).length;
      status.textContent = n || cards ? `${files.length} screenshot${files.length > 1 ? "s" : ""}, ${cards} cards: ${n} characters recognised${unknown ? `, ${unknown} card${unknown > 1 ? "s" : ""} not recognised` : ""}.`
        : "No character card found. Make sure the grid of cards is fully visible (the dark frame of each card) and that the database is downloaded.";
      render();
    }

    function render() {
      const list = Object.values(scanned).sort((a, b) => a.kind.localeCompare(b.kind) || a.name.localeCompare(b.name));
      if (!list.length) { out.innerHTML = ""; return; }
      const changed = list.filter((c) => c.level !== c.current).length;
      out.innerHTML = `<table class="scan"><tr><th>Apply</th><th></th><th>Character</th><th>Level read</th><th>Current</th></tr>${list.map((c, i) => `<tr>
        <td><input type="checkbox" data-i="${i}" ${c.level !== c.current ? "checked" : ""}></td>
        <td><img referrerpolicy="no-referrer" src="${esc(c.portrait)}" data-f="${esc(c.portrait2)}" alt=""></td>
        <td>${esc(c.name)} <span class="same">${c.kind === "killers" ? "killer" : "survivor"}</span></td>
        <td><select data-lv="${i}">${[0, 1, 2, 3].map((n) => `<option ${n === c.level ? "selected" : ""}>${n}</option>`).join("")}</select></td>
        <td class="${c.level > c.current ? "up" : c.level < c.current ? "dn" : "same"}">${c.current}${c.level !== c.current ? " → " + c.level : ""}</td></tr>`).join("")}</table>
        <div class="scan-actions"><button class="apply">Apply the ticked ones (${changed} differ from now)</button></div>`;
      out.querySelector(".apply").onclick = async () => {
        const entries = [];
        out.querySelectorAll("input[data-i]:checked").forEach((cb) => {
          const c = list[+cb.dataset.i];
          entries.push({ kind: c.kind, name: c.name, level: +out.querySelector(`select[data-lv="${cb.dataset.i}"]`).value });
        });
        const r = await post("/api/levels/apply", { entries });
        scanned = {}; out.innerHTML = ""; status.textContent = "";
        const msg = `Saved: ${r.changed} level(s) changed, ${entries.length} character(s) marked as owned.`;
        status.textContent = msg;
        if (opts.onDone) opts.onDone(msg);
      };
    }

    input.onchange = (e) => { scanFiles(e.target.files); e.target.value = ""; };
    ["dragenter", "dragover"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("over"); }));
    ["dragleave", "drop"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
    drop.addEventListener("drop", (e) => scanFiles(e.dataTransfer.files));
    root.addEventListener("error", (e) => {  // portrait fallback
      const i = e.target; if (i.tagName !== "IMG") return;
      const n = +(i.dataset.try || 0); i.dataset.try = n + 1;
      if (n === 0 && i.dataset.f) i.src = i.dataset.f;
    }, true);
  };
})();

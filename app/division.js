/* Composant commun des pages de division. Chaque division fournit le même JSON (pipeline/build_divisions.py),
   la page n'a donc rien à réécrire quand un indicateur ou une division s'ajoute. */
(function () {
  const fmt = (x, d = 1) => x == null ? "—" : Number(x).toLocaleString("fr-FR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const clean = s => s.toLowerCase().normalize("NFD").replace(/\p{Diacritic}/gu, "");
  const STAT = { zero_reel: "zéro réel", estime: "estimé", convention: "convention", manquant: "manquant", non_publie: "non publié", confidentiel: "confidentiel" };
  const AVAIL = { "disponible": "ok", "non collecté": "vis", "non publié par province": "vis", "à définir": "dev" };
  const $ = id => document.getElementById(id);
  const digits = c => c.unite.startsWith("établissements") ? 0 : c.unite === "pour 1 000 hab." || c.unite === "pour 100 000 hab." ? 2 : 1;

  function render(D, GEO) {
    const T = D.territoires, C = D.colonnes, key = c => c.indicator_id;
    const quant = (arr, q) => { const s = [...arr].sort((a, b) => a - b), i = (s.length - 1) * q, lo = Math.floor(i); return s[lo] + (s[Math.ceil(i)] - s[lo]) * (i - lo); };
    const median = c => quant(T.map(t => t.valeurs[key(c)]).filter(v => v != null), .5);
    const flag = (t, c) => t.statuts[key(c)] ? ` <span class="stat dev" title="${esc(t.statuts[key(c)].note)}">${STAT[t.statuts[key(c)].statut]}</span>` : "";

    // Chiffres clés
    const cat = D.indicateurs, ok = cat.filter(i => i.disponibilite === "disponible");
    const years = cat.flatMap(i => i.periodes || []);
    $("d-figs").innerHTML = [[`${ok.length}/${cat.length}`, "indicateurs du catalogue disponibles"], [T.length, "provinces et préfectures"], [D.jeux.length, "jeux de données ingérés"], [years.length ? years.sort().at(-1) : "—", "dernière année observée"]]
      .map(([v, l]) => `<div><b>${v}</b><span>${l}</span></div>`).join("");

    // Catalogue
    $("d-cat").innerHTML = `<tr><th>Code</th><th>Indicateur</th><th>Sous-domaine</th><th>État</th><th class="n">Couverture</th><th>Années</th><th>Sources</th></tr>` + cat.map(i =>
      `<tr><td>${i.indicator_id}</td><td>${esc(i.nom)}${i.indicateur_rafah ? ` <small>(indice Rafah : ${i.indicateur_rafah})</small>` : ""}<br><small>${esc(i.formule)}${i.note ? ". " + esc(i.note) : ""}</small></td><td>${esc(i.sous_domaine)}</td>` +
      `<td><span class="stat ${AVAIL[i.disponibilite] || "vis"}">${esc(i.disponibilite)}</span></td><td class="n">${i.couverture_pct != null ? fmt(i.couverture_pct, 0) + " %" : i.niveau === "National" ? "national" : "—"}</td>` +
      `<td>${(i.periodes || []).join(", ") || "—"}</td><td>${esc((i.sources || "").replaceAll(";", ", ")) || "—"}</td></tr>`).join("");

    // Sélecteurs
    const opts = C.map((c, n) => `<option value="${n}">${esc(c.nom)} (${c.periode})</option>`).join("");
    $("d-ind").innerHTML = opts;
    const byName = [...T].sort((a, b) => a.nom.localeCompare(b.nom, "fr"));
    $("d-terr").innerHTML = byName.map(t => `<option value="${t.territory_id}">${esc(t.nom)}</option>`).join("");
    const regions = [...new Set(T.map(t => t.region))].sort((a, b) => a.localeCompare(b, "fr"));
    $("d-region").innerHTML = `<option value="">Toutes</option>` + regions.map(r => `<option>${esc(r)}</option>`).join("");

    // Carte : quintiles d'une seule teinte, pour décrire sans juger.
    const k = Math.cos(29 * Math.PI / 180), x0 = -17.6, y1 = 36.1;
    const pts = r => "M" + r.map(c => `${((c[0] - x0) * k * 6).toFixed(1)} ${((y1 - c[1]) * 6).toFixed(1)}`).join("L") + "Z";
    const shapes = GEO.features.map(f => { const g = f.geometry, polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates; return { id: String(f.properties.code), d: polys.map(p => p.map(pts).join("")).join("") }; });
    function drawMap() {
      const c = C[$("d-ind").value], vals = T.map(t => t.valeurs[key(c)]).filter(v => v != null);
      const cuts = [.2, .4, .6, .8].map(q => quant(vals, q)), by = Object.fromEntries(T.map(t => [t.territory_id, t]));
      const cls = v => v == null ? -1 : cuts.filter(x => v > x).length;
      const W = (17.6 - .9) * k * 6, H = (36.1 - 20.6) * 6;
      $("d-map").innerHTML = `<svg viewBox="0 0 ${W.toFixed(0)} ${H.toFixed(0)}" role="img" aria-label="Carte : ${esc(c.nom)}">` + shapes.map(s => {
        const t = by[s.id], v = t.valeurs[key(c)], q = cls(v);
        return `<path d="${s.d}" data-id="${s.id}" fill="${q < 0 ? "var(--line)" : "var(--accent)"}" fill-opacity="${q < 0 ? 1 : (.14 + q * .2).toFixed(2)}" stroke="var(--land-line)" stroke-width=".35" style="cursor:pointer"><title>${esc(t.nom)} : ${fmt(v, digits(c))} ${esc(c.unite)}</title></path>`;
      }).join("") + "</svg>";
      const edges = [Math.min(...vals), ...cuts, Math.max(...vals)];
      $("d-legend").innerHTML = [0, 1, 2, 3, 4].map(q => `<span><b style="background:var(--accent);opacity:${(.14 + q * .2).toFixed(2)}"></b>${fmt(edges[q], digits(c))} à ${fmt(edges[q + 1], digits(c))}</span>`).join("") + ` <span>${esc(c.unite)}, quintiles</span>`;
    }
    $("d-map").addEventListener("click", e => { const p = e.target.closest("path"); if (p) { $("d-terr").value = p.dataset.id; profile(); $("profil").scrollIntoView({ behavior: "smooth" }); } });

    // Profil territorial
    function profile() {
      const t = T.find(x => x.territory_id === $("d-terr").value);
      $("d-profile").innerHTML = `<h3>${esc(t.nom)}</h3><p class="fine">${esc(t.region)} · ${fmt(t.population, 0)} habitants (RGPH 2024)</p><div class="scroll"><table><tr><th>Indicateur</th><th class="n">Valeur</th><th class="n">Médiane des 75</th><th class="n">Rang (1 = plus élevé)</th></tr>` +
        C.map(c => { const v = t.valeurs[key(c)], rank = 1 + T.filter(x => x.valeurs[key(c)] > v).length;
          return `<tr><td>${esc(c.nom)} <small>(${c.periode})</small>${flag(t, c)}</td><td class="n">${fmt(v, digits(c))}</td><td class="n">${fmt(median(c), digits(c))}</td><td class="n">${v == null ? "—" : rank + " / " + T.length}</td></tr>`; }).join("") +
        `</table></div>` + (Object.keys(t.statuts).length ? `<p class="fine">${Object.entries(t.statuts).map(([i, s]) => `${i} : ${esc(s.note)}`).join(" ")}</p>` : "");
    }

    // Tableau de comparaison
    const state = { k: 0, dir: -1 };
    const rows = () => { const r = $("d-region").value, q = clean($("d-q").value.trim()), c = C[state.k];
      return T.filter(t => (!r || t.region === r) && (!q || clean(t.nom).includes(q))).sort((a, b) => state.k < 0 ? a.nom.localeCompare(b.nom, "fr") * state.dir : ((a.valeurs[key(c)] ?? -1) - (b.valeurs[key(c)] ?? -1)) * state.dir); };
    function table() {
      const data = rows();
      $("d-count").textContent = `${data.length} territoire${data.length > 1 ? "s" : ""} sur ${T.length}`;
      $("d-table").innerHTML = `<tr><th><button type="button" data-k="-1">Territoire</button></th><th>Région</th>${C.map((c, n) => `<th class="n"><button type="button" data-k="${n}">${esc(c.nom)} (${c.periode})${state.k === n ? (state.dir > 0 ? " ↑" : " ↓") : ""}</button></th>`).join("")}</tr>` +
        data.map(t => `<tr><td>${esc(t.nom)}</td><td>${esc(t.region)}</td>${C.map(c => `<td class="n">${fmt(t.valeurs[key(c)], digits(c))}${t.statuts[key(c)] ? " *" : ""}</td>`).join("")}</tr>`).join("");
    }
    $("d-table").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; const n = +b.dataset.k; if (state.k === n) state.dir *= -1; else { state.k = n; state.dir = n < 0 ? 1 : -1; } table(); });
    for (const id of ["d-region", "d-q"]) $(id).addEventListener("input", table);
    $("d-export").onclick = () => {
      const q = s => `"${String(s).replace(/"/g, '""')}"`;
      const csv = "﻿" + [["code_hcp", "territoire", "region", ...C.map(c => `${c.indicator_id}_${c.periode}`), "statuts_particuliers"].map(q).join(";"),
        ...rows().map(t => [t.territory_id, q(t.nom), q(t.region), ...C.map(c => t.valeurs[key(c)] == null ? "" : String(t.valeurs[key(c)]).replace(".", ",")), q(Object.entries(t.statuts).map(([i, s]) => `${i}: ${s.statut}`).join(" | "))].join(";"))].join("\n");
      const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); a.download = `rafah_${D.id}.csv`; document.body.append(a); a.click(); a.remove();
    };

    // Évolution, inégalités, signaux, sources
    $("d-evo").innerHTML = D.evolution.map(e => `<div class="card"><h3>${esc(e.nom)}</h3><p><b>${fmt(e.total["2024"], 0)}</b> en 2024, <b>${fmt(e.total["2025"], 0)}</b> en 2025 : ${e.hausses} territoires en hausse, ${e.baisses} en baisse, ${e.stables} stables.</p>` +
      (e.plus_fortes_variations.length ? `<table><tr><th>Territoire</th><th class="n">2024</th><th class="n">2025</th></tr>${e.plus_fortes_variations.map(v => `<tr><td>${esc(v.territoire)}</td><td class="n">${v["2024"]}</td><td class="n">${v["2025"]}</td></tr>`).join("")}</table>` : "") + `</div>`).join("");
    $("d-ineq").innerHTML = `<tr><th>Indicateur</th><th class="n">Gini pondéré</th><th class="n">Rapport P90 / P10</th><th>Valeur la plus faible</th><th>Valeur la plus élevée</th></tr>` + D.inegalites.map(i =>
      `<tr><td>${esc(i.nom)} (${i.periode})</td><td class="n"><b>${fmt(i.gini, 2)}</b></td><td class="n">${i.rapport_p90_p10 != null ? fmt(i.rapport_p90_p10) : "—"}</td><td>${esc(i.min.territoire)} (${fmt(i.min.valeur, 2)})</td><td>${esc(i.max.territoire)} (${fmt(i.max.valeur, 2)})</td></tr>`).join("");
    $("d-flags").innerHTML = `<tr><th>Territoire</th><th>Région</th><th class="n">Habitants</th><th>Signaux</th></tr>` + D.signaux.map(f => `<tr><td>${esc(f.nom)}</td><td>${esc(f.region)}</td><td class="n">${fmt(f.population, 0)}</td><td>${f.signaux.map(esc).join(" ; ")}</td></tr>`).join("");
    $("d-flags-n").textContent = D.signaux.length;
    $("d-src").innerHTML = `<tr><th>Code</th><th>Jeu de données</th><th>Producteur</th><th>Année</th><th>Mis en ligne</th><th title="A officiel téléchargeable, B publication officielle, C plateforme interactive officielle, D source secondaire, E estimé">Classe</th><th>Licence</th></tr>` + D.sources.map(s => `<tr><td>${s.source_id}</td><td><a href="${esc(s.original_url)}" rel="noopener">${esc(s.dataset_name)}</a></td><td>${esc(s.producer)}</td><td>${esc(s.reference_year)}</td><td>${esc(s.published_on)}</td><td>${esc(s.quality_class)}</td><td>${esc(s.licence)}</td></tr>`).join("");
    $("d-jeux").innerHTML = `<tr><th>Jeu ingéré</th><th>Source</th><th class="n">Observations</th><th>Années</th><th>Empreinte SHA-256</th><th>Ingéré le</th></tr>` + D.jeux.map(j => `<tr><td>${esc(j.description)}</td><td>${j.source_id}</td><td class="n">${j.observations}</td><td>${esc(j.periodes)}</td><td><code title="${j.sha256}">${j.sha256.slice(0, 12)}…</code></td><td>${j.ingere_le}</td></tr>`).join("");

    $("d-ind").addEventListener("input", drawMap);
    $("d-terr").addEventListener("input", profile);
    $("d-terr").value = byName[0].territory_id;
    drawMap(); profile(); table();
  }
  window.RafahDivision = { render };
})();

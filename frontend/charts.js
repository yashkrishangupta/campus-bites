// ==========================================
// CAMPUSBITES - REVIEW CHARTS (plain SVG / CSS, no libraries)
// ==========================================

const RATING_COLORS = { 1: "#d6573d", 2: "#e8894a", 3: "#f2b84b", 4: "#9ac45a", 5: "#4a9d5c" };
const SHOP_COLORS = ["#e87532", "#2f7d8c", "#7b5ea7", "#4a9d5c", "#d6573d", "#c9a227", "#5d7a8c", "#a14b6b"];

// Horizontal bars. rows: [{label, value, note, color}]
function drawBars(el, rows, { max = 5 } = {}) {
    if (!rows.length) { el.innerHTML = '<p class="muted">Nothing to show yet.</p>'; return; }
    el.innerHTML = `<div class="hbars">${rows.map(r => `
        <div class="hbar">
            <span class="lbl" title="${escapeHTML(r.label)}">${escapeHTML(r.label)}</span>
            <span class="track"><span class="fill" style="width:${Math.max(2, (r.value / max) * 100)}%;${r.color ? `background:${r.color}` : ""}"></span></span>
            <span class="val">${r.value.toFixed(1)} <small>${escapeHTML(r.note || "")}</small></span>
        </div>`).join("")}</div>`;
}

// Rating breakdown (5 stars to 1 star)
function drawDistribution(el, distribution, total) {
    el.innerHTML = `<div class="hbars">${[5, 4, 3, 2, 1].map(n => {
        const count = distribution[n] || 0;
        const pct = total ? (count / total) * 100 : 0;
        return `<div class="hbar" style="grid-template-columns:40px 1fr 70px">
            <span class="lbl">${n} ★</span>
            <span class="track"><span class="fill" style="width:${pct}%;background:${RATING_COLORS[n]}"></span></span>
            <span class="val">${count} <small>${Math.round(pct)}%</small></span></div>`;
    }).join("")}</div>`;
}

// Donut: happy / okay / unhappy
function drawDonut(el, totals) {
    const parts = [
        { label: "Loved it (4-5★)", value: totals.positive, color: RATING_COLORS[5] },
        { label: "It was okay (3★)", value: totals.neutral, color: RATING_COLORS[3] },
        { label: "Not great (1-2★)", value: totals.negative, color: RATING_COLORS[1] }
    ];
    const sum = parts.reduce((s, p) => s + p.value, 0);
    const R = 52, C = 2 * Math.PI * R;
    let offset = 0;

    const arcs = sum ? parts.map(p => {
        const len = (p.value / sum) * C;
        const circle = `<circle cx="70" cy="70" r="${R}" fill="none" stroke="${p.color}" stroke-width="22"
            stroke-dasharray="${len} ${C - len}" stroke-dashoffset="${-offset}" transform="rotate(-90 70 70)"><title>${p.label}: ${p.value}</title></circle>`;
        offset += len;
        return circle;
    }).join("") : `<circle cx="70" cy="70" r="${R}" fill="none" stroke="#f4eee8" stroke-width="22"/>`;

    el.innerHTML = `<div class="donut-wrap">
        <svg viewBox="0 0 140 140" role="img" aria-label="Share of positive, neutral and negative reviews">${arcs}
            <text x="70" y="68" text-anchor="middle" style="font-size:26px;font-weight:800;fill:#33251e">${sum ? Math.round(parts[0].value / sum * 100) + "%" : "–"}</text>
            <text x="70" y="86" text-anchor="middle">happy</text></svg>
        <div class="legend" style="flex-direction:column;gap:8px;margin:0">${parts.map(p =>
            `<span><i style="background:${p.color}"></i>${p.label}: <b style="color:#33251e">${p.value}</b></span>`).join("")}</div></div>`;
}

// Reviews per day (bars) + average rating (line)
function drawTrend(el, trend) {
    const W = 640, H = 230, L = 34, R = 34, T = 14, B = 30;
    const iw = W - L - R, ih = H - T - B;
    const maxCount = Math.max(1, ...trend.map(d => d.count));
    const step = iw / trend.length;
    const x = i => L + step * i + step / 2;
    const yCount = v => T + ih - (v / maxCount) * ih;
    const yRate = v => T + ih - ((v - 1) / 4) * ih;

    const bars = trend.map((d, i) => d.count
        ? `<rect x="${x(i) - step * .35}" y="${yCount(d.count)}" width="${step * .7}" height="${T + ih - yCount(d.count)}" rx="3" fill="#f6c9a7"><title>${d.date}: ${d.count} reviews</title></rect>` : "").join("");

    const pts = trend.map((d, i) => d.average != null ? [x(i), yRate(d.average), d] : null).filter(Boolean);
    const line = pts.length > 1 ? `<polyline fill="none" stroke="#33251e" stroke-width="2" stroke-linejoin="round" points="${pts.map(p => p[0] + "," + p[1]).join(" ")}"/>` : "";
    const dots = pts.map(p => `<circle cx="${p[0]}" cy="${p[1]}" r="3.5" fill="#33251e"><title>${p[2].date}: average ${p[2].average}★</title></circle>`).join("");

    const grid = [1, 2, 3, 4, 5].map(v => `<line x1="${L}" x2="${W - R}" y1="${yRate(v)}" y2="${yRate(v)}" stroke="#f1e8de"/>
        <text x="${W - R + 6}" y="${yRate(v) + 4}">${v}★</text>`).join("");
    const left = [0, Math.ceil(maxCount / 2), maxCount].map(v => `<text x="${L - 6}" y="${yCount(v) + 4}" text-anchor="end">${v}</text>`).join("");
    const labelEvery = Math.ceil(trend.length / 6);
    const xs = trend.map((d, i) => i % labelEvery === 0 || i === trend.length - 1
        ? `<text x="${x(i)}" y="${H - 8}" text-anchor="middle">${new Date(d.date + "T00:00").toLocaleDateString(undefined, { day: "numeric", month: "short" })}</text>` : "").join("");

    el.innerHTML = `<svg class="chart-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Reviews per day and average rating">${grid}${bars}${line}${dots}${left}${xs}</svg>
        <div class="legend"><span><i style="background:#f6c9a7;border-radius:2px"></i>Reviews per day</span><span><i style="background:#33251e"></i>Average rating</span></div>`;
}

// Price (x) vs average rating (y); bubble size = number of reviews
function drawScatter(el, points) {
    if (!points.length) { el.innerHTML = '<p class="muted">Nothing to show yet.</p>'; return; }
    const W = 640, H = 300, L = 40, R = 16, T = 14, B = 36;
    const iw = W - L - R, ih = H - T - B;
    const maxPrice = Math.max(...points.map(p => p.price));
    const top = Math.ceil(maxPrice / 50) * 50 || 50;
    const x = v => L + (v / top) * iw;
    const y = v => T + ih - ((v - 1) / 4) * ih;

    const shops = [...new Set(points.map(p => p.shop))].sort();
    const color = shop => SHOP_COLORS[shops.indexOf(shop) % SHOP_COLORS.length];

    const grid = [1, 2, 3, 4, 5].map(v => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="#f1e8de"/>
        <text x="${L - 8}" y="${y(v) + 4}" text-anchor="end">${v}★</text>`).join("");
    const ticks = Array.from({ length: top / 50 + 1 }, (_, i) => i * 50).map(v =>
        `<text x="${x(v)}" y="${H - 14}" text-anchor="middle">₹${v}</text>`).join("");

    const dots = points.map(p => `<circle cx="${x(p.price)}" cy="${y(p.average_rating)}" r="${4 + Math.sqrt(p.total_reviews) * 2}"
        fill="${color(p.shop)}" fill-opacity=".6" stroke="${color(p.shop)}"><title>${escapeHTML(p.name)} (${escapeHTML(p.shop)})
₹${p.price} · ${p.average_rating}★ from ${p.total_reviews} review(s)</title></circle>`).join("");

    el.innerHTML = `<svg class="chart-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Price versus rating for each reviewed dish">${grid}${ticks}${dots}</svg>
        <div class="legend">${shops.map(s => `<span><i style="background:${color(s)}"></i>${escapeHTML(s)}</span>`).join("")}<span>Bigger bubble = more reviews</span></div>`;
}

// Simple ranked list: [{name, shop, average_rating, total_reviews, price}]
function drawLeaderboard(el, items, emptyText) {
    if (!items.length) { el.innerHTML = `<p class="muted">${emptyText}</p>`; return; }
    el.innerHTML = `<ul class="leader">${items.map(i => `
        <li><span><b>${escapeHTML(i.name)}</b><small>${escapeHTML(i.shop)} · ${money(i.price)}</small></span>
        ${ratingPill(i.average_rating, i.total_reviews)}</li>`).join("")}</ul>`;
}

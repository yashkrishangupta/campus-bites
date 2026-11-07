// ==========================================
// CAMPUSBITES - SHARED JAVASCRIPT (all pages)
// ==========================================

// If the site is opened from the backend (http://127.0.0.1:8000/app/) use the
// same server, otherwise (file or Live Server) talk to the local backend.
const API_URL =
    ["localhost", "127.0.0.1"].includes(location.hostname)
        ? (location.port === "8000" ? "" : "http://127.0.0.1:8000")
        : "";

const SHOP_EMOJI = {
    "Annapurna": "🍛", "Appetite Rolls": "🌯", "Chai Garam": "☕",
    "Food Court": "🍽️", "Frisco": "🍦", "Tulips": "🍰"
};
const COURSE_EMOJI = { meal: "🍛", snack: "🥨", drink: "🥤", dessert: "🍰" };
const RATING_WORDS = ["", "Poor", "Average", "Good", "Very good", "Excellent"];


// ---------- Small helpers ----------

const $ = (selector, root = document) => root.querySelector(selector);

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, c => (
        { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c]
    ));
}

const money = n => "₹" + (Number.isInteger(+n) ? +n : (+n).toFixed(2));
const shopEmoji = name => SHOP_EMOJI[name] || "🍴";

async function api(path, options) {
    let response;
    try {
        response = await fetch(API_URL + path, options);
    } catch (e) {
        throw new Error("Cannot reach the server. Is the backend running?");
    }
    let data = null;
    try { data = await response.json(); } catch (e) { /* no body */ }

    if (!response.ok) {
        const d = data && data.detail;
        throw new Error(
            typeof d === "string" ? d : (Array.isArray(d) && d[0]?.msg) || "Something went wrong."
        );
    }
    return data;
}

function starsHTML(value) {
    const full = Math.round(value || 0);
    return `<span class="stars" aria-label="${full} out of 5">${"★".repeat(full)}<span class="off">${"★".repeat(5 - full)}</span></span>`;
}

function ratingPill(avg, count) {
    if (avg == null) return '<span class="rating-pill none">No reviews yet</span>';
    return `<span class="rating-pill">★ ${Number(avg).toFixed(1)} <small>(${count})</small></span>`;
}

function timeAgo(iso) {
    if (!iso) return "";
    const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + "Z");
    const days = Math.floor((Date.now() - d) / 86400000);
    if (days <= 0) return "today";
    if (days === 1) return "yesterday";
    if (days < 30) return `${days} days ago`;
    return d.toLocaleDateString();
}

function toast(message) {
    const t = $("#toast");
    t.textContent = message;
    t.classList.add("show");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => t.classList.remove("show"), 2800);
}


// ---------- Page chrome: navigation, footer, popup ----------

function renderChrome() {
    const page = document.body.dataset.page;
    const link = (href, key, text) =>
        `<a href="${href}" class="${page === key ? "active" : ""}">${text}</a>`;

    document.body.insertAdjacentHTML("afterbegin", `
        <header class="navbar">
            <a href="index.html" class="logo">Campus<span>Bites.</span><small>UPES FOOD DISCOVERY</small></a>
            <button class="menu-toggle" id="menuToggle" aria-label="Menu">☰</button>
            <nav class="nav-links" id="navLinks">
                ${link("index.html", "home", "Home")}
                ${link("index.html#shops", "shop", "Food Shops")}
                ${link("meal.html", "meal", "Find Meal")}
                ${link("reviews.html", "reviews", "Reviews")}
            </nav>
            <a href="reviews.html#give" class="nav-button">Give Review ★</a>
        </header>`);

    document.body.insertAdjacentHTML("beforeend", `
        <footer class="footer">
            <h2>Campus<span>Bites.</span></h2>
            <p>Discover. Compare. Eat.</p>
            <p>Made for UPES students.</p>
        </footer>
        <div id="modal" class="modal" role="dialog" aria-modal="true">
            <div class="modal-content">
                <button class="close-button" type="button" aria-label="Close">×</button>
                <div id="modalBody"></div>
            </div>
        </div>
        <div id="toast" class="toast" role="status" aria-live="polite"></div>`);

    $("#menuToggle").addEventListener("click", () => $("#navLinks").classList.toggle("open"));
    $("#modal .close-button").addEventListener("click", closeModal);
    $("#modal").addEventListener("click", e => { if (e.target.id === "modal") closeModal(); });
    document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });
}

function openModal(html) {
    $("#modalBody").innerHTML = html;
    $("#modal").classList.add("open");
    return $("#modalBody");
}

function closeModal() {
    $("#modal").classList.remove("open");
}


// ---------- SEE REVIEWS popup ----------

function distributionHTML(distribution, total) {
    return [5, 4, 3, 2, 1].map(n => {
        const count = distribution[n] || 0;
        const pct = total ? (count / total) * 100 : 0;
        return `<div class="hbar"><span class="lbl">${n} ★</span>
            <span class="track"><span class="fill" style="width:${pct}%"></span></span>
            <span class="val">${count}</span></div>`;
    }).join("");
}

async function openReviews(item) {
    const body = openModal(`<h2>${escapeHTML(item.name)}</h2><p class="loading-message">Loading reviews...</p>`);

    try {
        const data = await api(`/items/${item.id}/reviews`);

        const list = data.reviews.length
            ? data.reviews.map(r => `
                <div class="review-card">
                    <div class="top"><strong>${escapeHTML(r.student_name)}</strong>${starsHTML(r.rating)}</div>
                    <p>${escapeHTML(r.comment || "")}</p>
                    <small>${timeAgo(r.created_at)}</small>
                </div>`).join("")
            : '<div class="empty-box">No reviews yet. Be the first to review this dish!</div>';

        body.innerHTML = `
            <h2>${escapeHTML(data.food_item)}</h2>
            <p class="muted">${escapeHTML(data.shop_name)} · ${money(data.price)}</p>
            ${data.total_reviews ? `
            <div class="review-summary">
                <div><div class="score">${data.average_rating.toFixed(1)}</div>
                    ${starsHTML(data.average_rating)}<div class="muted" style="font-size:13px">${data.total_reviews} review${data.total_reviews > 1 ? "s" : ""}</div></div>
                <div class="dist">${distributionHTML(data.distribution, data.total_reviews)}</div>
            </div>` : ""}
            <button class="primary-button" id="writeFromList" type="button">Write a review</button>
            <div class="review-list">${list}</div>`;

        $("#writeFromList").addEventListener("click", () => openReviewForm(item));

    } catch (error) {
        body.innerHTML = `<h2>${escapeHTML(item.name)}</h2><p class="empty-message">${escapeHTML(error.message)}</p>`;
    }
}


// ---------- WRITE A REVIEW popup ----------

// Star picker used in the popup and on the Reviews page
function mountStarPicker(container, onChange) {
    container.innerHTML = `<div class="star-picker">${[1, 2, 3, 4, 5].map(n =>
        `<button type="button" data-v="${n}" aria-label="${n} star${n > 1 ? "s" : ""}">★</button>`).join("")}
        <span class="star-label">Tap to rate</span></div>`;
    const buttons = container.querySelectorAll("button");
    const label = container.querySelector(".star-label");
    const picker = { value: 0 };

    buttons.forEach(b => b.addEventListener("click", () => {
        picker.value = +b.dataset.v;
        buttons.forEach(x => x.classList.toggle("on", +x.dataset.v <= picker.value));
        label.textContent = RATING_WORDS[picker.value];
        if (onChange) onChange(picker.value);
    }));
    picker.reset = () => {
        picker.value = 0;
        buttons.forEach(x => x.classList.remove("on"));
        label.textContent = "Tap to rate";
    };
    return picker;
}

// Sends a review to the backend. Shared by the popup and the Reviews page.
async function sendReview(itemId, name, rating, comment) {
    const result = await api(`/items/${itemId}/reviews`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_name: name, rating, comment })
    });
    try { localStorage.setItem("cb_name", name); } catch (e) { /* ignore */ }
    document.dispatchEvent(new CustomEvent("review-added", { detail: { itemId } }));
    return result;
}

function savedName() {
    try { return localStorage.getItem("cb_name") || ""; } catch (e) { return ""; }
}

function openReviewForm(item) {
    const body = openModal(`
        <h2>Review: ${escapeHTML(item.name)}</h2>
        <p class="muted">${escapeHTML(item.shop_name || "")}</p>
        <form id="popupForm" novalidate>
            <label class="field">Your rating</label>
            <div id="popupStars"></div>
            <label class="field" for="popupName">Your name</label>
            <input type="text" id="popupName" maxlength="100" placeholder="e.g. Aarav" value="${escapeHTML(savedName())}">
            <label class="field" for="popupComment">Your review</label>
            <textarea id="popupComment" rows="4" maxlength="1000" placeholder="How was the taste, portion and value?"></textarea>
            <button type="submit" class="primary-button" style="margin-top:18px">Submit review</button>
            <p class="form-message" id="popupMsg" aria-live="polite"></p>
        </form>`);

    const picker = mountStarPicker($("#popupStars", body));

    $("#popupForm", body).addEventListener("submit", async event => {
        event.preventDefault();
        const name = $("#popupName", body).value.trim();
        const comment = $("#popupComment", body).value.trim();
        const msg = $("#popupMsg", body);
        const button = $("button[type=submit]", body);

        msg.className = "form-message err";
        if (!picker.value) { msg.textContent = "Please choose a star rating."; return; }
        if (name.length < 2) { msg.textContent = "Please enter your name."; return; }
        if (comment.length < 2) { msg.textContent = "Please write a short review."; return; }

        button.disabled = true;
        button.textContent = "Submitting...";
        try {
            await sendReview(item.id, name, picker.value, comment);
            closeModal();
            toast("Thanks! Your review was added ★");
        } catch (error) {
            msg.textContent = error.message;
            button.disabled = false;
            button.textContent = "Submit review";
        }
    });
}


// ---------- Menu item card (used on shop page and meal finder) ----------

function menuItemCard(item, { showShop = false } = {}) {
    const el = document.createElement("div");
    el.className = "menu-item";
    el.innerHTML = `
        <div class="row">
            <h4>${escapeHTML(item.name)}</h4>
            <span class="price">${money(item.price)}</span>
        </div>
        <div class="meta">
            ${ratingPill(item.average_rating, item.total_reviews)}
            <span>${showShop ? "📍 " + escapeHTML(item.shop_name) + " · " : ""}${escapeHTML(item.category || "Other")}</span>
        </div>
        <div class="item-actions">
            <button type="button" class="ghost-button small-button" data-act="see">See Reviews</button>
            <button type="button" class="secondary-button small-button" data-act="write">Review</button>
        </div>`;
    $('[data-act="see"]', el).addEventListener("click", () => openReviews(item));
    $('[data-act="write"]', el).addEventListener("click", () => openReviewForm(item));
    return el;
}

document.addEventListener("DOMContentLoaded", renderChrome);

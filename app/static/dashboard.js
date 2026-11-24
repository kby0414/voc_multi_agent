"use strict";

const endpoints = {
  vocs: "/api/v1/vocs?offset=0&limit=1",
  issues: "/api/v1/issues",
  priorities: "/api/v1/priorities",
  inbox: "/api/v1/admin/vocs?offset=0&limit=1",
  classify: "/api/v1/analysis/classify?limit=5000",
  recalculate: "/api/v1/priorities/recalculate",
};

const number = new Intl.NumberFormat("ko-KR");
const $ = (selector) => document.querySelector(selector);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

async function request(url, options = {}) {
  const headers = { Accept: "application/json", ...(options.headers || {}) };
  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let message = `요청 실패 (${response.status})`;
    try { message = (await response.json()).detail || message; } catch (_) { /* 응답 본문 없음 */ }
    throw new Error(message);
  }
  return response.json();
}

function showToast(message, isError = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 3200);
}

function trendClass(rate) {
  return rate > 0 ? "trend-up" : rate < 0 ? "trend-down" : "trend-flat";
}

function trendText(rate) {
  if (rate > 0) return `▲ ${number.format(rate)}%`;
  if (rate < 0) return `▼ ${number.format(Math.abs(rate))}%`;
  return "— 0%";
}

function renderMetrics(vocTotal, issueTotal, items) {
  $("#metric-vocs").textContent = number.format(vocTotal);
  $("#metric-issues").textContent = number.format(issueTotal);
  $("#metric-critical").textContent = number.format(items.filter((item) => ["P0", "P1"].includes(item.priority_grade)).length);
  const growing = [...items].sort((a, b) => b.growth_rate_percent - a.growth_rate_percent)[0];
  $("#metric-growing").textContent = growing ? `${number.format(growing.growth_rate_percent)}%` : "—";
  $("#metric-growing-label").textContent = growing ? growing.topic : "비교 데이터 없음";
}

function renderPriorities(items) {
  const body = $("#priority-rows");
  $("#empty-state").hidden = items.length > 0;
  body.innerHTML = items.map((item) => `
    <tr>
      <td class="rank">${String(item.priority_rank).padStart(2, "0")}</td>
      <td class="issue-title"><strong>${escapeHtml(item.topic)}</strong><small>${escapeHtml(item.category)} · ${escapeHtml(item.issue_title)}</small></td>
      <td><span class="grade grade-${escapeHtml(item.priority_grade.toLowerCase())}">${escapeHtml(item.priority_grade)}</span></td>
      <td>${escapeHtml(item.severity_level)} <span class="rank">${item.severity_score.toFixed(2)}/5</span></td>
      <td>${number.format(item.inquiry_count)}건</td>
      <td class="${trendClass(item.growth_rate_percent)}">${trendText(item.growth_rate_percent)}</td>
      <td class="score">${item.priority_score.toFixed(2)}</td>
    </tr>`).join("");
}

function renderCategories(items) {
  const totals = items.reduce((acc, item) => {
    acc[item.category] = (acc[item.category] || 0) + item.inquiry_count;
    return acc;
  }, {});
  const rows = Object.entries(totals).sort((a, b) => b[1] - a[1]);
  const max = Math.max(...rows.map(([, count]) => count), 1);
  $("#category-chart").innerHTML = rows.length ? rows.map(([category, count]) => `
    <div class="category-row">
      <span>${escapeHtml(category)}</span><div class="bar"><div class="fill" style="width:${(count / max) * 100}%"></div></div><b>${number.format(count)}건</b>
    </div>`).join("") : '<div class="empty-state"><span>표시할 분류 데이터가 없습니다.</span></div>';
}

function renderTrends(items) {
  const max = Math.max(...items.flatMap((item) => [item.recent_7d_count, item.previous_7d_count]), 1);
  $("#trend-list").innerHTML = items.length ? items.slice(0, 6).map((item) => `
    <div class="trend-item">
      <div><strong>${escapeHtml(item.topic)}</strong><small>최근 ${item.recent_7d_count}건 / 직전 ${item.previous_7d_count}건</small></div>
      <div class="trend-bars" aria-label="${escapeHtml(item.topic)} 기간별 문의량">
        <div class="bar"><div class="recent" style="width:${(item.recent_7d_count / max) * 100}%"></div></div>
        <div class="bar"><div class="previous" style="width:${(item.previous_7d_count / max) * 100}%"></div></div>
      </div>
      <span class="trend-value ${trendClass(item.growth_rate_percent)}">${trendText(item.growth_rate_percent)}</span>
    </div>`).join("") : '<div class="empty-state"><span>표시할 추세 데이터가 없습니다.</span></div>';
}

async function loadDashboard() {
  const [vocs, issues, priorities, inbox] = await Promise.all([
    request(endpoints.vocs), request(endpoints.issues), request(endpoints.priorities), request(endpoints.inbox),
  ]);
  const items = priorities.items || [];
  renderMetrics(vocs.total, issues.total, items);
  renderPriorities(items);
  renderCategories(items);
  renderTrends(items);
  const inboxBadge = $("#sidebar-inbox-badge");
  inboxBadge.textContent = number.format(inbox.recent_count);
  inboxBadge.hidden = inbox.recent_count === 0;
  const time = priorities.as_of_utc ? new Date(`${priorities.as_of_utc}Z`).toLocaleString("ko-KR") : "계산 전";
  $("#last-updated").textContent = `분석 기준: ${time}`;
}

async function runAction(button, action) {
  button.disabled = true;
  try { await action(); await loadDashboard(); }
  catch (error) { showToast(error.message, true); }
  finally { button.disabled = false; }
}

$("#recalculate").addEventListener("click", (event) => runAction(event.currentTarget, async () => {
  await request(endpoints.recalculate, { method: "POST" });
  showToast("우선순위를 다시 계산했습니다.");
}));

$("#run-analysis").addEventListener("click", (event) => runAction(event.currentTarget, async () => {
  const result = await request(endpoints.classify, { method: "POST" });
  await request(endpoints.recalculate, { method: "POST" });
  showToast(`분류 ${number.format(result.processed_count)}건을 반영했습니다.`);
}));

loadDashboard().catch((error) => {
  $("#last-updated").textContent = "데이터 연결을 확인해 주세요.";
  showToast(error.message, true);
});

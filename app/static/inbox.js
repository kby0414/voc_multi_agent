"use strict";

const number = new Intl.NumberFormat("ko-KR");
const dateTime = new Intl.DateTimeFormat("ko-KR", {
  month: "numeric", day: "numeric", hour: "numeric", minute: "2-digit",
});
const $ = (selector) => document.querySelector(selector);
let items = [];
let selectedId = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

function formatUtc(value) {
  if (!value) return "—";
  return dateTime.format(new Date(`${value}Z`));
}

function statusClass(status) {
  if (status === "분석 완료") return "status-complete";
  if (status === "검토 필요") return "status-review";
  return "status-pending";
}

function filteredItems() {
  const query = $("#inbox-search").value.trim().toLowerCase();
  if (!query) return items;
  return items.filter((item) => [
    item.receipt_number, item.game_name, item.platform, item.content_masked,
    item.category, item.topic,
  ].some((value) => String(value || "").toLowerCase().includes(query)));
}

function renderList() {
  const visibleItems = filteredItems();
  const list = $("#inbox-list");
  if (!visibleItems.length) {
    list.innerHTML = '<div class="inbox-empty">조건에 맞는 문의가 없습니다.</div>';
    return;
  }
  list.innerHTML = visibleItems.map((item) => `
    <button class="inbox-item ${item.id === selectedId ? "selected" : ""}" data-voc-id="${item.id}" type="button">
      <div class="inbox-item-top">
        <span class="status-chip ${statusClass(item.processing_status)}">${escapeHtml(item.processing_status)}</span>
        ${item.is_recent ? '<span class="new-chip">방금 접수</span>' : ""}
        <time>${escapeHtml(formatUtc(item.received_at_utc))}</time>
      </div>
      <strong>${escapeHtml(item.content_masked)}</strong>
      <small>${escapeHtml(item.game_name || "게임 미지정")} · ${escapeHtml(item.platform || "플랫폼 미지정")} · ${escapeHtml(item.receipt_number)}</small>
    </button>`).join("");

  list.querySelectorAll("[data-voc-id]").forEach((button) => {
    button.addEventListener("click", () => selectItem(Number(button.dataset.vocId)));
  });
}

function valueOrDash(value, suffix = "") {
  return value === null || value === undefined ? "—" : `${value}${suffix}`;
}

function selectItem(vocId) {
  const item = items.find((candidate) => candidate.id === vocId);
  if (!item) return;
  selectedId = vocId;
  renderList();
  const grade = item.priority_grade || "—";
  const reasons = item.reasons.length
    ? item.reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")
    : "<li>아직 우선순위 산정 전입니다.</li>";
  $("#inbox-detail").innerHTML = `
    <div class="detail-heading">
      <div><span>${escapeHtml(item.receipt_number)}</span><h2>${escapeHtml(item.category || "분석 대기")} ${item.topic ? `&gt; ${escapeHtml(item.topic)}` : ""}</h2></div>
      <span class="grade grade-${escapeHtml(grade.toLowerCase())}">${escapeHtml(grade)}</span>
    </div>
    <section class="customer-message">
      <span>고객 작성 내용</span>
      <p>${escapeHtml(item.content_masked)}</p>
      <small>개인정보가 포함된 경우 해당 부분만 자동으로 가려집니다.</small>
    </section>
    <dl class="detail-grid">
      <div><dt>접수 시각</dt><dd>${escapeHtml(formatUtc(item.received_at_utc))}</dd></div>
      <div><dt>유입 채널</dt><dd>${escapeHtml(item.channel)}</dd></div>
      <div><dt>게임</dt><dd>${escapeHtml(item.game_name || "—")}</dd></div>
      <div><dt>플랫폼</dt><dd>${escapeHtml(item.platform || "—")}</dd></div>
      <div><dt>연결된 문제 그룹</dt><dd>${escapeHtml(item.issue_group_title || "—")}</dd></div>
      <div><dt>그룹 문의량</dt><dd>${valueOrDash(item.inquiry_count, "건")}</dd></div>
      <div><dt>심각도</dt><dd>${escapeHtml(item.severity_level || "—")} ${item.severity_score !== null ? `${item.severity_score.toFixed(2)}/5` : ""}</dd></div>
      <div><dt>현재 해결 순위</dt><dd>${item.priority_rank !== null ? `${number.format(item.priority_rank)}위 · ${item.priority_score.toFixed(2)}점` : "—"}</dd></div>
      <div><dt>자동 분류 신뢰도</dt><dd>${item.confidence !== null ? `${Math.round(item.confidence * 100)}%` : "—"}</dd></div>
      <div><dt>처리 상태</dt><dd><span class="status-chip ${statusClass(item.processing_status)}">${escapeHtml(item.processing_status)}</span></dd></div>
    </dl>
    <section class="reason-box"><span>우선순위 산정 근거</span><ul>${reasons}</ul></section>`;
}

async function loadInbox() {
  const response = await fetch("/api/v1/admin/vocs?offset=0&limit=100", { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`문의함을 불러오지 못했습니다. (${response.status})`);
  const result = await response.json();
  items = result.items || [];
  $("#inbox-total").textContent = `${number.format(result.total)}건`;
  const badge = $("#sidebar-inbox-badge");
  badge.textContent = number.format(result.recent_count);
  badge.hidden = result.recent_count === 0;
  $("#inbox-updated").textContent = `${new Date().toLocaleTimeString("ko-KR", { hour: "numeric", minute: "2-digit", second: "2-digit" })} 갱신`;
  if (selectedId === null && items.length) selectedId = items[0].id;
  if (selectedId !== null && !items.some((item) => item.id === selectedId)) selectedId = items[0]?.id ?? null;
  renderList();
  if (selectedId !== null) selectItem(selectedId);
}

$("#inbox-search").addEventListener("input", renderList);
loadInbox().catch((error) => { $("#inbox-list").innerHTML = `<div class="inbox-empty error">${escapeHtml(error.message)}</div>`; });
window.setInterval(() => loadInbox().catch(() => {}), 5000);

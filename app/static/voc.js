"use strict";

const form = document.querySelector("#voc-form");
const submitButton = document.querySelector("#submit-button");
const errorMessage = document.querySelector("#form-error");

async function submitInquiry(payload) {
  const response = await fetch("/api/v1/vocs/intake", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    let message = "문의를 접수하지 못했습니다. 잠시 후 다시 시도해 주세요.";
    try { message = (await response.json()).detail || message; } catch (_) { /* 본문 없음 */ }
    throw new Error(message);
  }
  return response.json();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorMessage.hidden = true;
  const content = document.querySelector("#content").value.trim();
  if (content.length < 2) {
    errorMessage.textContent = "문의 내용을 두 글자 이상 적어주세요.";
    errorMessage.hidden = false;
    return;
  }

  submitButton.disabled = true;
  submitButton.textContent = "문의 접수 중...";
  try {
    const result = await submitInquiry({
      game_name: document.querySelector("#game-name").value,
      platform: document.querySelector("#platform").value,
      content,
    });
    document.querySelector("#receipt-number").textContent = result.receipt_number;
    document.querySelector("#form-view").hidden = true;
    document.querySelector("#success-view").hidden = false;
  } catch (error) {
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "문의 전송";
  }
});

document.querySelector("#new-inquiry").addEventListener("click", () => {
  form.reset();
  document.querySelector("#success-view").hidden = true;
  document.querySelector("#form-view").hidden = false;
  document.querySelector("#content").focus();
});

(() => {
  "use strict";

  // ---------- Labels ----------
  const CATEGORY = {
    restaurant: "음식점", cafe: "카페", tourism: "관광", culture: "문화",
    activity: "활동", public_facility: "공공시설", education: "교육", other: "기타",
  };
  const COMPANION = { alone: "혼자", friend: "친구", family: "가족" };
  const INTENT = {
    recommend_place: "장소 추천", search_place: "장소 검색", get_event: "행사 찾기",
    get_route: "길찾기", unsupported: "장소와 무관한 요청",
  };
  const SOURCE = {
    mock: "샘플", mock_cross: "샘플 교차", kakao: "카카오", naver: "네이버",
    busan: "부산 데이터", tour: "관광공사", weather: "날씨",
  };
  const PROVIDER_STATUS = { ok: "정상", not_configured: "키 미설정", timeout: "시간 초과", error: "오류" };
  const SCORE = [
    ["relevance", "검색어 일치", 30], ["distance", "거리", 25], ["user_condition", "사용자 조건", 15],
    ["weather", "날씨", 10], ["cross_provider", "출처 교차 확인", 10], ["busan_data", "부산 데이터", 10],
  ];
  const TIMING = {
    intent_llm_ms: "LLM 해석", search_ms: "장소 검색", merge_ms: "중복 통합",
    ranking_ms: "점수 계산", pipeline_ms: "추천 처리", total_ms: "전체",
  };
  const EXAMPLES = [
    ["서면에서 친구랑 카페 추천해줘", "기본 추천 흐름"],
    ["북구청 근처 도서관과 중국집을 가고 싶어", "한 문장에 장소 두 곳"],
    ["비 오는데 해운대에서 가족이랑 실내에서 놀 곳 있어?", "실내 조건과 동행"],
  ];

  // ---------- Storage (브라우저에만 저장, 로그인 없음) ----------
  const STORE_KEY = "busanmate.conversations.v1";
  const DEV_KEY = "busanmate.devmode";

  const store = {
    load() {
      try { return JSON.parse(localStorage.getItem(STORE_KEY)) || []; } catch { return []; }
    },
    save(list) {
      try {
        const clean = list.map((c) => ({ ...c, messages: c.messages.filter((m) => !m.pending) }));
        localStorage.setItem(STORE_KEY, JSON.stringify(clean.slice(0, 50)));
      } catch { /* 저장 공간이 없어도 화면은 계속 동작 */ }
    },
    getDev() { try { return localStorage.getItem(DEV_KEY) === "1"; } catch { return false; } },
    setDev(on) { try { localStorage.setItem(DEV_KEY, on ? "1" : "0"); } catch { /* ignore */ } },
  };

  // ---------- State ----------
  let conversations = store.load();
  let currentId = null;
  let pending = false;

  const $ = (id) => document.getElementById(id);
  const els = {
    app: $("app"), messages: $("messages"), input: $("input"), send: $("sendBtn"),
    composer: $("composer"), history: $("historyList"), title: $("chatTitle"),
    newChat: $("newChatBtn"), dev: $("devToggle"), menu: $("menuBtn"), scrim: $("scrim"),
    llmDot: $("llmDot"), llmText: $("llmText"), mockRow: $("mockRow"), providers: $("providerList"),
  };

  const uid = () => Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
  const current = () => conversations.find((c) => c.id === currentId) || null;

  function h(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (value == null || value === false) continue;
      if (key === "class") node.className = value;
      else if (key === "text") node.textContent = value;
      else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
      else node.setAttribute(key, value === true ? "" : value);
    }
    for (const child of [].concat(children)) {
      if (child == null || child === false) continue;
      node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return node;
  }

  const formatMs = (ms) => (ms >= 1000 ? `${(ms / 1000).toFixed(2)}초` : ms < 10 ? `${ms.toFixed(1)}ms` : `${Math.round(ms)}ms`);
  const formatDistance = (m) => (m >= 1000 ? `${(m / 1000).toFixed(1)}km` : `${Math.round(m)}m`);

  // ---------- Sidebar ----------
  function renderHistory() {
    els.history.replaceChildren();
    if (!conversations.length) {
      els.history.append(h("li", { class: "history-empty", text: "아직 대화가 없습니다." }));
      return;
    }
    for (const conv of conversations) {
      const item = h("li", { class: `history-item${conv.id === currentId ? " active" : ""}` }, [
        h("button", {
          class: "history-link", type: "button", text: conv.title,
          onclick: () => { openConversation(conv.id); closeNav(); },
        }),
        h("button", {
          class: "history-delete", type: "button", "aria-label": `${conv.title} 삭제`,
          onclick: () => deleteConversation(conv.id),
        }, svgIcon("M5 5l10 10M15 5L5 15")),
      ]);
      els.history.append(item);
    }
  }

  function svgIcon(d) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 20 20");
    svg.setAttribute("aria-hidden", "true");
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", d);
    svg.append(path);
    return svg;
  }

  async function refreshStatus() {
    try {
      const res = await fetch("/api/v1/status");
      const data = await res.json();
      const { llm } = data;
      if (!llm.reachable) {
        setLlm("dot-bad", "Ollama 연결 안 됨");
      } else if (!llm.model_installed) {
        setLlm("dot-warn", `${llm.model} 모델 없음`);
      } else {
        setLlm("dot-ok", `${llm.model} 연결됨`);
      }
      els.mockRow.hidden = !data.mock_data;
      els.providers.replaceChildren(
        ...Object.entries(data.providers).map(([name, on]) =>
          h("li", {}, [h("span", { class: `dot ${on ? "dot-ok" : ""}` }), SOURCE[name] || name])
        )
      );
    } catch {
      setLlm("dot-bad", "백엔드 서버 응답 없음");
    }
  }

  function setLlm(dotClass, text) {
    els.llmDot.className = `dot ${dotClass}`;
    els.llmText.textContent = text;
  }

  // ---------- Conversations ----------
  function newConversation() {
    currentId = null;
    renderAll();
    els.input.focus();
  }

  function openConversation(id) {
    currentId = id;
    renderAll();
  }

  function deleteConversation(id) {
    conversations = conversations.filter((c) => c.id !== id);
    if (currentId === id) currentId = null;
    store.save(conversations);
    renderAll();
  }

  function renderAll() {
    const conv = current();
    els.title.textContent = conv ? conv.title : "새 대화";
    renderHistory();
    renderMessages();
  }

  // ---------- Messages ----------
  function renderMessages() {
    const conv = current();
    els.messages.replaceChildren();

    if (!conv || !conv.messages.length) {
      els.messages.append(renderEmpty());
      return;
    }

    const thread = h("div", { class: "thread" });
    for (const msg of conv.messages) thread.append(renderMessage(msg));
    els.messages.append(thread);
    els.messages.scrollTop = els.messages.scrollHeight;
  }

  function renderEmpty() {
    return h("div", { class: "empty" }, [
      h("h2", { text: "어디로 갈지 한 문장으로 말해 주세요" }),
      h("p", { text: "지역, 가고 싶은 장소, 함께 가는 사람을 적으면 어떻게 이해했는지와 추천 순위를 보여줍니다." }),
      h("div", { class: "examples" }, EXAMPLES.map(([text, note]) =>
        h("button", { class: "example", type: "button", onclick: () => send(text) }, [
          text, h("small", { text: note }),
        ])
      )),
    ]);
  }

  function renderMessage(msg) {
    if (msg.role === "user") {
      return h("div", { class: "msg-user" }, h("div", { class: "bubble", text: msg.text }));
    }
    if (msg.pending) {
      return h("div", { class: "msg-bot" },
        h("div", { class: "typing" }, [
          h("span", { class: "typing-dots" }, [h("i"), h("i"), h("i")]),
          "요청을 해석하고 장소를 찾는 중",
        ])
      );
    }
    if (msg.error) return renderError(msg);
    return renderResponse(msg.response);
  }

  function renderError(msg) {
    return h("div", { class: "msg-bot" },
      h("div", { class: "error-box", role: "alert" }, [
        h("strong", { text: msg.error.title }),
        h("p", { text: msg.error.message }),
        msg.retryText && h("button", {
          class: "retry-btn", type: "button", text: "다시 보내기",
          onclick: () => retry(msg),
        }),
      ])
    );
  }

  function renderResponse(res) {
    const { intent } = res;
    const wrap = h("div", { class: "msg-bot" });

    // 1) 한 줄 요약 (지원하지 않는 요청은 안내 문구만 보여준다)
    if (intent.intent !== "unsupported") wrap.append(h("p", { class: "bot-text", text: summarize(res) }));

    // 2) 해석 결과
    if (intent.intent !== "unsupported") {
      const chips = [h("span", { class: "understood-label", text: "이렇게 이해했어요" })];
      chips.push(chip("목적", INTENT[intent.intent] || intent.intent));
      if (intent.location) chips.push(chip("위치", intent.location));
      if (intent.companion) chips.push(chip("동행", COMPANION[intent.companion]));
      wrap.append(h("div", { class: "understood" }, chips));
    }

    if (res.notice) wrap.append(h("p", { class: "bot-notice", text: res.notice }));

    // 3) 요청별 추천 결과
    for (const result of res.results) wrap.append(renderRequest(result, res.mock_data));

    // 4) 개발자용 상세
    wrap.append(renderDebug(res));

    if (res.timing_ms && res.timing_ms.total_ms != null) {
      wrap.append(h("div", { class: "bot-foot", text: `응답 ${formatMs(res.timing_ms.total_ms)}` }));
    }
    return wrap;
  }

  function chip(label, value) {
    return h("span", { class: "chip" }, [label, h("b", { text: value })]);
  }

  function summarize(res) {
    const { intent, results } = res;
    if (intent.intent === "unsupported") return "장소 추천 요청이 아닌 것 같아요.";
    const names = intent.requests.map((r) => r.query).join(", ");
    const found = results.reduce((sum, r) => sum + r.places.length, 0);
    const where = intent.location ? `${intent.location} 기준으로 ` : "";
    if (!found) return `${where}찾은 장소가 없어요. (${names})`;
    return `${where}${names} 후보를 점수순으로 정리했어요.`;
  }

  function renderRequest(result, mock) {
    const { request, places, providers } = result;
    const categoryLabel = CATEGORY[request.category];
    const sub = [categoryLabel !== request.query ? categoryLabel : null, request.subcategory, request.indoor === true ? "실내" : request.indoor === false ? "야외" : null]
      .filter(Boolean).join(" / ");

    const block = h("section", { class: "request-block" }, [
      h("div", { class: "request-head" }, [
        h("h3", { text: request.query }),
        sub && h("span", { text: sub }),
        mock && h("span", { class: "chip chip-mock", text: "샘플 데이터" }),
      ]),
    ]);

    if (places.length) {
      block.append(h("ol", { class: "tickets" }, places.map((p, i) => renderTicket(p, i + 1))));
    } else {
      block.append(renderProviders(providers));
    }
    return block;
  }

  function renderTicket(place, rank) {
    const meta = [];
    if (place.category) meta.push(h("span", { class: "chip", text: CATEGORY[place.category] || place.category }));
    if (place.distance_m != null) meta.push(h("span", { class: "chip", text: formatDistance(place.distance_m) }));
    if (place.indoor != null) meta.push(h("span", { class: "chip", text: place.indoor ? "실내" : "야외" }));
    for (const s of place.sources) meta.push(h("span", { class: "chip chip-source", text: SOURCE[s] || s }));

    const breakdown = h("div", { class: "breakdown", id: `bd-${place.id}-${rank}` },
      SCORE.map(([key, label, max]) => {
        const value = place.score_breakdown[key] ?? 0;
        return h("div", { class: "bar-row" }, [
          h("span", { class: "bar-label", text: label }),
          h("span", { class: "bar" }, h("span", { class: "bar-fill", style: `width:${(value / max) * 100}%` })),
          h("span", { class: "bar-value", text: `${value} / ${max}` }),
        ]);
      })
    );

    const card = h("li", { class: "ticket" });
    const toggle = h("button", {
      class: "ticket-toggle", type: "button", text: "점수 구성 보기",
      "aria-expanded": "false", "aria-controls": breakdown.id,
      onclick: () => {
        const open = card.classList.toggle("open");
        toggle.setAttribute("aria-expanded", String(open));
        toggle.textContent = open ? "점수 구성 닫기" : "점수 구성 보기";
      },
    });

    card.append(
      h("div", { class: "ticket-body" }, [
        h("span", { class: "ticket-rank", text: rank }),
        h("div", {}, [
          h("p", { class: "ticket-name", text: place.name }),
          h("div", { class: "ticket-meta" }, meta),
        ]),
        toggle,
      ]),
      h("div", { class: "ticket-stub", "aria-label": `추천 점수 ${place.score}점` }, [
        h("span", { class: "score", text: Number(place.score).toFixed(place.score % 1 ? 1 : 0) }),
        h("span", { class: "score-max", text: "100점 중" }),
      ]),
      breakdown
    );
    return card;
  }

  function renderProviders(providers) {
    return h("div", { class: "providers" }, Object.entries(providers).map(([name, st]) => {
      const dot = st.status === "ok" ? "dot-ok" : st.status === "not_configured" ? "" : "dot-bad";
      return h("span", { class: "provider-chip", title: st.detail || "" }, [
        h("span", { class: `dot ${dot}` }),
        SOURCE[name] || name,
        h("small", { text: st.status === "ok" ? `${st.count}건` : PROVIDER_STATUS[st.status] }),
      ]);
    }));
  }

  function renderDebug(res) {
    const timings = Object.entries(res.timing_ms || {});
    return h("div", { class: "debug" }, [
      h("h4", { text: "처리 시간" }),
      h("dl", { class: "timings" }, timings.map(([k, v]) =>
        h("div", {}, [h("dt", { text: TIMING[k] || k }), h("dd", { text: formatMs(v) })])
      )),
      // 결과가 없는 요청은 본문에 이미 Provider 상태가 보이므로 여기서는 결과가 있는 요청만 보여준다.
      ...res.results.filter((r) => r.places.length).flatMap((r) => [
        h("h4", { text: `"${r.request.query}" Provider 상태` }),
        renderProviders(r.providers),
      ]),
      h("details", {}, [
        h("summary", { text: "Intent JSON" }),
        h("pre", { text: JSON.stringify(res.intent, null, 2) }),
      ]),
      h("details", {}, [
        h("summary", { text: "전체 응답 JSON" }),
        h("pre", { text: JSON.stringify(res, null, 2) }),
      ]),
    ]);
  }

  // ---------- Send ----------
  async function send(text) {
    const message = text.trim();
    if (!message || pending) return;

    let conv = current();
    if (!conv) {
      conv = { id: uid(), title: message.slice(0, 40), createdAt: Date.now(), messages: [] };
      conversations.unshift(conv);
      currentId = conv.id;
    } else {
      // 최근 사용한 대화를 목록 맨 위로 올린다.
      conversations = [conv, ...conversations.filter((c) => c.id !== conv.id)];
    }

    conv.messages.push({ id: uid(), role: "user", text: message });
    const botMsg = { id: uid(), role: "assistant", pending: true };
    conv.messages.push(botMsg);

    els.input.value = "";
    autosize();
    setPending(true);
    renderAll();

    try {
      const res = await fetch("/api/v1/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, limit: 5 }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) throw toError(res.status, data);
      botMsg.response = data;
    } catch (err) {
      botMsg.error = err.title ? err : { title: "서버에 연결할 수 없음", message: "FastAPI 서버가 실행 중인지 확인하세요." };
      botMsg.retryText = message;
    } finally {
      delete botMsg.pending;
      setPending(false);
      store.save(conversations);
      renderAll();
      refreshStatus();
    }
  }

  function toError(status, data) {
    const detail = data && data.detail;
    if (detail && detail.code === "llm_unavailable") return { title: "LLM에 연결할 수 없음", message: detail.message };
    if (detail && detail.code === "intent_parse_failed") return { title: "요청을 해석하지 못함", message: detail.message };
    if (status === 422) return { title: "입력 형식 오류", message: "메시지는 1~500자로 입력하세요." };
    return { title: `서버 오류 ${status}`, message: typeof detail === "string" ? detail : "백엔드 로그를 확인하세요." };
  }

  function retry(msg) {
    const conv = current();
    if (!conv) return;
    const index = conv.messages.indexOf(msg);
    // 실패한 응답과 그 질문을 지우고 같은 문장을 다시 보낸다.
    if (index > 0) conv.messages.splice(index - 1, 2);
    send(msg.retryText);
  }

  function setPending(on) {
    pending = on;
    els.send.disabled = on || !els.input.value.trim();
  }

  function autosize() {
    els.input.style.height = "auto";
    els.input.style.height = `${Math.min(els.input.scrollHeight, 200)}px`;
  }

  // ---------- Mobile nav ----------
  function openNav() { els.app.classList.add("nav-open"); els.scrim.hidden = false; }
  function closeNav() { els.app.classList.remove("nav-open"); els.scrim.hidden = true; }

  // ---------- Events ----------
  els.composer.addEventListener("submit", (e) => { e.preventDefault(); send(els.input.value); });
  els.input.addEventListener("input", () => { autosize(); els.send.disabled = pending || !els.input.value.trim(); });
  els.input.addEventListener("keydown", (e) => {
    // 한글 조합 중 Enter는 글자 확정이므로 전송하지 않는다.
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing && e.keyCode !== 229) {
      e.preventDefault();
      send(els.input.value);
    }
  });
  els.newChat.addEventListener("click", () => { newConversation(); closeNav(); });
  els.menu.addEventListener("click", openNav);
  els.scrim.addEventListener("click", closeNav);
  els.dev.addEventListener("change", () => {
    els.app.classList.toggle("dev-on", els.dev.checked);
    store.setDev(els.dev.checked);
  });

  // ---------- Init ----------
  els.dev.checked = store.getDev();
  els.app.classList.toggle("dev-on", els.dev.checked);
  if (conversations.length) currentId = conversations[0].id;
  renderAll();
  refreshStatus();
  setInterval(refreshStatus, 30000);
})();

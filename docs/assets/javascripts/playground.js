/*
|--------------------------------------------------------------------------
| Playground
|--------------------------------------------------------------------------
|
| Mengubah setiap <div class="zul-playground"> menjadi panel untuk mencoba
| agent dari proyek hasil "zul build hexa". Panel ini berbicara dengan
| endpoint /playground/* di API lokalmu, lalu menampilkan jawaban
| agent, jejak langkahnya, dan aksi yang menunggu keputusan.
|
| Saat API tidak terjangkau, misalnya di dokumentasi yang sudah diterbitkan,
| panel berjalan dalam mode simulasi: ia menampilkan contoh jejak supaya
| pembaca tetap bisa melihat cara kerja agent sebelum punya proyek.
|
| Pemakaian di halaman Markdown:
|
|   <div class="zul-playground" data-feature="ReAct"></div>
|
|   data-feature    nama fitur; tanpa atribut ini panel menampilkan pilihan
|   data-examples   contoh pesan, dipisah "|"; bawaannya dari features.py
|   data-layout     "wide" menaruh jejak langkah di samping percakapan
|   data-simulate   selalu memakai simulasi, tanpa mencoba menghubungi API
|   data-autoplay   pesan yang dikirim sendiri saat panel pertama tampil
|
*/

(function () {
  "use strict";

  /*
  |--------------------------------------------------------------------------
  | Alamat API
  |--------------------------------------------------------------------------
  |
  | Alamat API disimpan di browser, jadi sekali diubah ia berlaku untuk
  | semua panel di semua halaman. Bawaannya adalah alamat uvicorn saat
  | aplikasi dijalankan di komputermu sendiri.
  |
  */

  const DEFAULT_API = "http://localhost:8000";
  const API_STORAGE_KEY = "zul.playground.api";

  function apiBase() {
    let saved = null;

    try {
      saved = window.localStorage.getItem(API_STORAGE_KEY);
    } catch (error) {
      saved = null;
    }

    return (saved || DEFAULT_API).replace(/\/+$/, "");
  }

  function saveApiBase(value) {
    try {
      window.localStorage.setItem(API_STORAGE_KEY, value.trim());
    } catch (error) {
      /* Penyimpanan browser tidak tersedia; alamat bawaan tetap dipakai. */
    }
  }

  class ApiError extends Error {
    constructor(status, detail) {
      super(detail);
      this.status = status;
    }
  }

  async function callApi(path, body, timeout) {
    const options = body
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      : { method: "GET" };

    if (timeout) {
      const controller = new AbortController();

      window.setTimeout(() => controller.abort(), timeout);
      options.signal = controller.signal;
    }

    const response = await fetch(apiBase() + path, options);
    const payload = await response.json().catch(() => null);

    if (!response.ok) {
      throw new ApiError(response.status, describeFailure(response.status, payload));
    }

    return payload;
  }

  /*
   * Sambungan pertama ke "localhost" kadang ditolak, misalnya saat browser
   * mencoba alamat IPv6 lebih dulu padahal server hanya mendengarkan di
   * IPv4. Daftar fitur hanya dibaca, jadi aman dicoba sekali lagi. Setiap
   * percobaan dibatasi waktunya, supaya alamat yang tidak pernah menjawab
   * tidak membuat panel menunggu tanpa akhir.
   */
  const FEATURES_TIMEOUT = 2500;

  async function loadFeatures() {
    try {
      return await callApi("/playground/features", null, FEATURES_TIMEOUT);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }

      await wait(400);

      return callApi("/playground/features", null, FEATURES_TIMEOUT);
    }
  }

  function describeFailure(status, payload) {
    const detail = payload && payload.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
    }

    return "API menjawab dengan status " + status + ".";
  }

  /*
  |--------------------------------------------------------------------------
  | Simulasi
  |--------------------------------------------------------------------------
  |
  | Simulasi mengembalikan giliran dengan bentuk yang sama seperti API,
  | jadi kode tampilan tidak perlu tahu sumbernya. Isinya adalah contoh
  | untuk fitur bawaan template; pesan di luar contoh dijawab seadanya.
  |
  */

  const SIMULATED_FEATURES = [
    {
      name: "ReAct",
      description: "Agent dasar dengan tool cuaca. Sama dengan POST /chat.",
      examples: ["What is the weather in sf?"],
    },
    {
      name: "Human-in-the-loop",
      description:
        "Agent yang meminta persetujuanmu sebelum mengirim email. Sama dengan POST /hitl/chat.",
      examples: ["Kirim email ke alice@example.com: rapat besok jam 10"],
    },
    {
      name: "Subagents",
      description:
        "Supervisor yang membagi tugas ke subagent cuaca dan email. Sama dengan POST /subagents/chat.",
      examples: ["Cek cuaca di sf, lalu email hasilnya ke alice@example.com"],
    },
  ];

  const WEATHER_RESULT =
    "It's sunny in San Francisco, but you better look out if you're a Gemini 😈.";
  const ORDERS = { "ORD-1042": "shipped", "ORD-1043": "processing" };
  const OUTSIDE_RECORDING =
    "Mode simulasi hanya bisa menjawab contoh pesan di panel ini. Sambungkan proyekmu untuk mendapat jawaban dari model sungguhan.";

  const toolCall = (name, args) => ({ type: "tool_call", name: name, args: args });
  const toolResult = (name, content, failed) => ({
    type: "tool_result",
    name: name,
    content: content,
    failed: Boolean(failed),
  });
  const text = (content) => ({ type: "text", content: content });
  const step = (node, depth, events) => ({ node: node, depth: depth, events: events });

  function readIntent(message) {
    const order = message.match(/ORD-\d+/i);
    const address = message.match(/[\w.+-]+@[\w-]+\.[\w.-]+/);

    return {
      weather: /cuaca|weather/i.test(message),
      email: /e-?mail|surel/i.test(message),
      order: order ? order[0].toUpperCase() : null,
      address: address ? address[0] : "alice@example.com",
      indonesian: /cuaca|kirim|cek|apa|bagaimana|tolong/i.test(message),
    };
  }

  function orderStatus(orderId) {
    const status = ORDERS[orderId];

    return status ? "Order " + orderId + " is " + status : "No order found with id " + orderId;
  }

  class Simulator {
    constructor() {
      this.waiting = {};
      this.counter = 0;
    }

    features() {
      return Promise.resolve(SIMULATED_FEATURES);
    }

    async message(feature, message, threadId) {
      const thread = threadId || this.newThread();
      const intent = readIntent(message);

      await wait(650);

      if (feature === "Human-in-the-loop") {
        return this.reviewedTurn(thread, intent);
      }

      const steps = feature === "Subagents" ? supervisorSteps(intent) : reactSteps(intent);

      return this.finished(thread, steps);
    }

    async resume(feature, threadId, value) {
      const action = this.waiting[threadId];

      await wait(650);

      if (!action) {
        throw new ApiError(400, "Tidak ada aksi yang menunggu persetujuan di percakapan ini");
      }

      const decision = (value && value.decisions && value.decisions[0]) || { type: "approve" };
      delete this.waiting[threadId];

      return this.finished(threadId, reviewedSteps(action, decision));
    }

    reviewedTurn(thread, intent) {
      if (!intent.email) {
        const steps = reactSteps(intent);

        if (steps.length > 1) {
          steps.splice(1, 0, step("human_review", 0, []));
        }

        return this.finished(thread, steps);
      }

      const args = {
        to: intent.address,
        subject: "Rapat besok",
        body: "Rapat besok jam 10.",
      };
      this.waiting[thread] = { name: "send_email", args: args };

      return {
        thread_id: thread,
        answer: null,
        pending_review: {
          action_requests: [
            {
              name: "send_email",
              args: args,
              description: "Tool `send_email` menunggu persetujuan",
            },
          ],
          review_configs: [
            { action_name: "send_email", allowed_decisions: ["approve", "edit", "reject"] },
          ],
        },
        error: null,
        seconds: 0.9,
        steps: [step("llm_call", 0, [toolCall("send_email", args)])],
      };
    }

    finished(thread, steps) {
      const last = steps[steps.length - 1];
      const answer = last.events[last.events.length - 1].content;

      return {
        thread_id: thread,
        answer: answer,
        pending_review: null,
        error: null,
        seconds: 0.6 * steps.length,
        steps: steps,
      };
    }

    newThread() {
      this.counter += 1;

      return "simulasi-" + this.counter;
    }
  }

  function reactSteps(intent) {
    if (intent.order) {
      const status = orderStatus(intent.order);

      return [
        step("llm_call", 0, [toolCall("get_order_status", { order_id: intent.order })]),
        step("tool_node", 0, [toolResult("get_order_status", status)]),
        step("llm_call", 0, [text(status + ".")]),
      ];
    }

    if (intent.weather) {
      const answer = intent.indonesian
        ? "Cuaca di San Francisco sedang cerah."
        : "It's sunny in San Francisco right now.";

      return [
        step("llm_call", 0, [toolCall("get_weather", { location: "sf" })]),
        step("tool_node", 0, [toolResult("get_weather", WEATHER_RESULT)]),
        step("llm_call", 0, [text(answer)]),
      ];
    }

    return [step("llm_call", 0, [text(OUTSIDE_RECORDING)])];
  }

  function reviewedSteps(action, decision) {
    if (decision.type === "reject") {
      const reason = decision.message || "User rejected this action. It was not executed.";

      return [
        step("human_review", 0, [
          toolCall(action.name, action.args),
          toolResult(action.name, reason, true),
        ]),
        step("llm_call", 0, [
          text("Baik, emailnya tidak saya kirim. Bagaimana kamu ingin melanjutkannya?"),
        ]),
      ];
    }

    const args = decision.type === "edit" ? decision.edited_action.args : action.args;
    const sent = "Email sent to " + args.to + " with subject '" + args.subject + "'";

    return [
      step("human_review", 0, [toolCall(action.name, args)]),
      step("tool_node", 0, [toolResult(action.name, sent)]),
      step("llm_call", 0, [text("Email ke " + args.to + " sudah terkirim.")]),
    ];
  }

  function supervisorSteps(intent) {
    const steps = [];
    const results = [];

    const delegate = (agent, query, toolName, args, toolOutput, summary) => {
      steps.push(step("llm_call", 0, [toolCall(agent, { query: query })]));
      steps.push(step("llm_call", 1, [toolCall(toolName, args)]));
      steps.push(step("tool_node", 1, [toolResult(toolName, toolOutput)]));
      steps.push(step("llm_call", 1, [text(summary)]));
      steps.push(step("tool_node", 0, [toolResult(agent, summary)]));
      results.push(summary);
    };

    if (intent.order) {
      const status = orderStatus(intent.order);
      delegate(
        "order_agent",
        "Look up the status of order " + intent.order,
        "get_order_status",
        { order_id: intent.order },
        status,
        status + "."
      );
    }

    if (intent.weather) {
      delegate(
        "weather_agent",
        "What is the current weather in San Francisco?",
        "get_weather",
        { location: "sf" },
        WEATHER_RESULT,
        "It is sunny in San Francisco."
      );
    }

    if (intent.email) {
      const args = {
        to: intent.address,
        subject: "Cuaca San Francisco",
        body: "Cuaca di San Francisco sedang cerah.",
      };
      delegate(
        "email_agent",
        "Send an email to " + intent.address + " saying it is sunny in San Francisco.",
        "send_email",
        args,
        "Email sent to " + args.to + " with subject '" + args.subject + "'",
        "The email was sent to " + args.to + "."
      );
    }

    if (!results.length) {
      return [step("llm_call", 0, [text(OUTSIDE_RECORDING)])];
    }

    steps.push(step("llm_call", 0, [text(results.join(" "))]));

    return steps;
  }

  /*
  |--------------------------------------------------------------------------
  | Pembantu
  |--------------------------------------------------------------------------
  |
  | Semua teks dari API dimasukkan lewat textContent, tidak pernah lewat
  | innerHTML. Hasil tool bisa berisi apa saja, termasuk potongan HTML,
  | dan teks seperti itu tidak boleh sampai dijalankan browser.
  |
  */

  function el(tag, className, content) {
    const node = document.createElement(tag);

    if (className) {
      node.className = className;
    }

    if (content !== undefined && content !== null) {
      node.textContent = content;
    }

    return node;
  }

  function button(className, label, onClick) {
    const node = el("button", className, label);

    node.type = "button";
    node.addEventListener("click", onClick);

    return node;
  }

  function pretty(value) {
    return typeof value === "string" ? value : JSON.stringify(value, null, 2);
  }

  function wait(milliseconds) {
    return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
  }

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  let nextId = 0;

  function uniqueId(prefix) {
    nextId += 1;

    return prefix + "-" + nextId;
  }

  /* Jenis langkah menentukan warna titiknya di rel jejak. */
  function kindOf(traceStep) {
    if (/human|review/.test(traceStep.node)) {
      return "human";
    }

    if (traceStep.events.some((event) => event.type === "tool_result")) {
      return "tool";
    }

    return traceStep.events.length ? "model" : "pass";
  }

  /*
  |--------------------------------------------------------------------------
  | Panel
  |--------------------------------------------------------------------------
  */

  class Playground {
    constructor(root) {
      this.root = root;
      this.fixedFeature = root.dataset.feature || null;
      this.wide = root.dataset.layout === "wide";
      this.simulationOnly = root.hasAttribute("data-simulate");
      this.autoplay = root.dataset.autoplay || "";
      this.customExamples = (root.dataset.examples || "")
        .split("|")
        .map((example) => example.trim())
        .filter(Boolean);

      this.simulator = new Simulator();
      this.live = false;
      this.features = [];
      this.feature = this.fixedFeature;
      this.threadId = null;
      this.pending = null;
      this.busy = false;
      this.started = false;

      this.build();
      this.connect().then(() => this.playOnce());
    }

    /* -- Kerangka ------------------------------------------------------- */

    build() {
      this.root.textContent = "";
      this.panel = el("div", "zpg");
      this.panel.dataset.layout = this.wide ? "wide" : "compact";

      const bar = el("div", "zpg__bar");
      bar.append(el("span", "zpg__title", "Playground"));

      if (this.fixedFeature) {
        bar.append(el("span", "zpg__feature", this.fixedFeature));
      } else {
        this.select = el("select", "zpg__feature");
        this.select.setAttribute("aria-label", "Fitur yang dicoba");
        this.select.addEventListener("change", () => this.chooseFeature(this.select.value));
        bar.append(this.select);
      }

      this.status = button("zpg__status", "Memeriksa", () => this.toggleConnection());
      this.status.dataset.state = "checking";

      bar.append(
        el("span", "zpg__spacer"),
        this.status,
        button("zpg__link", "Percakapan baru", () => this.reset())
      );

      this.connection = this.buildConnection();
      this.description = el("p", "zpg__description");
      this.log = el("div", "zpg__log");
      this.log.setAttribute("aria-live", "polite");
      this.examples = el("div", "zpg__examples");
      this.form = this.buildForm();

      const chat = el("div", "zpg__chat");
      chat.append(this.description, this.log, this.examples, this.form);

      const body = el("div", "zpg__body");
      body.append(chat);

      if (this.wide) {
        this.inspector = el("div", "zpg__inspector");
        body.append(this.inspector);
        this.showInspectorHint();
      }

      this.panel.append(bar, this.connection, body);
      this.root.append(this.panel);
      this.showEmpty();
    }

    buildConnection() {
      const box = el("div", "zpg__connection");
      const form = el("form", "zpg__address");
      const id = uniqueId("zpg-api");
      const label = el("label", null, "Alamat API proyekmu");
      const input = el("input");
      const save = el("button", "zpg__button", "Sambungkan");
      const steps = el("ol");
      const first = el("li");
      const second = el("li");
      const third = el("li");

      this.connectionNote = el("p", "zpg__connection-note");

      label.htmlFor = id;
      input.id = id;
      input.type = "url";
      input.value = apiBase();
      input.placeholder = DEFAULT_API;
      save.type = "submit";
      form.append(label, input, save);

      first.append("Di file ", el("code", null, ".env"), " proyekmu, isi ");
      first.append(el("code", null, "PLAYGROUND_ENABLED=true"), ".");
      second.append("Jalankan aplikasinya: ");
      second.append(el("code", null, "uvicorn src.interface.http.main:app --reload"));
      third.append("Pastikan alamat halaman ini, ", el("code", null, window.location.origin));
      third.append(", ada di ", el("code", null, "PLAYGROUND_ORIGINS"), ".");
      steps.append(first, second, third);

      box.hidden = true;
      box.append(this.connectionNote, steps, form);

      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        saveApiBase(input.value || DEFAULT_API);
        save.disabled = true;
        await this.connect(true);
        save.disabled = false;
      });

      return box;
    }

    buildForm() {
      const form = el("form", "zpg__form");

      this.input = el("input");
      this.input.type = "text";
      this.input.placeholder = "Tulis pesan untuk agent";
      this.input.setAttribute("aria-label", "Pesan untuk agent");
      this.input.autocomplete = "off";

      this.sendButton = el("button", "zpg__button", "Kirim");
      this.sendButton.type = "submit";

      form.append(this.input, this.sendButton);
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        this.send(this.input.value, true);
      });

      return form;
    }

    toggleConnection() {
      this.connection.hidden = !this.connection.hidden;
    }

    /* -- Sambungan ke API ----------------------------------------------- */

    /*
     * Panel selalu bisa dipakai. Jika API menjawab, panel memakai agent di
     * proyekmu. Jika tidak, panel menampilkan contoh jawaban, dan tombol
     * status tetap menawarkan cara menyambungkan proyek.
     */
    async connect(askedByUser) {
      this.setStatus("checking");
      this.live = false;

      /*
       * Contoh jawaban dipasang lebih dulu, supaya panel sudah berisi
       * dan bisa dipakai selama alamat API masih diperiksa. Percakapan
       * yang dimulai selama pemeriksaan tetap memakai contoh itu.
       */
      if (!this.features.length) {
        this.features = SIMULATED_FEATURES;
        this.fillFeatures();
      }

      let found = null;

      if (!this.simulationOnly) {
        try {
          found = await loadFeatures();
        } catch (error) {
          found = null;
        }
      }

      if (found && this.started && !askedByUser) {
        found = null;
      }

      this.live = found !== null;
      this.features = found || SIMULATED_FEATURES;
      this.setStatus(this.live ? "live" : "simulated");
      this.connectionNote.textContent = this.live
        ? "Terhubung ke " + apiBase() + ". Panel ini menjalankan agent di proyekmu."
        : askedByUser
          ? "Belum bisa terhubung ke " + apiBase() + ". Periksa tiga hal berikut, lalu coba lagi."
          : "Panel ini belum terhubung ke proyekmu, jadi yang tampil adalah contoh jawaban. Untuk memakai agent-mu sendiri:";

      if (this.live && askedByUser) {
        this.connection.hidden = true;
      }

      if (this.live || askedByUser) {
        this.fillFeatures();
      }
    }

    setStatus(state) {
      const labels = { checking: "Memeriksa", live: "Terhubung", simulated: "Simulasi" };

      this.status.dataset.state = state;
      this.status.textContent = labels[state];
      this.status.title =
        state === "live" ? "Terhubung ke " + apiBase() : "Klik untuk menyambungkan proyekmu";
      this.panel.dataset.mode = state;
    }

    fillFeatures() {
      if (this.select) {
        this.select.textContent = "";
        this.features.forEach((feature) => {
          const option = el("option", null, feature.name);
          option.value = feature.name;
          this.select.append(option);
        });
      }

      const known = this.features.some((feature) => feature.name === this.feature);
      const first = this.features.length ? this.features[0].name : "";

      this.chooseFeature(known ? this.feature : this.fixedFeature || first);
    }

    /* -- Fitur dan percakapan ------------------------------------------- */

    chooseFeature(name) {
      const info = this.features.find((feature) => feature.name === name);

      this.feature = name;
      if (this.select) {
        this.select.value = name;
      }

      this.description.textContent = info ? info.description.replace(/`/g, "") : "";
      this.currentExamples = this.customExamples.length
        ? this.customExamples
        : info
          ? info.examples
          : [];
      this.reset();

      if (!info) {
        this.showProblem(
          this.live
            ? "Fitur '" + name + "' tidak terdaftar di features.py proyekmu."
            : "Fitur '" + name + "' hanya tersedia saat panel tersambung ke proyekmu."
        );
      }
    }

    reset() {
      this.threadId = null;
      this.pending = null;
      this.started = false;
      this.setBusy(false);
      this.showEmpty();
      this.showExamples();

      if (this.wide) {
        this.showInspectorHint();
      }
    }

    showEmpty() {
      this.log.textContent = "";
      this.log.append(el("p", "zpg__empty", "Tulis pesan, atau pilih salah satu contoh."));
    }

    showInspectorHint() {
      this.inspector.textContent = "";
      this.inspector.append(el("p", "zpg__inspector-title", "Jejak langkah"));
      this.inspector.append(
        el("p", "zpg__empty", "Setiap langkah agent muncul di sini setelah kamu mengirim pesan.")
      );
    }

    showExamples() {
      this.examples.textContent = "";

      (this.currentExamples || []).forEach((example) => {
        this.examples.append(button("zpg__chip", example, () => this.send(example, true)));
      });
    }

    showProblem(message) {
      this.append(el("p", "zpg__notice zpg__notice--error", message));
    }

    append(node) {
      const empty = this.log.querySelector(".zpg__empty");

      if (empty) {
        empty.remove();
      }

      this.log.append(node);
      this.log.scrollTop = this.log.scrollHeight;
    }

    setBusy(busy) {
      this.busy = busy;
      this.input.disabled = busy || this.pending !== null;
      this.sendButton.disabled = busy || this.pending !== null;
      this.input.placeholder = this.pending
        ? "Beri keputusan dulu untuk aksi di atas"
        : "Tulis pesan untuk agent";
    }

    /* -- Mengirim pesan dan keputusan ----------------------------------- */

    /*
     * Halaman sampul menjalankan satu contoh sendiri supaya pembaca langsung
     * melihat agent bekerja. Pesannya diketik huruf demi huruf, kecuali
     * jika pembaca meminta gerakan dikurangi.
     */
    async playOnce() {
      if (!this.autoplay || this.threadId || this.busy) {
        return;
      }

      this.examples.textContent = "";

      if (!prefersReducedMotion()) {
        await wait(500);

        for (const character of this.autoplay) {
          this.input.value += character;
          await wait(22);
        }

        await wait(250);
      }

      this.send(this.autoplay, false);
    }

    async send(message, fromUser) {
      const content = (message || "").trim();

      if (!content || this.busy || this.pending !== null) {
        return;
      }

      this.started = true;
      this.input.value = "";
      this.examples.textContent = "";
      this.append(el("p", "zpg__msg zpg__msg--user", content));

      const request = { feature: this.feature, message: content };
      if (this.threadId) {
        request.thread_id = this.threadId;
      }

      await this.run("/playground/messages", request, "Agent bekerja", fromUser);
    }

    /*
     * Form review dikunci selama keputusannya dikirim. Kalau API menolak
     * keputusan itu, agent masih menunggu, jadi form dibuka lagi supaya
     * keputusannya bisa diperbaiki.
     */
    async resume(value, form) {
      const request = { feature: this.feature, thread_id: this.threadId, value: value };
      const controls = Array.from(form.querySelectorAll("input, textarea, button"));

      controls.forEach((control) => {
        control.disabled = true;
      });

      const accepted = await this.run("/playground/resume", request, "Agent melanjutkan", true);

      if (!accepted) {
        controls.forEach((control) => {
          control.disabled = false;
        });
        form.querySelectorAll(".zpg__choices").forEach((choices) => {
          choices.dispatchEvent(new Event("change"));
        });
      }
    }

    request(path, body) {
      if (this.live) {
        return callApi(path, body);
      }

      return path === "/playground/resume"
        ? this.simulator.resume(body.feature, body.thread_id, body.value)
        : this.simulator.message(body.feature, body.message, body.thread_id);
    }

    async run(path, request, busyText, fromUser) {
      const busy = el("p", "zpg__notice zpg__notice--busy", busyText);
      let accepted = false;

      this.setBusy(true);
      this.append(busy);

      try {
        const turn = await this.request(path, request);

        busy.remove();
        accepted = true;
        this.threadId = turn.thread_id;
        this.pending = turn.pending_review;
        this.renderTurn(turn, { path: path, request: request });
      } catch (error) {
        busy.remove();
        this.showProblem(
          error instanceof ApiError
            ? error.message
            : "API di " + apiBase() + " tidak menjawab. Periksa apakah aplikasinya masih berjalan."
        );
      }

      this.setBusy(false);
      if (fromUser && this.pending === null) {
        this.input.focus({ preventScroll: true });
      }

      return accepted;
    }

    /* -- Menampilkan satu giliran --------------------------------------- */

    renderTurn(turn, call) {
      const block = el("div", "zpg__turn");
      const trace = this.renderTrace(turn);
      const raw = this.renderRaw(call, turn);

      if (this.wide) {
        this.showInInspector(trace, raw);
      } else if (turn.steps.length) {
        block.append(trace);
      }

      if (turn.error) {
        const message = turn.error.type + ": " + turn.error.message;
        block.append(el("p", "zpg__notice zpg__notice--error", message));
        block.append(
          el(
            "p",
            "zpg__empty",
            "Agent berhenti karena error. Mulai percakapan baru untuk mencoba lagi."
          )
        );
      } else if (turn.pending_review !== null) {
        block.append(this.renderReview(turn.pending_review));
      } else {
        block.append(
          el("p", "zpg__msg zpg__msg--agent", turn.answer || "Agent selesai tanpa jawaban.")
        );
      }

      if (this.wide) {
        block.append(
          button("zpg__link zpg__link--inline", "Lihat jejak giliran ini", () =>
            this.showInInspector(this.renderTrace(turn, true), this.renderRaw(call, turn))
          )
        );
      } else {
        block.append(raw);
      }

      this.append(block);
    }

    showInInspector(trace, raw) {
      this.inspector.textContent = "";
      this.inspector.append(el("p", "zpg__inspector-title", "Jejak langkah"), trace, raw);
    }

    /*
     * Jejak ditampilkan sebagai rel: satu titik per node yang selesai.
     * Langkah muncul berurutan dengan jeda singkat, supaya urutan kerja
     * agent terbaca. Langkah subagent menjorok sesuai kedalamannya.
     */
    renderTrace(turn, replay) {
      const details = el("details", "zpg__trace");
      const seconds = turn.seconds.toFixed(1).replace(".", ",");
      const summary = el("summary", null, turn.steps.length + " langkah, " + seconds + " detik");
      const list = el("ol", "zpg__steps");
      const animate = !replay && !prefersReducedMotion();

      details.open = true;

      turn.steps.forEach((traceStep, index) => {
        const item = this.renderStep(traceStep);

        if (animate) {
          item.classList.add("zpg__step--arriving");
          item.style.animationDelay = index * 110 + "ms";
        }

        list.append(item);
      });

      details.append(summary, list);

      return details;
    }

    renderStep(traceStep) {
      const item = el("li", "zpg__step");

      item.dataset.kind = kindOf(traceStep);
      item.style.setProperty("--depth", traceStep.depth);

      if (!traceStep.events.length) {
        const head = el("p", "zpg__step-head");
        head.append(el("span", "zpg__node", traceStep.node), " meneruskan tanpa perubahan");
        item.append(head);
      }

      traceStep.events.forEach((event) => {
        const head = el("p", "zpg__step-head");
        head.append(el("span", "zpg__node", traceStep.node), " ");

        if (event.type === "tool_call") {
          head.append("meminta tool ", el("span", "zpg__tool", event.name));
          item.append(head, el("pre", null, pretty(event.args)));
        } else if (event.type === "tool_result") {
          const label = event.failed ? "tool gagal atau ditolak: " : "hasil tool ";
          head.append(el("span", event.failed ? "zpg__failed" : null, label));
          head.append(el("span", "zpg__tool", event.name || ""));
          item.append(head, el("pre", null, event.content));
        } else {
          head.append("menjawab");
          item.append(head, el("pre", null, event.content));
        }
      });

      return item;
    }

    renderRaw(call, turn) {
      const details = el("details", "zpg__raw");
      const body = el("div", "zpg__raw-body");
      const source = this.live ? "POST " + apiBase() + call.path : "Contoh respons untuk POST " + call.path;

      body.append(el("p", "zpg__step-head", source));
      body.append(el("pre", null, pretty(call.request)));
      body.append(el("p", "zpg__step-head", "Respons"));
      body.append(el("pre", null, pretty(turn)));
      details.append(el("summary", null, "Lihat request dan respons"), body);

      return details;
    }

    /* -- Form review ---------------------------------------------------- */

    renderReview(pending) {
      const isActionReview = pending && Array.isArray(pending.action_requests);

      return isActionReview ? this.renderActionReview(pending) : this.renderFreeResume(pending);
    }

    renderActionReview(pending) {
      const form = el("form", "zpg__review");
      const error = el("p", "zpg__field-error");
      const submit = el("button", "zpg__button", "Kirim keputusan");
      const title = el("p", "zpg__review-title", "Agent berhenti dan menunggu keputusanmu");

      form.append(title);

      const readers = pending.action_requests.map((action, index) => {
        const reader = this.renderAction(action, index);
        form.append(reader.fieldset);

        return reader.read;
      });

      error.hidden = true;
      submit.type = "submit";
      form.append(error, submit);

      form.addEventListener("submit", (event) => {
        event.preventDefault();

        let decisions;
        try {
          decisions = readers.map((read) => read());
        } catch (problem) {
          error.textContent = problem.message;
          error.hidden = false;
          return;
        }

        error.hidden = true;
        this.resume({ decisions: decisions }, form);
      });

      return form;
    }

    renderAction(action, index) {
      const group = uniqueId("zpg-decision");
      const fieldset = el("fieldset");
      const choices = el("div", "zpg__choices");
      const labels = { approve: "Setujui", edit: "Ubah", reject: "Tolak" };

      fieldset.append(el("legend", null, "Aksi " + (index + 1) + ": " + action.name));

      Object.keys(labels).forEach((value) => {
        const label = el("label");
        const radio = el("input");

        radio.type = "radio";
        radio.name = group;
        radio.value = value;
        radio.checked = value === "approve";
        label.append(radio, el("span", null, labels[value]));
        choices.append(label);
      });

      const args = el("textarea");
      args.value = pretty(action.args);
      args.spellcheck = false;

      const reason = el("input");
      reason.type = "text";

      const argsField = el("label", "zpg__field");
      argsField.append(el("span", null, "Argumen"), args);

      const reasonField = el("label", "zpg__field");
      reasonField.append(el("span", null, "Alasan penolakan"), reason);

      const chosen = () => fieldset.querySelector("input[type=radio]:checked").value;
      const sync = () => {
        args.readOnly = chosen() !== "edit";
        reasonField.hidden = chosen() !== "reject";
        fieldset.dataset.choice = chosen();
      };

      choices.addEventListener("change", sync);
      fieldset.append(choices, argsField, reasonField);
      sync();

      return {
        fieldset: fieldset,
        read: () => buildDecision(chosen(), action, args.value, reason.value),
      };
    }

    renderFreeResume(pending) {
      const form = el("form", "zpg__review");
      const value = el("textarea");
      const error = el("p", "zpg__field-error");
      const submit = el("button", "zpg__button", "Lanjutkan");
      const field = el("label", "zpg__field");

      value.value = "true";
      error.hidden = true;
      submit.type = "submit";
      field.append(el("span", null, "Nilai untuk melanjutkan (JSON)"), value);
      form.append(
        el("p", "zpg__review-title", "Agent berhenti dan menunggu nilai darimu"),
        el("pre", null, pretty(pending)),
        field,
        error,
        submit
      );

      form.addEventListener("submit", (event) => {
        event.preventDefault();

        let parsed;
        try {
          parsed = JSON.parse(value.value);
        } catch (problem) {
          error.textContent = "Nilai belum berupa JSON yang valid.";
          error.hidden = false;
          return;
        }

        error.hidden = true;
        this.resume(parsed, form);
      });

      return form;
    }
  }

  /*
  |--------------------------------------------------------------------------
  | Menyusun Keputusan
  |--------------------------------------------------------------------------
  |
  | Bentuk keputusan mengikuti format review human-in-the-loop: satu objek
  | per aksi, dengan urutan yang sama seperti aksi yang ditampilkan.
  |
  */

  function buildDecision(choice, action, argsText, reason) {
    if (choice === "approve") {
      return { type: "approve" };
    }

    if (choice === "reject") {
      const decision = { type: "reject" };

      if (reason.trim()) {
        decision.message = reason.trim();
      }

      return decision;
    }

    let args;
    try {
      args = JSON.parse(argsText);
    } catch (error) {
      throw new Error("Argumen " + action.name + " belum berupa JSON yang valid.");
    }

    if (args === null || typeof args !== "object" || Array.isArray(args)) {
      throw new Error("Argumen " + action.name + " harus berupa objek JSON.");
    }

    return { type: "edit", edited_action: { name: action.name, args: args } };
  }

  /*
  |--------------------------------------------------------------------------
  | Memasang Panel
  |--------------------------------------------------------------------------
  |
  | Material memuat halaman berikutnya tanpa memuat ulang seluruh dokumen.
  | Karena itu panel dipasang lewat document$ milik Material, yang
  | dipanggil setiap kali isi halaman berganti.
  |
  */

  function mountAll() {
    document.querySelectorAll(".zul-playground:not([data-mounted])").forEach((root) => {
      root.dataset.mounted = "true";
      new Playground(root);
    });
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(mountAll);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll);
  } else {
    mountAll();
  }
})();

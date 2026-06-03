const places = [
  {
    id: "home",
    name: "出租屋",
    desc: "一间狭小但能落脚的房间。",
    x: 1,
    y: 1,
    type: "home",
    actions: [
      { label: "睡一觉", time: 1, effects: { stamina: 34, mood: 8, hunger: -10, clean: -8 }, log: "你把闹钟调早，倒头睡了一段踏实觉。" },
      { label: "洗漱整理", time: 1, cost: 6, effects: { clean: 35, mood: 4 }, log: "热水不太稳定，但整个人清爽了些。" },
      { label: "记账规划", time: 1, effects: { mood: -3, skill: 3 }, log: "你算清了今天的开销，焦虑没有消失，但方向清楚了。" }
    ]
  },
  {
    id: "labor",
    name: "劳务市场",
    desc: "临时招工的地方，机会多，风险也多。",
    x: 3,
    y: 1,
    type: "job",
    actions: [
      { label: "搬货零工", time: 1, money: 145, effects: { stamina: -32, hunger: -18, clean: -20, health: -4, skill: 1 }, log: "你跟着车队搬了半天货，肩膀很酸。" },
      { label: "工地小工", time: 2, money: 280, effects: { stamina: -52, hunger: -28, clean: -30, health: -8, mood: -5, reputation: 2 }, log: "工头结了现钱，你回家路上脚步很沉。" },
      { label: "等熟人介绍", time: 1, effects: { mood: -4, reputation: 3 }, log: "你在人群里站了一阵，记住了几个招工人的脸。" }
    ]
  },
  {
    id: "diner",
    name: "快餐店",
    desc: "便宜、热闹、能让肚子暂时安静。",
    x: 5,
    y: 1,
    type: "market",
    actions: [
      { label: "买盒饭", time: 1, cost: 18, effects: { hunger: 34, mood: 4, health: 2 }, log: "一份热盒饭让你重新有了力气。" },
      { label: "洗碗兼职", time: 1, money: 88, effects: { stamina: -18, hunger: -10, clean: -18, mood: -4 }, log: "后厨很闷，你靠着水池撑完了班。" },
      { label: "和店员聊天", time: 1, effects: { mood: 9, reputation: 2 }, log: "店员提醒你附近新开了夜班岗位。" }
    ]
  },
  {
    id: "courier",
    name: "配送站",
    desc: "订单像潮水一样来，跑得越久赚得越多。",
    x: 6,
    y: 3,
    type: "job",
    actions: [
      { label: "跑午高峰", time: 1, money: 118, effects: { stamina: -24, hunger: -16, clean: -10, health: -3, skill: 1 }, log: "你在车流里穿行，准时送完了大部分订单。" },
      { label: "跑晚高峰", time: 1, money: 132, effects: { stamina: -28, hunger: -18, mood: -3, health: -4, reputation: 1 }, log: "夜里路不好走，但单价高一点。" },
      { label: "维护电动车", time: 1, cost: 22, effects: { mood: 3, reputation: 1 }, log: "刹车终于不再尖叫，明天能少点麻烦。" }
    ]
  },
  {
    id: "school",
    name: "培训班",
    desc: "不保证翻身，但能让选择变多。",
    x: 2,
    y: 4,
    type: "school",
    actions: [
      { label: "学维修", time: 1, cost: 60, effects: { skill: 9, mood: -2, stamina: -10 }, log: "你学会了基础拆装，手艺有了点样子。" },
      { label: "练沟通", time: 1, cost: 45, effects: { skill: 5, reputation: 3, mood: 2 }, log: "你试着把话说稳，不再一开口就露怯。" },
      { label: "蹭公开课", time: 1, effects: { skill: 2, mood: 1 }, log: "免费课内容不深，但你记了几条有用信息。" }
    ]
  },
  {
    id: "market",
    name: "夜市",
    desc: "有人消费，有人讨生活。",
    x: 4,
    y: 4,
    type: "market",
    actions: [
      { label: "摆小摊", time: 1, cost: 45, money: 128, effects: { stamina: -18, mood: 4, clean: -8, reputation: 2 }, log: "你卖出几份小商品，第一次感觉钱是自己挣来的。" },
      { label: "帮摊主打杂", time: 1, money: 76, effects: { stamina: -14, hunger: -8, reputation: 2 }, log: "摊主话不多，但收摊时多给了你一瓶水。" },
      { label: "买便宜晚饭", time: 1, cost: 12, effects: { hunger: 22, mood: 2 }, log: "热气、油烟和人声，让这个夜晚没那么难熬。" }
    ]
  },
  {
    id: "clinic",
    name: "社区诊所",
    desc: "小病拖久了也会变成大问题。",
    x: 1,
    y: 5,
    type: "clinic",
    actions: [
      { label: "看诊买药", time: 1, cost: 85, effects: { health: 32, mood: -2 }, log: "医生让你少熬夜，你点头，但心里知道不容易。" },
      { label: "量血压", time: 1, cost: 8, effects: { health: 5, mood: 2 }, log: "数据还过得去，你暂时松了口气。" }
    ]
  },
  {
    id: "park",
    name: "小公园",
    desc: "城市里少数不用花钱就能喘气的地方。",
    x: 6,
    y: 5,
    type: "park",
    actions: [
      { label: "坐一会儿", time: 1, effects: { mood: 16, stamina: 8, hunger: -6 }, log: "你看着路灯亮起来，脑子慢慢安静。" },
      { label: "晨练", time: 1, effects: { health: 8, stamina: -8, mood: 6, clean: -6 }, log: "活动开身体后，你感觉自己还能再撑几天。" }
    ]
  }
];

const events = [
  {
    title: "房东催租",
    text: "房东说下周房租可能要涨，今天先让你补一部分押金。",
    choices: [
      { label: "先交 120 元稳住住处", cost: 120, effects: { mood: -5, reputation: 1 }, log: "你交了钱，至少今晚不用担心搬走。" },
      { label: "解释困难，争取缓几天", effects: { mood: -8, reputation: -1 }, log: "房东脸色不好，但暂时没有继续逼你。" }
    ]
  },
  {
    title: "家里来电话",
    text: "家里问你最近过得怎么样，你听见电话那头也不轻松。",
    choices: [
      { label: "报喜不报忧", effects: { mood: -6, reputation: 1 }, log: "你说一切都还行，挂掉电话后沉默了很久。" },
      { label: "坦白说最近很难", effects: { mood: 8 }, log: "话说出口后，你反而轻了一点。" }
    ]
  },
  {
    title: "高薪短工",
    text: "有人招夜间搬运，钱给得高，但工作强度很大。",
    choices: [
      { label: "接下这份短工", money: 210, effects: { stamina: -38, health: -9, hunger: -18, clean: -18 }, log: "你拿到了钱，也把身体往透支边缘推了一步。" },
      { label: "拒绝，明天还要继续", effects: { mood: 4, stamina: 6 }, log: "你没有接单，回去路上有点不甘心。" }
    ]
  },
  {
    title: "顾客投诉",
    text: "一个顾客把自己的错误怪到你头上，平台提醒会扣分。",
    choices: [
      { label: "忍下来，保住评分", effects: { mood: -10, reputation: 2 }, log: "你把解释咽回去，评分保住了。" },
      { label: "据理力争", effects: { mood: 3, reputation: -2 }, log: "你说清楚了事实，但平台结果不一定站在你这边。" }
    ]
  },
  {
    title: "旧手机坏了",
    text: "手机屏幕开始乱跳，再拖下去可能影响接单。",
    choices: [
      { label: "花 160 元维修", cost: 160, effects: { mood: -3, reputation: 2 }, log: "手机修好了，至少工作工具还能用。" },
      { label: "先凑合用", effects: { mood: -5, skill: 1 }, log: "你学会了怎么避开坏掉的触控区域。" }
    ]
  }
];

const maxStats = {
  stamina: 100,
  mood: 100,
  hunger: 100,
  health: 100,
  clean: 100,
  skill: 100,
  reputation: 100
};

const statNames = {
  money: "现金",
  stamina: "体力",
  mood: "情绪",
  hunger: "饱腹",
  health: "健康",
  clean: "清洁",
  skill: "技能",
  reputation: "名声"
};

const startingState = {
  day: 1,
  slot: 0,
  place: "home",
  debt: 3000,
  stats: {
    money: 260,
    stamina: 76,
    mood: 58,
    hunger: 72,
    health: 82,
    clean: 66,
    skill: 8,
    reputation: 12
  },
  log: ["你抵达这座城市，先在城中村租下一张床。"],
  finished: false
};

let state = clone(startingState);

const mapEl = document.querySelector("#map");
const actionsEl = document.querySelector("#actions");
const statsEl = document.querySelector("#stats");
const logEl = document.querySelector("#log");
const placeNameEl = document.querySelector("#placeName");
const placeDescEl = document.querySelector("#placeDesc");
const dayLabelEl = document.querySelector("#dayLabel");
const timeLabelEl = document.querySelector("#timeLabel");
const debtLabelEl = document.querySelector("#debtLabel");
const debtMeterEl = document.querySelector("#debtMeter");
const modalEl = document.querySelector("#modal");
const modalTagEl = document.querySelector("#modalTag");
const modalTitleEl = document.querySelector("#modalTitle");
const modalTextEl = document.querySelector("#modalText");
const modalChoicesEl = document.querySelector("#modalChoices");
const resetBtn = document.querySelector("#resetBtn");
const bridgeStatusEl = document.querySelector("#bridgeStatus");
const dashboardLinkEl = document.querySelector("#dashboardLink");

const timeSlots = ["上午", "下午", "晚上"];
const dashboardOrigin = window.location.protocol === "file:" ? "http://localhost:3000" : window.location.origin;
const mikaBridgeUrl = `${dashboardOrigin}/api/messages`;
let bridgeReady = false;

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function getPlace(id) {
  return places.find((place) => place.id === id);
}

function updateStat(name, amount) {
  if (name === "money") {
    state.stats.money = Math.max(0, state.stats.money + amount);
    return;
  }

  state.stats[name] = clamp(state.stats[name] + amount, 0, maxStats[name]);
}

function canPay(cost = 0) {
  return state.stats.money >= cost;
}

function applyEffects(source) {
  if (source.cost) {
    updateStat("money", -source.cost);
  }

  if (source.money) {
    updateStat("money", source.money);
  }

  Object.entries(source.effects || {}).forEach(([name, amount]) => updateStat(name, amount));
}

function addLog(text) {
  const line = `第 ${state.day} 天 ${timeSlots[state.slot]}：${text}`;
  state.log.unshift(line);
  state.log = state.log.slice(0, 12);
  publishGameEvent(line);
}

function setBridgeStatus(text, ready) {
  if (!bridgeStatusEl) {
    return;
  }
  bridgeStatusEl.textContent = text;
  bridgeStatusEl.style.color = ready ? "var(--green)" : "var(--muted)";
}

function publishGameEvent(text) {
  if (!window.fetch || !text) {
    return;
  }

  window
    .fetch(mikaBridgeUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: `[城里人游戏] ${text}` })
    })
    .then((response) => {
      bridgeReady = response.ok;
      setBridgeStatus(response.ok ? "已连接" : "未连接", response.ok);
    })
    .catch(() => {
      if (bridgeReady) {
        bridgeReady = false;
        setBridgeStatus("未连接", false);
      }
    });
}

function initializeBridgeLink() {
  if (dashboardLinkEl) {
    dashboardLinkEl.href = dashboardOrigin;
  }
}

function advanceTime(amount = 1) {
  for (let index = 0; index < amount; index += 1) {
    state.slot += 1;
    updateStat("hunger", -5);
    updateStat("stamina", -3);

    if (state.stats.hunger < 20) {
      updateStat("health", -5);
      updateStat("mood", -4);
      addLog("你饿得发慌，效率开始下降。");
    }

    if (state.stats.clean < 18) {
      updateStat("mood", -3);
      updateStat("reputation", -1);
    }

    if (state.slot >= timeSlots.length) {
      state.slot = 0;
      state.day += 1;
      updateStat("stamina", 18);
      updateStat("mood", -2);
      updateStat("hunger", -8);
      const debtPayment = Math.min(state.stats.money, state.debt, 100);
      state.debt = Math.max(0, state.debt - debtPayment);
      updateStat("money", -debtPayment);
      addLog(`你固定还了 ${debtPayment} 元债务，新的日子开始了。`);
    }
  }
}

function runAction(action) {
  if (state.finished) {
    return;
  }

  if (!canPay(action.cost)) {
    showModal({
      tag: "钱不够",
      title: "现金不够",
      text: "你摸了摸口袋，决定先去找点收入。",
      choices: [{ label: "知道了", log: "你放弃了这次消费。" }]
    });
    return;
  }

  applyEffects(action);
  addLog(action.log);
  advanceTime(action.time);
  maybeTriggerEvent();
  checkEnding();
  render();
}

function maybeTriggerEvent() {
  if (state.finished || Math.random() > 0.28) {
    return;
  }

  const event = events[Math.floor(Math.random() * events.length)];
  showModal({
    tag: "突发事件",
    title: event.title,
    text: event.text,
    choices: event.choices
  });
}

function chooseModal(choice) {
  if (choice.cost && !canPay(choice.cost)) {
    modalTitleEl.textContent = "现金不够";
    modalTextEl.textContent = "你想这么做，但现在真的拿不出这笔钱。";
    modalChoicesEl.innerHTML = "";
    const closeBtn = document.createElement("button");
    closeBtn.className = "choice-btn";
    closeBtn.type = "button";
    closeBtn.textContent = "换个办法";
    closeBtn.addEventListener("click", () => {
      modalEl.classList.add("hidden");
      render();
    });
    modalChoicesEl.append(closeBtn);
    return;
  }

  applyEffects(choice);
  addLog(choice.log);
  modalEl.classList.add("hidden");
  checkEnding();
  render();
}

function showModal({ tag, title, text, choices }) {
  modalTagEl.textContent = tag;
  modalTitleEl.textContent = title;
  modalTextEl.textContent = text;
  modalChoicesEl.innerHTML = "";

  choices.forEach((choice) => {
    const button = document.createElement("button");
    button.className = "choice-btn";
    button.type = "button";
    button.textContent = choice.label;
    button.addEventListener("click", () => chooseModal(choice));
    modalChoicesEl.append(button);
  });

  modalEl.classList.remove("hidden");
}

function checkEnding() {
  if (state.debt <= 0) {
    state.finished = true;
    showModal({
      tag: "结局",
      title: "债务还清",
      text: "你没有一步登天，但终于不用每天被债务追着走。城市还是很硬，你已经站稳了。",
      choices: [{ label: "继续留在城市", log: "你还清债务，准备开始新的阶段。" }]
    });
    return;
  }

  if (state.stats.health <= 0 || state.stats.mood <= 0) {
    state.finished = true;
    showModal({
      tag: "结局",
      title: "撑不下去了",
      text: "过度透支让你停了下来。你需要重新开始，给身体和情绪留一点余地。",
      choices: [{ label: "重新思考这段人生", log: "这一次，你准备换一种活法。" }]
    });
    return;
  }

  if (state.day > 30) {
    state.finished = true;
    const stable = state.debt < 1200 && state.stats.skill > 35;
    showModal({
      tag: "月末",
      title: stable ? "暂时站稳" : "还在挣扎",
      text: stable
        ? "一个月过去，你留下了技能、人脉和继续生活的底气。"
        : "一个月过去，债还没还完，但你已经知道这座城市的规则。",
      choices: [{ label: "查看结果", log: stable ? "你撑过第一个月，生活出现转机。" : "你撑过第一个月，仍要继续寻找机会。" }]
    });
  }
}

function renderMap() {
  mapEl.innerHTML = "";

  for (let y = 1; y <= 6; y += 1) {
    for (let x = 1; x <= 8; x += 1) {
      const place = places.find((item) => item.x === x && item.y === y);
      const tile = document.createElement("button");
      tile.type = "button";
      tile.className = `tile ${place ? `${place.type} walkable` : ""}`;

      if (place) {
        tile.setAttribute("aria-label", place.name);
        tile.addEventListener("click", () => {
          state.place = place.id;
          render();
        });

        if (place.type !== "park") {
          const building = document.createElement("span");
          building.className = "building";
          tile.append(building);
        }

        const label = document.createElement("span");
        label.className = "tile-label";
        label.textContent = place.name;
        tile.append(label);
      }

      mapEl.append(tile);
    }
  }

  const current = getPlace(state.place);
  const player = document.createElement("span");
  player.className = "player";
  player.style.left = `${((current.x - 0.5) / 8) * 100}%`;
  player.style.top = `${((current.y - 0.18) / 6) * 100}%`;
  mapEl.append(player);
}

function renderActions(place) {
  actionsEl.innerHTML = "";
  place.actions.forEach((action) => {
    const button = document.createElement("button");
    button.className = "action-btn";
    button.type = "button";
    const price = action.cost ? ` -${action.cost}元` : "";
    const income = action.money ? ` +${action.money}元` : "";
    button.textContent = `${action.label}${income}${price}`;
    button.disabled = state.finished;
    button.addEventListener("click", () => runAction(action));
    actionsEl.append(button);
  });
}

function renderStats() {
  statsEl.innerHTML = "";

  Object.entries(state.stats).forEach(([name, value]) => {
    const row = document.createElement("div");
    row.className = "stat-row";

    const label = document.createElement("span");
    label.textContent = statNames[name];

    if (name === "money") {
      const moneyLine = document.createElement("strong");
      moneyLine.textContent = `${value} 元`;
      row.append(label, document.createElement("span"), moneyLine);
      statsEl.append(row);
      return;
    }

    const bar = document.createElement("span");
    bar.className = "stat-bar";
    if (value < 25) {
      bar.classList.add("danger");
    } else if (value < 45) {
      bar.classList.add("warning");
    }

    const fill = document.createElement("i");
    fill.style.width = `${value}%`;
    bar.append(fill);

    const number = document.createElement("strong");
    number.textContent = value;
    row.append(label, bar, number);
    statsEl.append(row);
  });
}

function renderLog() {
  logEl.innerHTML = "";
  state.log.forEach((item) => {
    const line = document.createElement("li");
    line.textContent = item;
    logEl.append(line);
  });
}

function render() {
  const place = getPlace(state.place);
  dayLabelEl.textContent = `第 ${state.day} 天`;
  timeLabelEl.textContent = timeSlots[state.slot];
  placeNameEl.textContent = place.name;
  placeDescEl.textContent = place.desc;
  debtLabelEl.textContent = `${state.debt} 元`;
  debtMeterEl.style.width = `${clamp((3000 - state.debt) / 3000, 0, 1) * 100}%`;

  renderMap();
  renderActions(place);
  renderStats();
  renderLog();
}

resetBtn.addEventListener("click", () => {
  state = clone(startingState);
  modalEl.classList.add("hidden");
  publishGameEvent("城里人游戏重新开始。");
  render();
});

render();
initializeBridgeLink();
setBridgeStatus("待连接", false);
publishGameEvent("城里人游戏已打开，玩家阿成进入城市。");

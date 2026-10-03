/* 上岸花园 · 真实浏览器端到端测试（puppeteer-core + 本机 Chrome） */
const puppeteer = require('puppeteer-core');
const NODE_PATH = process.env.NODE_PATH || '';

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--window-size=420,900', '--proxy-server=direct://', '--proxy-bypass-list=*']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 414, height: 896 }); // iPhone 尺寸

  const consoleErrors = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 150)); });
  page.on('pageerror', e => consoleErrors.push('PAGEERROR: ' + String(e).slice(0, 150)));

  const results = [];
  const check = (name, ok, detail) => { results.push({ name, ok, detail }); console.log((ok ? '✅' : '❌') + ' ' + name + (detail ? '  | ' + detail : '')); };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const path = require('path');
  const URL = 'file://' + path.resolve(__dirname, '上岸花园v2.html');

  try {
    // 先写一个旧文件名的跳转备用：直接用新名字（本地产物叫上岸花园v2.html，无中文名问题）
    // ===== T0: 新手向导（首次打开弹出→选择→跳过AI→标记完成）=====
    const resp = await page.goto(URL, { waitUntil: 'networkidle2', timeout: 30000 });
    check('T1 页面加载', resp.ok(), 'HTTP ' + resp.status());
    await sleep(3200); // 等2.5s引导延迟
    const wizShown = await page.evaluate(() => document.getElementById('mask').classList.contains('on') && document.getElementById('sheet').innerHTML.indexOf('欢迎来到上岸花园') >= 0);
    check('T0a 首次打开弹引导', wizShown, '');
    if (wizShown) {
      await page.evaluate(() => { document.querySelector('[data-exam="both"]').click(); });
      await page.evaluate(() => { document.getElementById('wiz-next1').click(); });
      await sleep(300);
      const step2 = await page.evaluate(() => document.getElementById('sheet').innerHTML.indexOf('配置 AI') >= 0);
      check('T0b 向导第二步AI配置', step2, '');
      await page.evaluate(() => { document.getElementById('wiz-ai-skip').click(); });
      await sleep(400);
      const done = await page.evaluate(() => !!JSON.parse(localStorage.getItem('wb_garden_onboarded') || 'null'));
      check('T0c 完成标记写入', done, '');
    }
    // ===== T1.5: 页面加载完成 =====
    await sleep(300);

    // ===== T0d: 向导只弹一次（刷新后不再弹 + 点遮罩关闭=今日免扰 + 设置里可重开）=====
    await page.reload({ waitUntil: 'networkidle2' });
    await sleep(3200);
    const t0d = await page.evaluate(() => ({
      maskOn: document.getElementById('mask').classList.contains('on'),
      onboarded: !!JSON.parse(localStorage.getItem('wb_garden_onboarded') || 'null')
    }));
    check('T0d 完成向导后刷新不再弹', !t0d.maskOn && t0d.onboarded, '');
    // 清掉完成标记模拟"用户直接点遮罩关掉"的场景
    await page.evaluate(() => {
      localStorage.removeItem('wb_garden_onboarded');
      localStorage.removeItem('wb_garden_wizard_step');
    });
    await page.reload({ waitUntil: 'networkidle2' });
    await sleep(3200);
    const t0e1 = await page.evaluate(() => document.getElementById('mask').classList.contains('on'));
    check('T0e-1 未完成时再次弹出', t0e1, '');
    // 点遮罩空白关闭 → 写入今日免扰标记
    await page.evaluate(() => { document.getElementById('mask').click(); });
    await sleep(300);
    const t0e2 = await page.evaluate(() => {
      const sn = JSON.parse(localStorage.getItem('wb_garden_wizard_snooze') || 'null');
      const today = new Date();
      const key = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');
      return { snooze: sn && sn.date === key, maskOff: !document.getElementById('mask').classList.contains('on') };
    });
    check('T0e-2 点遮罩关闭=今日不再弹', t0e2.snooze && t0e2.maskOff, '');
    // 同日再刷新不弹；设置中心可重新打开向导
    await page.reload({ waitUntil: 'networkidle2' });
    await sleep(3200);
    const t0e3 = await page.evaluate(() => !document.getElementById('mask').classList.contains('on'));
    check('T0e-3 当日刷新不再弹', t0e3, '');
    await page.evaluate(() => { document.getElementById('btn-settings').click(); });
    await sleep(300);
    const t0e4 = await page.evaluate(() => {
      const el = document.querySelector('[data-set="wizard"]');
      if (el) el.click();
      return { has: !!el };
    });
    await sleep(300);
    const t0e5 = await page.evaluate(() => document.getElementById('wiz-skip-top') !== null && document.getElementById('mask').classList.contains('on'));
    check('T0f 设置中心可重开向导+跳过链接', t0e4.has && t0e5, '');
    // 恢复完成状态，不影响后续用例
    await page.evaluate(() => {
      document.getElementById('wiz-skip-top').click();
    });
    await sleep(200);
    await page.evaluate(() => { localStorage.setItem('wb_garden_onboarded', JSON.stringify({ date: 'e2e', v: 1 })); });

    // ===== T2: 无 JS 报错 =====
    check('T2 无JS报错', consoleErrors.length === 0, consoleErrors.slice(0, 2).join(' / ') || 'clean');

    // ===== T3: 云端连接状态（skoo SDK 初始化可能失败，离线模式也算过） =====
    const syncText = await page.evaluate(() => { const el = document.getElementById('sync-state'); return el ? el.textContent : '(无sync-state)'; });
    check('T3 同步状态显示', /云端|离线/.test(syncText), syncText);

    // ===== T4: 首页 KPI 渲染 =====
    const kpis = await page.evaluate(() => ({
      streak: document.getElementById('kpi-streak') ? document.getElementById('kpi-streak').textContent : null,
      hours: document.getElementById('kpi-sun') ? document.getElementById('kpi-sun').textContent : null,
      sunLabel: document.querySelector('#kpi-sun') ? (document.getElementById('kpi-sun').parentElement.querySelector('.l') || {}).textContent : null
    }));
    check('T4a 连续打卡KPI', kpis.streak !== null && /\d/.test(kpis.streak), '显示=' + kpis.streak);
    check('T4b 累计打卡(h)KPI', kpis.hours !== null && /累计打卡/.test(kpis.sunLabel || ''), '显示=' + kpis.hours + ' 标签=' + kpis.sunLabel);

    // ===== T5: 今日计划卡（今天是周六=轻量日）=====
    const planHtml = await page.evaluate(() => (document.getElementById('home-plan') || {}).innerHTML || '');
    check('T5 今日计划卡', planHtml.length > 200, '长度' + planHtml.length + ' 含复盘=' + /复盘/.test(planHtml));

    // ===== T6: 花园 + 阳光区 =====
    const sunZone = await page.evaluate(() => !!document.getElementById('sun-zone'));
    check('T6 首页阳光掉落区', sunZone);

    // ===== T7: 导航到计划页（日历）=====
    await page.evaluate(() => { document.querySelector('[data-nav="plan"]').click(); });
    await sleep(400);
    const planPage = await page.evaluate(() => {
      const on = document.getElementById('page-plan');
      return { visible: on && on.classList.contains('on'), cal: !!document.querySelector('[data-calday]'), title: (document.getElementById('topbar-title') || {}).textContent };
    });
    check('T7a 计划页切换', planPage.visible && /计划/.test(planPage.title), '标题=' + planPage.title);
    check('T7b 日历渲染', planPage.cal, '');

    // ===== T8: 点日期弹详情 =====
    await page.evaluate(() => { const c = document.querySelector('[data-calday="2026-10-05"]'); if (c) c.click(); });
    await sleep(400);
    const t8 = await page.evaluate(() => ({
      maskOn: document.getElementById('mask').classList.contains('on'),
      full: document.getElementById('sheet').classList.contains('full'),
      hasW1: document.getElementById('sheet').innerHTML.indexOf('申论启动') >= 0,
      hasClose: !!document.querySelector('[data-sf-close]')
    }));
    check('T8a 日历点日期弹详情', t8.maskOn && t8.full, 'W1主题=' + t8.hasW1);

    // ===== T9: 关闭弹窗 → full 类清理（验证本轮修的 bug）=====
    await page.evaluate(() => { document.querySelector('[data-sf-close]').click(); });
    await sleep(300);
    const t9 = await page.evaluate(() => ({
      maskOn: document.getElementById('mask').classList.contains('on'),
      fullLeft: document.getElementById('sheet').classList.contains('full')
    }));
    check('T9 关闭后full类清理(本轮bug修复)', !t9.maskOn && !t9.fullLeft, 'maskOn=' + t9.maskOn + ' full残留=' + t9.fullLeft);

    // ===== T10: 时政页（33条 + 分组 + 展开收起）=====
    await page.evaluate(() => { document.querySelector('[data-nav="affairs"]').click(); });
    await sleep(400);
    const t10 = await page.evaluate(() => {
      const items = document.querySelectorAll('#affairs-list [data-affairoopen]').length;
      const heads = document.querySelectorAll('[data-affairdate]');
      const chips = document.querySelectorAll('[data-affaircat]').length;
      // 点第一个日期头收起
      const h0 = heads[0];
      const before = document.querySelectorAll('#affairs-list [data-affairoopen]').length;
      h0.click();
      const after = document.querySelectorAll('#affairs-list [data-affairoopen]').length;
      return { items, groups: heads.length, chips, expandWorked: after !== before, after };
    });
    check('T10a 时政展开组=最新一天条数', t10.items === 18, '展开' + t10.items + '条(默认只展开最新组,共33条入库)');
    check('T10b 日期分组≥2', t10.groups >= 2, '组数' + t10.groups);
    check('T10c 分类筛选chips', t10.chips >= 3, 'chips=' + t10.chips);
    check('T10d 展开收起交互', t10.expandWorked, '点击后可见条数=' + t10.after);

    // ===== T11: 申论页 4 tab =====
    await page.evaluate(() => { document.querySelector('[data-nav="essay"]').click(); });
    await sleep(300);
    const t11 = await page.evaluate(() => {
      const tabs = [...document.querySelectorAll('[data-essaytab]')].map(b => b.getAttribute('data-essaytab'));
      // 点「我的申论」
      const pr = document.querySelector('[data-essaytab="practice"]');
      if (pr) pr.click();
      return { tabs, practiceBtn: !!document.getElementById('btn-new-practice') };
    });
    await sleep(300);
    check('T11a 申论4tab', t11.tabs.length === 4 && t11.tabs.indexOf('practice') >= 0 && t11.tabs.indexOf('tools') >= 0, t11.tabs.join(','));
    check('T11b 我的申论练笔入口', t11.practiceBtn, '');

    // ===== T12: 打开练笔编辑器 + 本地评分全流程 =====
    await page.evaluate(() => { document.getElementById('btn-new-practice').click(); });
    await sleep(400);
    const t12 = await page.evaluate(() => {
      const title = document.getElementById('pr-title');
      const answer = document.getElementById('pr-answer');
      if (!title || !answer) return { ok: false };
      title.value = '测试：以创新为题写议论文';
      answer.value = '创新是引领发展的第一动力。\n\n第一，坚持创新驱动，久久为功。\n\n第二，突破关键核心技术，科技自立自强。\n\n总之，推动高质量发展。';
      return { ok: true, aiState: (document.getElementById('pr-ai-state') || {}).textContent || '' };
    });
    check('T12a 练笔编辑器打开+填写', t12.ok, 'AI状态=' + (t12.aiState || '').slice(0, 30));
    // 提交评分（本地规则，无AI key）
    await page.evaluate(() => { document.getElementById('btn-pr-score').click(); });
    await sleep(800);
    const t12b = await page.evaluate(() => {
      const maskOn = document.getElementById('mask').classList.contains('on');
      const sheet = document.getElementById('sheet').innerHTML;
      const saved = JSON.parse(localStorage.getItem('wb_garden_my_shenlun') || '[]');
      return { maskOn, hasScore: /分维度评分|分</.test(sheet), saved: saved.length, byAI: saved.length && saved[saved.length - 1].byAI };
    });
    check('T12b 本地评分出结果', t12b.maskOn && t12b.saved >= 1, '历史' + t12b.saved + '条 byAI=' + t12b.byAI);
    // 清掉测试数据
    await page.evaluate(() => {
      const list = JSON.parse(localStorage.getItem('wb_garden_my_shenlun') || '[]');
      list.pop(); localStorage.setItem('wb_garden_my_shenlun', JSON.stringify(list));
    });
    await page.evaluate(() => { const c = document.querySelector('[data-sf-close]'); if (c) c.click(); });

    // ===== T13: 打卡全流程（错题标签→数量输入联动→自动汇总→真实提交→数据页联动）=====
    const streakBefore = await page.evaluate(() => document.getElementById('kpi-streak').textContent);
    await page.evaluate(() => { document.querySelector('[data-nav="checkin"]').click(); });
    await sleep(400);
    // 勾一个模块标签 + 填数据 + 提交（前后对比法）
    const cntBefore = await page.evaluate(() => (JSON.parse(localStorage.getItem('wb_garden_checkin') || '[]')).length);
    const t13 = await page.evaluate(() => {
      const tag = document.querySelector('[data-ckcat]');
      if (tag) tag.click();
      const total = document.getElementById('ck-total');
      const wrong = document.getElementById('ck-wrong');
      const hours = document.getElementById('ck-hours');
      if (total) total.value = '';
      if (wrong) wrong.value = '';
      if (hours) hours.value = '1';
      return { hasForm: !!document.getElementById('btn-ck-submit'), tagSelected: !!tag };
    });
    await sleep(300);
    // N1: 选错题标签后，数量输入框自动出现
    const t13n1 = await page.evaluate(() => {
      const tags = document.querySelectorAll('#ck-wrong-tags [data-ckwrong]');
      if (!tags.length) return { has: false };
      tags[0].click();
      return { has: true, count: tags.length };
    });
    await sleep(300);
    const t13n2 = await page.evaluate(() => {
      const rows = document.querySelectorAll('#ck-wrong-qty [data-wq]');
      const inp = document.querySelector('#ck-wrong-qty [data-wqtotal]');
      return { rows: rows.length, hasInput: !!inp };
    });
    check('T13-N1 选错题标签后出现数量输入框', t13n1.has && t13n2.rows >= 1 && t13n2.hasInput, '标签' + (t13n1.count || 0) + '个 输入行' + t13n2.rows + '行');
    // N2: 填数量 → 自动汇总出现且数字正确（20题错6 → 错误率70%）
    const t13n3 = await page.evaluate(() => {
      const total = document.querySelector('#ck-wrong-qty [data-wqtotal]');
      const wrongI = document.querySelector('#ck-wrong-qty [data-wqwrong]');
      if (!total || !wrongI) return { ok: false };
      total.value = '20'; total.dispatchEvent(new Event('input', { bubbles: true }));
      wrongI.value = '6'; wrongI.dispatchEvent(new Event('input', { bubbles: true }));
      return { ok: true };
    });
    await sleep(300);
    const t13n4 = await page.evaluate(() => {
      const sum = document.getElementById('ck-wrong-sum') ? document.getElementById('ck-wrong-sum').textContent : '';
      return { sum, hasTotal: sum.indexOf('20') >= 0 && sum.indexOf('6') >= 0, hasRate: sum.indexOf('70%') >= 0 };
    });
    check('T13-N2 填数量后自动汇总(20题错6→70%)', t13n3.ok && t13n4.hasTotal && t13n4.hasRate, '汇总=' + t13n4.sum.slice(0, 60));
    // N3: 提交打卡（带数量明细）
    await page.evaluate(() => {
      const s = document.getElementById('btn-ck-submit');
      if (s) s.click();
    });
    await sleep(1800);
    const t13b = await page.evaluate((cnt) => {
      const saved = JSON.parse(localStorage.getItem('wb_garden_checkin') || '[]');
      const today = new Date();
      const key = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');
      const todayRec = saved.filter(c => String(c['日期'] || '').indexOf(key) === 0);
      const studySaved = JSON.parse(localStorage.getItem('wb_garden_study') || '[]');
      const todayStudy = studySaved.filter(s => String(s['日期'] || '').indexOf(key) === 0 && s['类型'] === '打卡记录');
      const sum20 = todayStudy.some(s => Number(s['题量']) === 20 && Number(s['错题数']) === 6);
      return { delta: saved.length - cnt, todayRec: todayRec.length, studyCnt: todayStudy.length, sum20 };
    }, cntBefore);
    check('T13a 打卡表单提交', t13.hasForm && t13.tagSelected && t13b.todayRec >= 1, '新增' + t13b.delta + '条 今日记录' + t13b.todayRec + '条');
    check('T13-N3 学习记录按数量明细写入(20题/错6)', t13b.studyCnt >= 1 && t13b.sum20, '打卡记录写入' + t13b.studyCnt + '条 明细匹配=' + t13b.sum20);
    // N4: 数据页模块学习量/正确率联动（开源版空基线，只有本次打卡的20题）
    await page.evaluate(() => {
      const b = document.querySelector('[data-nav="data"]');
      if (b) b.click();
    });
    await sleep(500);
    const t13n5 = await page.evaluate(() => {
      const mc = document.getElementById('data-module-chart') ? document.getElementById('data-module-chart').textContent : '';
      return { mcSum: /政治理论20题/.test(mc) };
    });
    check('T13-N4 数据页联动(本次打卡20题计入)', t13n5.mcSum, '学习量图含政治理论20题=' + t13n5.mcSum);
    // 回首页看比对
    await page.evaluate(() => { document.querySelector('[data-nav="home"]').click(); });
    await sleep(500);
    const t13c = await page.evaluate(() => {
      const hp = document.getElementById('home-plan') ? document.getElementById('home-plan').innerHTML : '';
      return { cmp: hp.indexOf('计划比对') >= 0, level: /按计划|轻度偏差|明显偏差/.test(hp), streak: document.getElementById('kpi-streak').textContent, hours: document.getElementById('kpi-sun').textContent };
    });
    check('T13b 打卡后出现计划比对', t13c.cmp && t13c.level, 'streak=' + t13c.streak + ' 累计=' + t13c.hours + 'h (打卡前streak=' + streakBefore + ')');

    // ===== T14: 复盘中心全流程 =====
    await page.evaluate(() => { const b = document.querySelector('[data-navreview]'); if (b) b.click(); });
    await sleep(500);
    const t14 = await page.evaluate(() => {
      const sh = document.getElementById('sheet').innerHTML;
      const ok = sh.indexOf('复盘中心') >= 0 && sh.indexOf('本周学习快照') >= 0;
      const learned = document.getElementById('rev-learned');
      const errors = document.getElementById('rev-errors');
      if (learned) learned.value = 'E2E测试：因果标志词';
      if (errors) errors.value = 'E2E测试：篇章阅读超时';
      const save = document.getElementById('rev-save');
      if (save) save.click();
      return { ok, saved: !!save };
    });
    await sleep(500);
    const t14b = await page.evaluate(() => {
      const notes = JSON.parse(localStorage.getItem('wb_garden_review_notes') || '[]');
      return { count: notes.length, last: notes.length ? notes[notes.length - 1].learned : '' };
    });
    check('T14 复盘中心打开+笔记保存', t14.ok && t14b.count >= 1 && /E2E测试/.test(t14b.last), '笔记' + t14b.count + '条');
    // 清测试数据
    await page.evaluate(() => { localStorage.removeItem('wb_garden_review_notes'); });

    // ===== T15: 规则引擎偏差分析（无需AI key，点AI按钮走降级）=====
    await page.evaluate(() => { const b = document.querySelector('[data-navreview]'); if (b) b.click(); });
    await sleep(600);
    const hasAiBtn = await page.evaluate(() => !!document.getElementById('btn-ai-gap'));
    if (hasAiBtn) {
      // 注入假 key（与页面 lsSet 同格式：JSON 字符串）触发真实 API 失败 → 验证规则引擎降级
      await page.evaluate(() => { localStorage.setItem('wb_garden_glm_api_key', JSON.stringify('fake_key_for_e2e')); });
      await page.evaluate(() => { document.getElementById('btn-ai-gap').click(); });
      await sleep(4000);
      const t15 = await page.evaluate(() => {
        const sh = document.getElementById('sheet').innerHTML;
        const tt = document.querySelectorAll('.sf-head .tt');
        const title = tt.length ? tt[tt.length - 1].textContent : '';
        return { title, hasContent: sh.indexOf('完成度') >= 0, rule: sh.indexOf('规则引擎') >= 0, ai: sh.indexOf('🤖 AI') >= 0, loading: sh.indexOf('AI 正在') >= 0 };
      });
      await page.evaluate(() => { localStorage.removeItem('wb_garden_glm_api_key'); });
      check('T15 偏差分析(API拦截→规则引擎降级)', t15.hasContent && (t15.rule || t15.ai || t15.loading), '标题=' + t15.title);
    } else {
      check('T15 偏差分析入口', false, 'btn-ai-gap未找到');
    }

    // ===== T16: 调整记录管理页 =====
    await page.evaluate(() => { const c = document.querySelector('[data-sf-close]'); if (c) c.click(); });
    await sleep(200);
    await page.evaluate(() => { document.querySelector('[data-nav="plan"]').click(); });
    await sleep(400);
    await page.evaluate(() => { const b = document.querySelector('[data-adjmgr]'); if (b) b.click(); });
    await sleep(400);
    const t16 = await page.evaluate(() => {
      const sh = document.getElementById('sheet').innerHTML;
      return { ok: sh.indexOf('计划调整记录') >= 0 && sh.indexOf('自己写一条调整') >= 0 };
    });
    check('T16 调整记录管理页', t16.ok, '');

    // ===== T17: 花园页 + 数据页导航不报错 =====
    await page.evaluate(() => { const c = document.querySelector('[data-sf-close]'); if (c) c.click(); });
    await page.evaluate(() => { document.querySelector('[data-nav="garden"]').click(); });
    await sleep(400);
    await page.evaluate(() => { document.querySelector('[data-nav="data"]').click(); });
    await sleep(400);
    check('T17 花园页+数据页导航', consoleErrors.filter(e => e.indexOf('401') < 0).length === 0, consoleErrors.slice(0, 2).join(' / ') || 'clean');

    // ===== T18: 历史数据补录（设置中心入口 → 非法输入报错 → 合法补录 → 联动）=====
    await page.evaluate(() => { document.getElementById('btn-settings').click(); });
    await sleep(400);
    const t18entry = await page.evaluate(() => {
      const el = document.querySelector('[data-set="backfill"]');
      if (el) el.click();
      return { has: !!el };
    });
    await sleep(400);
    const t18open = await page.evaluate(() => document.getElementById('sheet').innerHTML.indexOf('历史数据补录') >= 0 && !!document.getElementById('bf-save'));
    check('T18a 补录入口+面板打开', t18entry.has && t18open, '');
    // T18b: 非法输入（文字）→ 报错不写入
    const t18b = await page.evaluate(() => {
      const row = document.querySelector('.bf-mod-row');
      row.querySelector('[data-bf="total"]').value = '不想管的文字';
      row.querySelector('[data-bf="right"]').value = '30';
      document.getElementById('bf-save').click();
      const err = document.getElementById('bf-err');
      return { shown: err.style.display !== 'none', msg: err.textContent };
    });
    check('T18b 非数字报错拦截', t18b.shown && t18b.msg.indexOf('不是有效数字') >= 0, t18b.msg.slice(0, 40));
    // T18c: 做对数>总题量 → 报错
    const t18c = await page.evaluate(() => {
      const row = document.querySelector('.bf-mod-row');
      row.querySelector('[data-bf="mod"]').value = '数量关系';
      row.querySelector('[data-bf="total"]').value = '20';
      row.querySelector('[data-bf="right"]').value = '35';
      document.getElementById('bf-save').click();
      const err = document.getElementById('bf-err');
      return { shown: err.style.display !== 'none', msg: err.textContent };
    });
    check('T18c 做对数>总题量拦截', t18c.shown && t18c.msg.indexOf('不能大于') >= 0, t18c.msg.slice(0, 40));
    // T18d: 空提交 → 报错
    const t18d = await page.evaluate(() => {
      document.querySelector('.bf-mod-row [data-bf="total"]').value = '';
      document.querySelector('.bf-mod-row [data-bf="right"]').value = '';
      document.getElementById('bf-save').click();
      const err = document.getElementById('bf-err');
      return { shown: err.style.display !== 'none', msg: err.textContent };
    });
    check('T18d 空提交拦截', t18d.shown && t18d.msg.indexOf('至少补录一项') >= 0, t18d.msg.slice(0, 30));
    // T18e: 合法补录（数量关系 100题对55 + 申论3篇62分 + 模考）→ 成功写入
    const t18e = await page.evaluate(() => {
      const row = document.querySelector('.bf-mod-row');
      row.querySelector('[data-bf="mod"]').value = '数量关系';
      row.querySelector('[data-bf="total"]').value = '100';
      row.querySelector('[data-bf="right"]').value = '55';
      document.getElementById('bf-sl-count').value = '3';
      document.getElementById('bf-sl-score').value = '62';
      const mr = document.querySelector('.bf-mock-row');
      mr.querySelector('[data-bf="mdate"]').value = '2026-08-15';
      mr.querySelector('[data-bf="mscope"]').value = '行测';
      mr.querySelector('[data-bf="mscore"]').value = '58';
      mr.querySelector('[data-bf="mfull"]').value = '100';
      document.getElementById('bf-save').click();
      return true;
    });
    await sleep(1200);
    const t18f = await page.evaluate(() => {
      const study = JSON.parse(localStorage.getItem('wb_garden_study') || '[]');
      const bf = study.find(s => s['类型'] === '历史基线' && String(s['备注'] || '').indexOf('【历史补录】') >= 0 && Number(s['题量']) === 100);
      const sl = JSON.parse(localStorage.getItem('wb_garden_my_shenlun') || '[]');
      const bfSl = sl.filter(x => x.backfill);
      const mocks = JSON.parse(localStorage.getItem('wb_garden_bf_mocks') || '[]');
      const maskOn = document.getElementById('mask').classList.contains('on');
      return { hasMod: !!bf, hasModRight: bf && Number(bf['错题数']) === 45, slBackfill: bfSl.length, slFirstScore: bfSl.length ? bfSl[0].score : null, mocks: mocks.length, sheetClosed: !maskOn };
    });
    check('T18e 合法补录写入(刷题+申论+模考)', t18f.hasMod && t18f.hasModRight && t18f.slBackfill === 3 && t18f.slFirstScore === 62 && t18f.mocks >= 1 && t18f.sheetClosed, '刷题' + (t18f.hasMod ? '✓' : '✗') + ' 申论' + t18f.slBackfill + '篇(首篇' + t18f.slFirstScore + '分) 模考' + t18f.mocks + '次');
    // T18f: 数据页联动（空基线 + 补录100 = 数量关系100题）
    await page.evaluate(() => { document.querySelector('[data-nav="data"]').click(); });
    await sleep(500);
    const t18g = await page.evaluate(() => {
      const mc = document.getElementById('data-module-chart') ? document.getElementById('data-module-chart').textContent : '';
      return { has249: /数量关系100题/.test(mc) };
    });
    check('T18f 补录后数据页联动(数量关系100题)', t18g.has249, '学习量图含数量关系100题=' + t18g.has249);
    // 清理补录测试数据（恢复 E2E 基线状态）
    await page.evaluate(() => {
      const study = JSON.parse(localStorage.getItem('wb_garden_study') || '[]');
      localStorage.setItem('wb_garden_study', JSON.stringify(study.filter(s => String(s['备注'] || '').indexOf('【历史补录】') < 0)));
      const sl = JSON.parse(localStorage.getItem('wb_garden_my_shenlun') || '[]');
      localStorage.setItem('wb_garden_my_shenlun', JSON.stringify(sl.filter(x => !x.backfill)));
      localStorage.removeItem('wb_garden_bf_mocks');
    });

  } catch (e) {
    check('测试执行异常', false, String(e).slice(0, 120));
  }

  // 汇总
  const pass = results.filter(r => r.ok).length;
  console.log('\n========== E2E 汇总: ' + pass + '/' + results.length + ' 通过 ==========');
  if (consoleErrors.length) console.log('控制台错误清单:\n' + consoleErrors.slice(0, 5).join('\n'));

  await browser.close();
  process.exit(pass === results.length ? 0 : 1);
})();

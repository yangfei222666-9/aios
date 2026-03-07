// ==================== 核心调度引擎 ====================
class TripleAIEngine {
    constructor() {
        // API配置
        this.apiKey = '';
        this.endpoint = '';
        this.modelDoubao = '';
        this.modelDeepseek = '';
        this.modelGLM = '';

        // 统计
        this.totalTokens = 0;
        this.dsCalls = 0;
        this.glmCalls = 0;
        this.lastTokenUsage = 0;

        // 状态
        this.phase = 'idle'; // 'idle', 'discussion', 'production'
        this.projectCore = '';
        this.consensusJSON = {}; // 讨论共识

        // 讨论阶段
        this.discussionActive = false;
        this.discussionPaused = false;
        this.discussionAbort = false;
        this.discussionTotal = 3;
        this.discussionCurrent = 0;
        this.discussionHistory = [];

        // 制作阶段
        this.productionActive = false;
        this.productionPaused = false;
        this.productionAbort = false;
        this.productionTotal = 13;
        this.productionCurrent = 0;
        this.productionHistory = [];

        // 插队指令队列
        this.interruptQueue = [];

        // 温度、摘要字数、max_tokens
        this.temperature = 0.3;
        this.showThinking = true;
        this.summaryWordLimit = 300;
        this.maxTokens = 8000;

        // 预览自动刷新
        this.autoRefresh = false;

        // 全量对话历史
        this.conversationHistory = [];

        // 当前预览的HTML内容
        this.currentPreviewHtml = '';

        // DOM元素引用（将在bindElements中设置）
        this.elements = {};
    }

    // 绑定所有DOM元素
    bindElements(elements) {
        this.elements = elements;
    }

    // 加载本地设置
    loadSettings() {
        this.apiKey = localStorage.getItem('volcano_api_key') || '';
        this.modelDoubao = localStorage.getItem('model_doubao') || '';
        this.modelDeepseek = localStorage.getItem('model_deepseek') || '';
        this.modelGLM = localStorage.getItem('model_glm') || '';
        if (this.elements.apiKey) this.elements.apiKey.value = this.apiKey;
        if (this.elements.modelDoubao) this.elements.modelDoubao.value = this.modelDoubao;
        if (this.elements.modelDeepseek) this.elements.modelDeepseek.value = this.modelDeepseek;
        if (this.elements.modelGLM) this.elements.modelGLM.value = this.modelGLM;
        if (this.elements.apiEndpoint) this.endpoint = this.elements.apiEndpoint.value.trim();

        const savedTemp = localStorage.getItem('temperature');
        if (savedTemp) {
            this.temperature = parseFloat(savedTemp);
            if (this.elements.temperatureSlider) this.elements.temperatureSlider.value = this.temperature;
            if (this.elements.tempDisplay) this.elements.tempDisplay.textContent = this.temperature.toFixed(1);
        }

        const savedMaxTokens = localStorage.getItem('maxTokens');
        if (savedMaxTokens) {
            this.maxTokens = parseInt(savedMaxTokens);
            if (this.elements.maxTokensSlider) this.elements.maxTokensSlider.value = this.maxTokens;
            if (this.elements.maxTokensDisplay) this.elements.maxTokensDisplay.textContent = this.maxTokens;
        }

        const showThink = localStorage.getItem('showThinking');
        if (showThink !== null) {
            this.showThinking = showThink === 'true';
            if (this.elements.showThinking) this.elements.showThinking.checked = this.showThinking;
        }

        const savedWordLimit = localStorage.getItem('summaryWordLimit');
        if (savedWordLimit) {
            this.summaryWordLimit = parseInt(savedWordLimit);
            if (this.elements.summaryLimitSlider) this.elements.summaryLimitSlider.value = this.summaryWordLimit;
            if (this.elements.summaryLimitDisplay) this.elements.summaryLimitDisplay.textContent = this.summaryWordLimit;
        }

        const savedDiscussionRounds = localStorage.getItem('discussionRounds');
        if (savedDiscussionRounds) {
            this.discussionTotal = parseInt(savedDiscussionRounds);
            if (this.elements.discussionRoundsSlider) this.elements.discussionRoundsSlider.value = this.discussionTotal;
            if (this.elements.discussionRoundsDisplay) this.elements.discussionRoundsDisplay.textContent = this.discussionTotal;
        }

        const savedProductionRounds = localStorage.getItem('productionRounds');
        if (savedProductionRounds) {
            this.productionTotal = parseInt(savedProductionRounds);
            if (this.elements.productionRoundsSlider) this.elements.productionRoundsSlider.value = this.productionTotal;
            if (this.elements.productionRoundsDisplay) this.elements.productionRoundsDisplay.textContent = this.productionTotal;
        }

        this.updateAllUI();
    }

    // 保存设置
    saveSettings() {
        localStorage.setItem('volcano_api_key', this.apiKey);
        localStorage.setItem('model_doubao', this.modelDoubao);
        localStorage.setItem('model_deepseek', this.modelDeepseek);
        localStorage.setItem('model_glm', this.modelGLM);
        localStorage.setItem('temperature', this.temperature);
        localStorage.setItem('maxTokens', this.maxTokens);
        localStorage.setItem('showThinking', this.showThinking);
        localStorage.setItem('summaryWordLimit', this.summaryWordLimit);
        localStorage.setItem('discussionRounds', this.discussionTotal);
        localStorage.setItem('productionRounds', this.productionTotal);
    }

    // 绑定事件监听
    attachEvents() {
        // 滑块事件
        if (this.elements.temperatureSlider) {
            this.elements.temperatureSlider.addEventListener('input', (e) => {
                this.temperature = parseFloat(e.target.value);
                if (this.elements.tempDisplay) this.elements.tempDisplay.textContent = this.temperature.toFixed(1);
                localStorage.setItem('temperature', this.temperature);
            });
        }
        if (this.elements.maxTokensSlider) {
            this.elements.maxTokensSlider.addEventListener('input', (e) => {
                this.maxTokens = parseInt(e.target.value);
                if (this.elements.maxTokensDisplay) this.elements.maxTokensDisplay.textContent = this.maxTokens;
                localStorage.setItem('maxTokens', this.maxTokens);
            });
        }
        if (this.elements.summaryLimitSlider) {
            this.elements.summaryLimitSlider.addEventListener('input', (e) => {
                this.summaryWordLimit = parseInt(e.target.value);
                if (this.elements.summaryLimitDisplay) this.elements.summaryLimitDisplay.textContent = this.summaryWordLimit;
                localStorage.setItem('summaryWordLimit', this.summaryWordLimit);
            });
        }
        if (this.elements.showThinking) {
            this.elements.showThinking.addEventListener('change', (e) => {
                this.showThinking = e.target.checked;
                localStorage.setItem('showThinking', this.showThinking);
            });
        }

        // API配置保存
        if (this.elements.apiKey) {
            this.elements.apiKey.addEventListener('change', () => {
                this.apiKey = this.elements.apiKey.value.trim();
                this.saveSettings();
            });
        }
        if (this.elements.modelDoubao) {
            this.elements.modelDoubao.addEventListener('change', () => {
                this.modelDoubao = this.elements.modelDoubao.value.trim();
                this.saveSettings();
            });
        }
        if (this.elements.modelDeepseek) {
            this.elements.modelDeepseek.addEventListener('change', () => {
                this.modelDeepseek = this.elements.modelDeepseek.value.trim();
                this.saveSettings();
            });
        }
        if (this.elements.modelGLM) {
            this.elements.modelGLM.addEventListener('change', () => {
                this.modelGLM = this.elements.modelGLM.value.trim();
                this.saveSettings();
            });
        }
        if (this.elements.apiEndpoint) {
            this.elements.apiEndpoint.addEventListener('change', () => {
                this.endpoint = this.elements.apiEndpoint.value.trim();
            });
        }

        // 讨论轮数滑块
        if (this.elements.discussionRoundsSlider) {
            this.elements.discussionRoundsSlider.addEventListener('input', (e) => {
                this.discussionTotal = parseInt(e.target.value);
                if (this.elements.discussionRoundsDisplay) this.elements.discussionRoundsDisplay.textContent = this.discussionTotal;
                localStorage.setItem('discussionRounds', this.discussionTotal);
                this.updateDiscussionProgress();
            });
        }
        // 制作轮数滑块
        if (this.elements.productionRoundsSlider) {
            this.elements.productionRoundsSlider.addEventListener('input', (e) => {
                this.productionTotal = parseInt(e.target.value);
                if (this.elements.productionRoundsDisplay) this.elements.productionRoundsDisplay.textContent = this.productionTotal;
                localStorage.setItem('productionRounds', this.productionTotal);
                this.updateProductionProgress();
            });
        }

        // 讨论控制按钮
        if (this.elements.startDiscussionBtn) {
            this.elements.startDiscussionBtn.addEventListener('click', () => this.startDiscussion());
        }
        if (this.elements.pauseDiscussionBtn) {
            this.elements.pauseDiscussionBtn.addEventListener('click', () => this.pauseDiscussion());
        }
        if (this.elements.stopDiscussionBtn) {
            this.elements.stopDiscussionBtn.addEventListener('click', () => this.stopDiscussion());
        }

        // 制作控制按钮
        if (this.elements.startProductionBtn) {
            this.elements.startProductionBtn.addEventListener('click', () => this.startProduction());
        }
        if (this.elements.pauseProductionBtn) {
            this.elements.pauseProductionBtn.addEventListener('click', () => this.pauseProduction());
        }
        if (this.elements.stopProductionBtn) {
            this.elements.stopProductionBtn.addEventListener('click', () => this.stopProduction());
        }

        // 插队指令
        if (this.elements.sendInterrupt) {
            this.elements.sendInterrupt.addEventListener('click', () => this.sendInterruptCommand());
        }

        // 单轮发送
        if (this.elements.sendBtn) {
            this.elements.sendBtn.addEventListener('click', () => this.handleSingleRound());
        }
        if (this.elements.userInput) {
            this.elements.userInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSingleRound();
                }
            });
        }

        // 导出、打包、清空
        if (this.elements.exportChatBtn) {
            this.elements.exportChatBtn.addEventListener('click', () => this.exportChatLog());
        }
        if (this.elements.packCodeBtn) {
            this.elements.packCodeBtn.addEventListener('click', () => this.packCodeZip());
        }
        if (this.elements.clearChatBtn) {
            this.elements.clearChatBtn.addEventListener('click', () => this.clearChatWithConfirm());
        }

        // 预览
        if (this.elements.refreshPreviewBtn) {
            this.elements.refreshPreviewBtn.addEventListener('click', () => this.updatePreview());
        }
        if (this.elements.openNewWindowBtn) {
            this.elements.openNewWindowBtn.addEventListener('click', () => this.openPreviewWindow());
        }
        if (this.elements.autoRefreshCheck) {
            this.elements.autoRefreshCheck.addEventListener('change', (e) => {
                this.autoRefresh = e.target.checked;
            });
        }
    }

    // 模板加载
    loadTemplate(type) {
        if (this.elements.userInput) {
            this.elements.userInput.value = TEMPLATES[type] || '';
        }
    }

    setDiscussionPreset(rounds) {
        this.discussionTotal = rounds;
        if (this.elements.discussionRoundsSlider) this.elements.discussionRoundsSlider.value = rounds;
        if (this.elements.discussionRoundsDisplay) this.elements.discussionRoundsDisplay.textContent = rounds;
        localStorage.setItem('discussionRounds', rounds);
        this.updateDiscussionProgress();
    }

    setProductionPreset(rounds) {
        this.productionTotal = rounds;
        if (this.elements.productionRoundsSlider) this.elements.productionRoundsSlider.value = rounds;
        if (this.elements.productionRoundsDisplay) this.elements.productionRoundsDisplay.textContent = rounds;
        localStorage.setItem('productionRounds', rounds);
        this.updateProductionProgress();
    }

    // ---------- 火山API调用 ----------
    async callModel(modelId, messages, temperature = this.temperature, maxTokens = this.maxTokens) {
        if (!this.apiKey || !this.endpoint || !modelId) {
            throw new Error('请填写完整的API配置');
        }

        const payload = {
            model: modelId,
            messages: messages,
            temperature: temperature,
            max_tokens: maxTokens,
            stream: false
        };

        try {
            const response = await fetch(this.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const err = await response.text();
                throw new Error(`API错误 ${response.status}: ${err.slice(0, 100)}`);
            }

            const data = await response.json();
            const usage = data.usage || { total_tokens: 0 };
            this.lastTokenUsage = usage.total_tokens || 0;
            this.totalTokens += this.lastTokenUsage;
            this.updateStats();

            return {
                content: data.choices[0].message.content,
                token: this.lastTokenUsage
            };
        } catch (e) {
            console.error('火山调用失败', e);
            throw e;
        }
    }

    // ---------- 单轮模式 ----------
    async handleSingleRound() {
        if (!this.elements.userInput) return;
        const userMsg = this.elements.userInput.value.trim();
        if (!userMsg) return;

        if (this.discussionActive || this.productionActive) {
            alert('请先停止当前讨论或制作');
            return;
        }

        appendMessage('user', userMsg);
        this.conversationHistory.push({ role: 'user', content: userMsg, time: new Date().toLocaleString() });

        if (this.elements.sendBtn) {
            this.elements.sendBtn.disabled = true;
            this.elements.sendBtn.innerHTML = '⏳ 调度中...';
        }

        if (this.showThinking) appendThinking('豆包1.8', '拆解需求...');

        try {
            const tasks = await this.dispatchTask(userMsg);
            if (this.showThinking) {
                removeThinking();
                appendThinking('豆包1.8', `调度完成: DS:${tasks.deepseek_task ? '有' : '无'}, GLM:${tasks.glm_task ? '有' : '无'}`);
            }

            const [dsResult, glmResult] = await Promise.all([
                this.callDeepSeek(tasks.deepseek_task),
                this.callGLM(tasks.glm_task)
            ]);

            if (this.showThinking) {
                removeThinking();
                appendThinking('豆包1.8', '整合清洗代码...');
            }

            const integrateResult = await this.integrate(dsResult.content, glmResult.content, userMsg);
            removeThinking();

            appendMessage('assistant', integrateResult.content, integrateResult.token);
            this.conversationHistory.push({
                role: '豆包1.8',
                content: integrateResult.content,
                token: integrateResult.token,
                time: new Date().toLocaleString()
            });

            this.updatePreviewFromContent(integrateResult.content);
        } catch (error) {
            removeThinking();
            appendMessage('assistant', `❌ 单轮失败: ${error.message}`, 0);
        } finally {
            if (this.elements.sendBtn) {
                this.elements.sendBtn.disabled = false;
                this.elements.sendBtn.innerHTML = '🚀 发送单轮';
            }
            if (this.elements.userInput) {
                this.elements.userInput.value = '';
                this.elements.userInput.style.height = 'auto';
            }
            this.updateStats();
        }
    }

    async dispatchTask(userMessage, extraContext = '') {
        const systemPrompt = `${DOUBAO_ROLE_PROMPT}\n你现在是豆包1.8，严格遵循以上角色。用户的最新需求如下："""${userMessage}"""\n${extraContext}\n请根据需求判断需要调用哪个底层模型：- 如果涉及逻辑、后端、函数、算法、硬核代码→ 派发给 DeepSeek V3.2- 如果涉及界面、样式、交互、暗黑模式、美化、排版→ 派发给 GLM-4.7你必须以纯净JSON格式输出调度指令，不要任何额外解释。格式：{"deepseek_task":"...","glm_task":"..."}`;
        const messages = [{ role: "system", content: systemPrompt }, { role: "user", content: userMessage }];
        const result = await this.callModel(this.modelDoubao, messages, 0.3, 6000);
        const jsonMatch = result.content.match(/\{[\s\S]*\}/);
        if (jsonMatch) return JSON.parse(jsonMatch[0]);
        throw new Error('豆包调度返回非JSON格式');
    }

    async callDeepSeek(task) {
        if (!task || task.trim() === '') return { content: '', token: 0 };
        const messages = [{ role: "system", content: DEEPSEEK_ROLE_PROMPT }, { role: "user", content: task }];
        this.dsCalls++;
        this.updateStats();
        return await this.callModel(this.modelDeepseek, messages, this.temperature, this.maxTokens);
    }

    async callGLM(task) {
        if (!task || task.trim() === '') return { content: '', token: 0 };
        const messages = [{ role: "system", content: GLM_ROLE_PROMPT }, { role: "user", content: task }];
        this.glmCalls++;
        this.updateStats();
        return await this.callModel(this.modelGLM, messages, this.temperature, this.maxTokens);
    }

    async integrate(dsOutput, glmOutput, userMsg) {
        let combineContent = `用户原始需求：${userMsg}\n\n`;
        if (dsOutput) combineContent += `【DeepSeek V3.2 输出的逻辑/代码】:\n${dsOutput}\n\n`;
        if (glmOutput) combineContent += `【GLM-4.7 输出的界面/样式】:\n${glmOutput}\n\n`;
        combineContent += `请你豆包1.8 严格按角色定义：只做整合、排版、合并，并按照文件标记格式输出。输出最终可直接使用的完整代码方案，务必使用 === filename: ... === 标记文件。`;
        const systemPrompt = `${DOUBAO_ROLE_PROMPT}\n你现在是豆包1.8，负责最后出口。只做排版整理合并，必须使用文件标记格式。`;
        const messages = [{ role: "system", content: systemPrompt }, { role: "user", content: combineContent }];
        return await this.callModel(this.modelDoubao, messages, 0.3, 6000);
    }
    // ---------- 讨论阶段 ----------
    async startDiscussion() {
        if (!this.elements.userInput) return;
        const topic = this.elements.userInput.value.trim();
        if (!topic) { alert('请输入讨论主题'); return; }
        if (this.discussionActive || this.productionActive) this.stopAll();

        this.projectCore = topic;
        this.phase = 'discussion';
        this.discussionActive = true;
        this.discussionPaused = false;
        this.discussionAbort = false;
        this.discussionCurrent = 0;
        this.discussionHistory = [];

        // 更新UI
        if (this.elements.startDiscussionBtn) this.elements.startDiscussionBtn.disabled = true;
        if (this.elements.pauseDiscussionBtn) {
            this.elements.pauseDiscussionBtn.disabled = false;
            this.elements.pauseDiscussionBtn.textContent = '⏸ 暂停';
        }
        if (this.elements.stopDiscussionBtn) this.elements.stopDiscussionBtn.disabled = false;
        updateDiscussionProgress(0, this.discussionTotal, '讨论中');

        appendMessage('user', `【讨论阶段】主题: ${topic}`);
        this.conversationHistory.push({ role: 'user', content: `【讨论】主题: ${topic}`, time: new Date().toLocaleString() });

        try {
            // 第一轮强制由 DeepSeek 发言，确保讨论启动
            const decision = {
                next_speaker: 'deepseek',
                task_description: `请根据项目核心「${topic}」提出技术方案、难点和初步分工建议。`
            };
            if (this.showThinking) appendThinking('豆包1.8', '分析主题，引导讨论...');
            await this.sleep(500);
            this.removeThinking();
            await this.runDiscussion(decision);
        } catch (error) {
            removeThinking();
            appendMessage('assistant', `❌ 讨论启动失败: ${error.message}`, 0);
            this.resetDiscussionUI();
        }
    }

    async runDiscussion(firstDecision) {
        let currentDecision = firstDecision;
        let round = 0;

        while (round < this.discussionTotal && this.discussionActive && !this.discussionAbort) {
            while (this.discussionPaused && !this.discussionAbort) await this.sleep(300);
            if (this.discussionAbort) break;

            round++;
            this.discussionCurrent = round;
            updateDiscussionProgress(round, this.discussionTotal, '讨论中');

            const speaker = currentDecision.next_speaker; // deepseek, glm, 或 doubao
            const taskDesc = currentDecision.task_description;

            // 显示调度消息
            appendDiscussionDispatch(speaker, taskDesc, round);
            if (this.showThinking) appendThinking(speaker === 'deepseek' ? 'DeepSeek' : (speaker === 'glm' ? 'GLM' : '豆包'), `第${round}轮讨论发言...`);

            try {
                let result;
                if (speaker === 'deepseek') {
                    result = await this.callDeepSeekDiscuss(taskDesc);
                } else if (speaker === 'glm') {
                    result = await this.callGLMDiscuss(taskDesc);
                } else {
                    result = await this.callDoubaoDiscuss(taskDesc);
                }
                removeThinking();

                // 显示讨论发言
                appendDiscussionMessage(speaker, result.content, round);
                this.discussionHistory.push({
                    round: round,
                    speaker: speaker,
                    task: taskDesc,
                    output: result.content,
                    token: result.token
                });

                // 准备下一轮调度（如果不是最后一轮）
                if (round < this.discussionTotal) {
                    if (this.showThinking) appendThinking('豆包1.8', `第${round}轮讨论结束，决定下一轮发言者...`);
                    const contextSummary = await this.generateDiscussionSummary();
                    const nextDecision = await this.dispatchDiscussionRound(contextSummary, round);
                    removeThinking();
                    currentDecision = nextDecision;
                }
            } catch (error) {
                removeThinking();
                appendMessage('assistant', `❌ 第${round}轮讨论失败: ${error.message}`, 0);
                this.stopDiscussion();
                break;
            }
            await this.sleep(500);
        }

        if (!this.discussionAbort && this.discussionCurrent === this.discussionTotal) {
            // 讨论结束，生成共识总结
            updateDiscussionProgress(this.discussionTotal, this.discussionTotal, '生成共识...');
            if (this.showThinking) appendThinking('豆包1.8', '所有轮次完成，整合讨论共识...');
            try {
                const consensus = await this.generateConsensus();
                removeThinking();
                appendMessage('assistant', `【讨论共识】\n${consensus.content}`, consensus.token);
                this.conversationHistory.push({
                    role: '豆包1.8',
                    content: `【讨论共识】\n${consensus.content}`,
                    token: consensus.token,
                    time: new Date().toLocaleString()
                });
                // 尝试解析共识中的JSON
                this.consensusJSON = this.parseConsensus(consensus.content);
                updateDiscussionProgress(this.discussionTotal, this.discussionTotal, '讨论完成');
            } catch (e) {
                removeThinking();
                appendMessage('assistant', `❌ 共识生成失败: ${e.message}`, 0);
            }
        }
        this.resetDiscussionUI();
    }

    // 解析共识中的JSON
    parseConsensus(text) {
        try {
            const jsonMatch = text.match(/\{[\s\S]*\}/);
            if (jsonMatch) return JSON.parse(jsonMatch[0]);
        } catch (e) {}
        return {};
    }

    async dispatchDiscussionRound(contextSummary, currentRound) {
        const systemPrompt = `你是一个讨论主持人。当前项目核心：${this.projectCore}\n基于以下讨论历史摘要，决定下一轮由谁发言（可以是豆包、DeepSeek 或 GLM），并给出具体的讨论话题。讨论应该围绕项目需求、技术方案、设计思路、分工等展开。尽量让每个参与者都有发言机会。\n历史摘要：\n${contextSummary}\n输出格式必须是纯净JSON：{"next_speaker":"doubao/deepseek/glm","task_description":"..."}`;
        const messages = [{ role: "system", content: systemPrompt }, { role: "user", content: "请根据以上历史摘要，决定下一轮发言者。" }];
        const result = await this.callModel(this.modelDoubao, messages, 0.3, 6000);
        const jsonMatch = result.content.match(/\{[\s\S]*\}/);
        if (jsonMatch) return JSON.parse(jsonMatch[0]);
        throw new Error('豆包讨论调度返回非JSON格式');
    }

    async callDeepSeekDiscuss(task) {
        const messages = [{ role: "system", content: DEEPSEEK_DISCUSS_PROMPT }, { role: "user", content: task }];
        this.dsCalls++;
        this.updateStats();
        return await this.callModel(this.modelDeepseek, messages, this.temperature, this.maxTokens);
    }

    async callGLMDiscuss(task) {
        const messages = [{ role: "system", content: GLM_DISCUSS_PROMPT }, { role: "user", content: task }];
        this.glmCalls++;
        this.updateStats();
        return await this.callModel(this.modelGLM, messages, this.temperature, this.maxTokens);
    }

    async callDoubaoDiscuss(task) {
        const messages = [{ role: "system", content: DOUBAO_DISCUSS_PROMPT }, { role: "user", content: task }];
        return await this.callModel(this.modelDoubao, messages, this.temperature, 6000);
    }

    async generateDiscussionSummary() {
        let historyText = `项目核心：${this.projectCore}\n\n`;
        if (this.discussionHistory.length === 0) return historyText + '暂无讨论历史。';
        const recent = this.discussionHistory.slice(-3);
        historyText += `已进行 ${this.discussionCurrent}/${this.discussionTotal} 轮讨论。\n最近讨论摘要：\n`;
        recent.forEach(h => {
            const name = h.speaker === 'deepseek' ? 'DeepSeek' : (h.speaker === 'glm' ? 'GLM' : '豆包');
            const brief = h.output.substring(0, 150) + (h.output.length > 150 ? '...' : '');
            historyText += `第${h.round}轮 ${name}：${brief}\n`;
        });
        const limit = this.summaryWordLimit;
        const prompt = `请将以下讨论历史压缩成一段精简的摘要（${limit}字以内），用于下一轮讨论的上下文：\n\n${historyText}`;
        const messages = [{ role: "system", content: "你是一个摘要专家，只输出精简摘要，不要任何额外内容。" }, { role: "user", content: prompt }];
        try {
            const result = await this.callModel(this.modelDoubao, messages, 0.3, 6000);
            return result.content.trim();
        } catch (e) {
            return `项目核心：${this.projectCore}，当前第${this.discussionCurrent}轮，最近发言：${recent[recent.length-1]?.output.substring(0,50)}...`;
        }
    }

    async generateConsensus() {
        let historyFull = '';
        this.discussionHistory.forEach(h => {
            const name = h.speaker === 'deepseek' ? 'DeepSeek' : (h.speaker === 'glm' ? 'GLM' : '豆包');
            historyFull += `第${h.round}轮 ${name}：\n${h.output}\n\n`;
        });
        const prompt = `项目核心：${this.projectCore}\n\n以下是完整的讨论历史：\n${historyFull}\n\n请根据以上讨论，生成一份共识总结，包含：1. 对项目的共同理解；2. 达成的技术/设计方向；3. 初步分工建议；4. 下一步制作阶段的注意事项。用中文，并输出一份JSON格式的简洁摘要，放在末尾，格式：{"project":"...","tech_stack":"...","division":"...","constraints":"...","keywords":[...]}`;
        const messages = [{ role: "system", content: "你是一个项目协调员，负责总结讨论成果。" }, { role: "user", content: prompt }];
        return await this.callModel(this.modelDoubao, messages, 0.3, 6000);
    }

    pauseDiscussion() {
        if (!this.discussionActive) return;
        this.discussionPaused = !this.discussionPaused;
        if (this.elements.pauseDiscussionBtn) {
            this.elements.pauseDiscussionBtn.textContent = this.discussionPaused ? '▶ 继续' : '⏸ 暂停';
        }
        updateDiscussionProgress(this.discussionCurrent, this.discussionTotal, this.discussionPaused ? '已暂停' : '讨论中');
    }

    stopDiscussion() {
        this.discussionAbort = true;
        this.discussionActive = false;
        this.resetDiscussionUI();
        appendMessage('assistant', '⏹️ 讨论已停止', 0);
    }

    resetDiscussionUI() {
        this.discussionActive = false;
        this.discussionPaused = false;
        if (this.elements.startDiscussionBtn) this.elements.startDiscussionBtn.disabled = false;
        if (this.elements.pauseDiscussionBtn) {
            this.elements.pauseDiscussionBtn.disabled = true;
            this.elements.pauseDiscussionBtn.textContent = '⏸ 暂停';
        }
        if (this.elements.stopDiscussionBtn) this.elements.stopDiscussionBtn.disabled = true;
        updateDiscussionProgress(0, this.discussionTotal, '空闲');
    }

    // ---------- 制作阶段 ----------
    async startProduction() {
        if (!this.projectCore) {
            alert('请先完成讨论阶段，输入项目主题');
            return;
        }
        if (this.discussionActive || this.productionActive) this.stopAll();

        this.phase = 'production';
        this.productionActive = true;
        this.productionPaused = false;
        this.productionAbort = false;
        this.productionCurrent = 0;
        this.productionHistory = [];

        // 更新UI
        if (this.elements.startProductionBtn) this.elements.startProductionBtn.disabled = true;
        if (this.elements.pauseProductionBtn) {
            this.elements.pauseProductionBtn.disabled = false;
            this.elements.pauseProductionBtn.textContent = '⏸ 暂停';
        }
        if (this.elements.stopProductionBtn) this.elements.stopProductionBtn.disabled = false;
        updateProductionProgress(0, this.productionTotal, '制作中');

        appendMessage('user', `【制作阶段】项目核心: ${this.projectCore}`);
        this.conversationHistory.push({ role: 'user', content: `【制作】核心: ${this.projectCore}`, time: new Date().toLocaleString() });

        try {
            const context = `项目核心：${this.projectCore}\n讨论共识：${JSON.stringify(this.consensusJSON)}`;
            if (this.showThinking) appendThinking('豆包1.8', '分析项目，决定第一轮制作任务...');
            const decision = await this.dispatchProductionRound(context);
            removeThinking();
            await this.runProduction(decision);
        } catch (error) {
            removeThinking();
            appendMessage('assistant', `❌ 制作启动失败: ${error.message}`, 0);
            this.resetProductionUI();
        }
    }

    async runProduction(firstDecision) {
        let currentDecision = firstDecision;
        let round = 0;

        while (round < this.productionTotal && this.productionActive && !this.productionAbort) {
            // 检查插队指令
            if (this.interruptQueue.length > 0) {
                const cmd = this.interruptQueue.shift();
                await this.handleInterrupt(cmd);
                // 可能需要更新 currentDecision
            }

            while (this.productionPaused && !this.productionAbort) await this.sleep(300);
            if (this.productionAbort) break;

            round++;
            this.productionCurrent = round;
            updateProductionProgress(round, this.productionTotal, '制作中');

            const speaker = currentDecision.next_speaker;
            const taskDesc = currentDecision.task_description;

            // 显示调度消息
            appendDispatchMessage(speaker, taskDesc, round);
            if (this.showThinking) appendThinking(speaker === 'deepseek' ? 'DeepSeek V3.2' : 'GLM-4.7', `第${round}轮执行任务...`);

            try {
                let result;
                if (speaker === 'deepseek') {
                    result = await this.callDeepSeek(taskDesc);
                } else {
                    result = await this.callGLM(taskDesc);
                }
                removeThinking();

                // 显示模型输出
                appendModelMessage(speaker, result.content, round);
                this.productionHistory.push({
                    round: round,
                    speaker: speaker,
                    task: taskDesc,
                    output: result.content,
                    token: result.token
                });

                // 如果开启了自动刷新且GLM输出包含index.html，则预览更新
                if (this.autoRefresh && speaker === 'glm' && result.content.includes('index.html')) {
                    this.updatePreviewFromContent(result.content);
                }

                if (round < this.productionTotal) {
                    if (this.showThinking) appendThinking('豆包1.8', `第${round}轮完成，摘要历史，决定下一轮...`);
                    const contextSummary = await this.generateProductionSummary();
                    const nextDecision = await this.dispatchProductionRound(contextSummary);
                    removeThinking();
                    currentDecision = nextDecision;
                }
            } catch (error) {
                removeThinking();
                appendMessage('assistant', `❌ 第${round}轮制作失败: ${error.message}`, 0);
                this.stopProduction();
                break;
            }
            await this.sleep(500);
        }

        if (!this.productionAbort && this.productionCurrent === this.productionTotal) {
            // 制作完成，整合最终代码
            updateProductionProgress(this.productionTotal, this.productionTotal, '生成成品中...');
            if (this.showThinking) appendThinking('豆包1.8', '所有轮次完成，整合最终代码方案...');
            try {
                const finalCode = await this.integrateProduction();
                removeThinking();
                appendMessage('assistant', finalCode.content, finalCode.token);
                this.conversationHistory.push({
                    role: '豆包1.8',
                    content: finalCode.content,
                    token: finalCode.token,
                    time: new Date().toLocaleString()
                });
                this.updatePreviewFromContent(finalCode.content);
                updateProductionProgress(this.productionTotal, this.productionTotal, '制作完成');
            } catch (e) {
                removeThinking();
                appendMessage('assistant', `❌ 最终整合失败: ${e.message}`, 0);
            }
        }
        this.resetProductionUI();
    }
    async handleInterrupt(cmd) {
        // 显示用户插队指令
        appendMessage('user', `【插队指令】${cmd}`);

        // 让豆包理解新指令并更新调度
        const prompt = `用户插队指令：${cmd}。请根据当前项目核心和讨论共识，更新调度策略。输出下一轮发言者和任务，格式：{"next_speaker":"deepseek/glm","task_description":"..."}`;
        const messages = [
            { role: "system", content: "你是一个调度器，需要根据插队指令调整后续任务。" },
            { role: "user", content: prompt }
        ];

        try {
            const result = await this.callModel(this.modelDoubao, messages, 0.3, 6000);
            const jsonMatch = result.content.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                // 将新的决策作为下一轮的 currentDecision（通过一个临时变量）
                this.interruptDecision = JSON.parse(jsonMatch[0]);
                // 暂停一下让调度循环有机会处理
                this.productionPaused = false; // 确保不卡死
            }
        } catch (e) {
            console.error('插队处理失败', e);
            appendMessage('assistant', `⚠️ 插队指令处理失败: ${e.message}`, 0);
        }
    }

    async dispatchProductionRound(contextSummary) {
        // 获取上一轮的发言者（如果有）
        let lastSpeaker = '';
        if (this.productionHistory.length > 0) {
            lastSpeaker = this.productionHistory[this.productionHistory.length - 1].speaker;
        }
        const lastSpeakerHint = lastSpeaker ? `上一轮发言者是 ${lastSpeaker === 'deepseek' ? 'DeepSeek' : 'GLM'}。` : '这是第一轮。';

        // 添加当前轮次信息
        const roundInfo = `当前是制作阶段第 ${this.productionCurrent + 1} 轮 / 总共 ${this.productionTotal} 轮。还剩 ${this.productionTotal - this.productionCurrent - 1} 轮。`;

        const systemPrompt = `${DOUBAO_ROLE_PROMPT}

你现在是豆包1.8，负责多轮制作的调度。你需要根据项目核心、讨论共识和制作历史，决定下一轮由谁发言（DeepSeek V3.2 或 GLM-4.7），并生成具体的任务指令。

${roundInfo}

【项目核心】
${this.projectCore}

【讨论共识】
${JSON.stringify(this.consensusJSON)}

${lastSpeakerHint}
请尽量交替指派。如果剩余轮数较少（例如最后2轮），可以要求模型输出最终版本代码，并确保所有文件按目录结构输出。

当前摘要：
${contextSummary}

输出格式必须是纯净JSON：
{
  "next_speaker": "deepseek 或 glm",
  "task_description": "给该模型的具体任务，必须清晰、自包含，并在开头简要提及项目背景。如果剩余轮数很少，任务应包含「请输出最终版本，确保所有文件完整，并在文件开头注明文件名」。"
}`;

        const messages = [
            { role: "system", content: systemPrompt },
            { role: "user", content: "请根据以上摘要，决定下一轮调度。" }
        ];

        const result = await this.callModel(this.modelDoubao, messages, 0.3, 6000);
        const jsonMatch = result.content.match(/\{[\s\S]*\}/);
        if (jsonMatch) return JSON.parse(jsonMatch[0]);
        throw new Error('豆包制作调度返回非JSON格式');
    }

    async generateProductionSummary() {
        let historyText = `项目核心：${this.projectCore}\n讨论共识：${JSON.stringify(this.consensusJSON)}\n\n`;
        if (this.productionHistory.length === 0) return historyText + '暂无制作历史。';
        const recent = this.productionHistory.slice(-3);
        historyText += `已进行 ${this.productionCurrent}/${this.productionTotal} 轮制作。\n最近制作摘要：\n`;
        recent.forEach(h => {
            const name = h.speaker === 'deepseek' ? 'DeepSeek' : 'GLM';
            const brief = h.output.substring(0, 150) + (h.output.length > 150 ? '...' : '');
            historyText += `第${h.round}轮 ${name}：${brief}\n`;
        });
        const limit = this.summaryWordLimit;
        const prompt = `请将以下制作历史压缩成一段精简的摘要（${limit}字以内），用于下一轮调度的上下文：\n\n${historyText}`;
        const messages = [
            { role: "system", content: "你是一个摘要专家，只输出精简摘要，不要任何额外内容。" },
            { role: "user", content: prompt }
        ];
        try {
            const result = await this.callModel(this.modelDoubao, messages, 0.3, 6000);
            return result.content.trim();
        } catch (e) {
            return `项目核心：${this.projectCore}，当前第${this.productionCurrent}轮，最近产出：${recent[recent.length-1]?.output.substring(0,50)}...`;
        }
    }

    async integrateProduction() {
        // 让豆包根据所有制作历史整合最终代码
        let historyFull = '';
        this.productionHistory.forEach(h => {
            const name = h.speaker === 'deepseek' ? 'DeepSeek' : 'GLM';
            historyFull += `第${h.round}轮 ${name}：\n${h.output}\n\n`;
        });

        const prompt = `项目核心：${this.projectCore}\n讨论共识：${JSON.stringify(this.consensusJSON)}\n\n以下是制作过程中输出的所有代码：\n${historyFull}\n\n请你豆包1.8整合最终代码方案。必须使用 === filename: ... === 标记文件，并按项目目录结构组织（如 index.html, css/style.css, js/script.js, backend/app.js 等）。输出可直接运行的完整代码。`;

        const messages = [
            { role: "system", content: DOUBAO_ROLE_PROMPT },
            { role: "user", content: prompt }
        ];
        return await this.callModel(this.modelDoubao, messages, 0.3, 6000);
    }

    pauseProduction() {
        if (!this.productionActive) return;
        this.productionPaused = !this.productionPaused;
        if (this.elements.pauseProductionBtn) {
            this.elements.pauseProductionBtn.textContent = this.productionPaused ? '▶ 继续' : '⏸ 暂停';
        }
        updateProductionProgress(this.productionCurrent, this.productionTotal, this.productionPaused ? '已暂停' : '制作中');
    }

    stopProduction() {
        this.productionAbort = true;
        this.productionActive = false;
        this.resetProductionUI();
        appendMessage('assistant', '⏹️ 制作已停止', 0);
    }

    resetProductionUI() {
        this.productionActive = false;
        this.productionPaused = false;
        if (this.elements.startProductionBtn) this.elements.startProductionBtn.disabled = false;
        if (this.elements.pauseProductionBtn) {
            this.elements.pauseProductionBtn.disabled = true;
            this.elements.pauseProductionBtn.textContent = '⏸ 暂停';
        }
        if (this.elements.stopProductionBtn) this.elements.stopProductionBtn.disabled = true;
        updateProductionProgress(0, this.productionTotal, '空闲');
    }

    stopAll() {
        if (this.discussionActive) this.stopDiscussion();
        if (this.productionActive) this.stopProduction();
    }

    // 插队指令发送
    sendInterruptCommand() {
        if (!this.elements.interruptInput) return;
        const cmd = this.elements.interruptInput.value.trim();
        if (!cmd) return;
        this.interruptQueue.push(cmd);
        this.elements.interruptInput.value = '';
        appendMessage('user', `【插队指令已加入队列】${cmd}`);
    }

    // ---------- 打包代码 ----------
    packCodeZip() {
        const files = {};

        // 遍历整个对话历史，收集所有文件标记
        for (let i = 0; i < this.conversationHistory.length; i++) {
            const entry = this.conversationHistory[i];
            if (entry.role === '豆包1.8' && entry.content && entry.content.includes('=== filename:')) {
                const fileRegex = /=== filename: (.+?) ===\n([\s\S]*?)(?=\n=== filename:|$)/g;
                let match;
                while ((match = fileRegex.exec(entry.content)) !== null) {
                    const fileName = match[1].trim();
                    const fileContent = match[2].trim();
                    // 后面的版本覆盖前面的，确保最新
                    files[fileName] = fileContent;
                }
            }
        }

        if (Object.keys(files).length === 0) {
            alert('未找到任何文件标记，请确保豆包已输出文件。');
            return;
        }

        const zip = new JSZip();

        // 按文件名中的路径直接存储
        Object.entries(files).forEach(([fileName, content]) => {
            zip.file(fileName, content);
        });

        zip.generateAsync({ type: 'blob' }).then(blob => {
            saveAs(blob, `三AI项目_${new Date().toISOString().slice(0,10)}.zip`);
        });
    }

    // ---------- 导出聊天记录 ----------
    exportChatLog() {
        if (this.conversationHistory.length === 0) {
            alert('暂无聊天记录');
            return;
        }
        let text = '';
        this.conversationHistory.forEach(entry => {
            text += `[${entry.time}] ${entry.role}:\n${entry.content}\n\n`;
        });
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const date = new Date().toISOString().slice(0,10);
        saveAs(blob, `三AI_调度记录_${date}.txt`);
    }

    // ---------- 清空对话带确认 ----------
    clearChatWithConfirm() {
        if (confirm('⚠️ 确定清空所有对话历史？此操作不可恢复。')) {
            if (this.elements.chatMessages) {
                this.elements.chatMessages.innerHTML = '';
            }
            this.conversationHistory = [];
            this.currentPreviewHtml = '';
            if (this.elements.previewContainer) {
                this.elements.previewContainer.innerHTML = '<div class="preview-placeholder">⚡ 等待豆包输出 index.html ...</div>';
            }
            // 重新添加欢迎语
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'message assistant';
            welcomeDiv.innerHTML = `
                <div class="bubble">
                    🧠 <strong>豆包1.8 · 三AI调度官</strong><br>
                    - 讨论阶段：三个模型轮流发言，形成共识<br>
                    - 制作阶段：调度DeepSeek/GLM输出代码，可插队<br>
                    - 打包按目录自动分类<br>
                    <span style="color:#9ec3ff;">⸻ 指挥官，请指示 ⸻</span>
                </div>
                <div class="message-meta">豆包1.8 • 上下文管家</div>
            `;
            if (this.elements.chatMessages) {
                this.elements.chatMessages.appendChild(welcomeDiv);
            }
            this.totalTokens = 0;
            this.dsCalls = 0;
            this.glmCalls = 0;
            this.updateStats();
        }
    }

    // ---------- 预览 ----------
    updatePreviewFromContent(content) {
        if (!content) return;

        const regex = /=== filename: index\.html ===\n([\s\S]*?)(?=\n=== filename:|$)/i;
        const match = content.match(regex);
        let htmlContent = '';

        if (match && match[1]) {
            htmlContent = match[1].trim();
        } else {
            const htmlMatch = content.match(/<!DOCTYPE[\s\S]*?<\/html>/i);
            if (htmlMatch) {
                htmlContent = htmlMatch[0];
            }
        }

        if (htmlContent) {
            this.currentPreviewHtml = htmlContent;
            this.renderPreview(htmlContent);
        }
    }

    renderPreview(htmlString) {
        if (!this.elements.previewContainer) return;
        this.elements.previewContainer.innerHTML = '';
        const iframe = document.createElement('iframe');
        iframe.sandbox = 'allow-scripts allow-same-origin allow-forms allow-popups allow-downloads allow-modals';
        iframe.style.width = '100%';
        iframe.style.height = '100%';
        iframe.style.border = 'none';
        iframe.style.background = 'white';
        iframe.srcdoc = htmlString;
        this.elements.previewContainer.appendChild(iframe);
    }

    updatePreview() {
        if (this.currentPreviewHtml) {
            this.renderPreview(this.currentPreviewHtml);
        } else {
            alert('暂无预览内容，请先让豆包输出 index.html');
        }
    }

    openPreviewWindow() {
        if (!this.currentPreviewHtml) {
            alert('暂无预览内容，请先让豆包输出 index.html');
            return;
        }
        const blob = new Blob([this.currentPreviewHtml], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }

    // ---------- 统计和进度更新 ----------
    updateStats() {
        updateTopStats(this.totalTokens, this.dsCalls, this.glmCalls);
        if (this.elements.topRound) {
            if (this.productionActive) {
                this.elements.topRound.textContent = `${this.productionCurrent}/${this.productionTotal}`;
            } else if (this.discussionActive) {
                this.elements.topRound.textContent = `${this.discussionCurrent}/${this.discussionTotal}`;
            } else {
                this.elements.topRound.textContent = `0/0`;
            }
        }
    }

    updateAllUI() {
        this.updateStats();
        this.updateDiscussionProgress();
        this.updateProductionProgress();
    }

    updateDiscussionProgress() {
        updateDiscussionProgress(this.discussionCurrent, this.discussionTotal,
            this.discussionActive ? (this.discussionPaused ? '已暂停' : '讨论中') : '空闲');
    }

    updateProductionProgress() {
        updateProductionProgress(this.productionCurrent, this.productionTotal,
            this.productionActive ? (this.productionPaused ? '已暂停' : '制作中') : '空闲');
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
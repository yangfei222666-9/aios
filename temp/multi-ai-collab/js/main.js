// ==================== 全局入口 ====================
let engine;

window.onload = function() {
    // 创建引擎实例
    engine = new TripleAIEngine();

    // 绑定所有需要操作的DOM元素
    engine.bindElements({
        // 顶部统计
        topRound: document.getElementById('topRound'),
        topTokens: document.getElementById('topTokens'),
        topDs: document.getElementById('topDs'),
        topGlm: document.getElementById('topGlm'),

        // API配置
        apiKey: document.getElementById('apiKey'),
        apiEndpoint: document.getElementById('apiEndpoint'),
        modelDoubao: document.getElementById('modelDoubao'),
        modelDeepseek: document.getElementById('modelDeepseek'),
        modelGLM: document.getElementById('modelGLM'),

        // 输入区
        userInput: document.getElementById('userInput'),
        sendBtn: document.getElementById('sendBtn'),
        chatMessages: document.getElementById('chatMessages'),

        // 滑块
        temperatureSlider: document.getElementById('temperatureSlider'),
        tempDisplay: document.getElementById('tempDisplay'),
        maxTokensSlider: document.getElementById('maxTokensSlider'),
        maxTokensDisplay: document.getElementById('maxTokensDisplay'),
        summaryLimitSlider: document.getElementById('summaryLimitSlider'),
        summaryLimitDisplay: document.getElementById('summaryLimitDisplay'),
        showThinking: document.getElementById('showThinking'),

        // 讨论控制
        discussionRoundsSlider: document.getElementById('discussionRoundsSlider'),
        discussionRoundsDisplay: document.getElementById('discussionRoundsDisplay'),
        discussionProgressRing: document.getElementById('discussionProgressRing'),
        discussionStatus: document.getElementById('discussionStatus'),
        discussionTimeRemaining: document.getElementById('discussionTimeRemaining'),
        startDiscussionBtn: document.getElementById('startDiscussionBtn'),
        pauseDiscussionBtn: document.getElementById('pauseDiscussionBtn'),
        stopDiscussionBtn: document.getElementById('stopDiscussionBtn'),

        // 制作控制
        productionRoundsSlider: document.getElementById('productionRoundsSlider'),
        productionRoundsDisplay: document.getElementById('productionRoundsDisplay'),
        productionProgressRing: document.getElementById('productionProgressRing'),
        productionStatus: document.getElementById('productionStatus'),
        productionTimeRemaining: document.getElementById('productionTimeRemaining'),
        startProductionBtn: document.getElementById('startProductionBtn'),
        pauseProductionBtn: document.getElementById('pauseProductionBtn'),
        stopProductionBtn: document.getElementById('stopProductionBtn'),

        // 插队
        interruptInput: document.getElementById('interruptInput'),
        sendInterrupt: document.getElementById('sendInterrupt'),

        // 持久化按钮
        exportChatBtn: document.getElementById('exportChatBtn'),
        packCodeBtn: document.getElementById('packCodeBtn'),
        clearChatBtn: document.getElementById('clearChatBtn'),

        // 预览
        refreshPreviewBtn: document.getElementById('refreshPreviewBtn'),
        openNewWindowBtn: document.getElementById('openNewWindowBtn'),
        autoRefreshCheck: document.getElementById('autoRefreshPreview'),
        previewContainer: document.getElementById('previewContainer'),
    });

    // 加载本地设置
    engine.loadSettings();

    // 绑定事件监听
    engine.attachEvents();

    // 初始化UI（如填充统计、进度等）
    engine.updateAllUI();

    // 模板按钮绑定（因为onclick属性已经写在HTML中，但需要在engine实例上调用）
    window.engine = engine; // 使全局可用
};
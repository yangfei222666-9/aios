// ==================== UI 辅助方法 ====================

// 显示消息（用户或豆包）
function appendMessage(role, content, tokens = 0) {
    const chatMessages = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role === 'user' ? 'user' : 'assistant'}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    let formatted = formatContent(content);
    if (role === 'assistant' && tokens > 0) {
        formatted += `<div style="margin-top:12px; font-size:11px; color:var(--text-dim); border-top:1px solid var(--border); padding-top:8px;">🧾 Token: ${tokens}</div>`;
    }
    bubble.innerHTML = formatted;
    msgDiv.appendChild(bubble);
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    meta.innerHTML = role === 'user' ? '你' : '豆包1.8';
    msgDiv.appendChild(meta);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 显示调度消息（豆包指派）
function appendDispatchMessage(speaker, task, round) {
    const chatMessages = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.style.borderLeftColor = 'var(--accent)';
    bubble.innerHTML = `
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <span style="background:var(--accent); padding:4px 10px; border-radius:16px; font-size:12px; font-weight:600; color:white;">🧠 豆包调度</span>
            <span style="font-size:11px;">第${round}轮</span>
        </div>
        <div>👉 指派 <strong style="color:${speaker==='deepseek'?'var(--ds-color)':'var(--glm-color)'};">${speaker==='deepseek'?'DeepSeek V3.2':'GLM-4.7'}</strong></div>
        <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px;">${formatContent(task)}</div>
    `;
    msgDiv.appendChild(bubble);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 显示模型输出消息（带角色标签）
function appendModelMessage(speaker, content, round) {
    const chatMessages = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message assistant ${speaker === 'deepseek' ? 'message-deepseek' : 'message-glm'}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = `
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <span class="role-tag ${speaker==='deepseek'?'tag-ds':'tag-glm'}">${speaker==='deepseek'?'DeepSeek V3.2':'GLM-4.7'}</span>
            <span style="font-size:11px;">第${round}轮 执行结果</span>
        </div>
        ${formatContent(content)}
    `;
    msgDiv.appendChild(bubble);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 显示讨论阶段的发言
function appendDiscussionMessage(speaker, content, round) {
    const chatMessages = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message assistant ${speaker==='deepseek'?'message-deepseek':(speaker==='glm'?'message-glm':'message-doubao')}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    let speakerShow = speaker === 'deepseek' ? 'DeepSeek V3.2' : (speaker === 'glm' ? 'GLM-4.7' : '豆包1.8');
    bubble.innerHTML = `
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <span class="role-tag ${speaker==='deepseek'?'tag-ds':(speaker==='glm'?'tag-glm':'tag-doubao')}">${speakerShow}</span>
            <span style="font-size:11px;">第${round}轮 讨论发言</span>
        </div>
        ${formatContent(content)}
    `;
    msgDiv.appendChild(bubble);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 显示讨论阶段的调度消息
function appendDiscussionDispatch(speaker, task, round) {
    const chatMessages = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.style.borderLeftColor = 'var(--accent)';
    let speakerShow = speaker === 'deepseek' ? 'DeepSeek V3.2' : (speaker === 'glm' ? 'GLM-4.7' : '豆包1.8');
    bubble.innerHTML = `
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <span style="background:var(--accent); padding:4px 10px; border-radius:16px; font-size:12px; font-weight:600; color:white;">🧠 豆包调度</span>
            <span style="font-size:11px;">第${round}轮讨论</span>
        </div>
        <div>👉 请 <strong>${speakerShow}</strong> 发言</div>
        <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px;">${formatContent(task)}</div>
    `;
    msgDiv.appendChild(bubble);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 显示思考中动画
function appendThinking(speaker, text) {
    const chatMessages = document.getElementById('chatMessages');
    const id = 'thinking-message';
    let el = document.getElementById(id);
    if (!el) {
        el = document.createElement('div');
        el.id = id;
        el.className = 'message assistant';
        el.innerHTML = `
            <div class="bubble" style="background: rgba(204,102,255,0.1);">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="color:var(--accent);">🤔 ${speaker}</span>
                    <span style="font-size:12px; color:var(--text-dim);">${text}</span>
                    <span style="width:6px; height:6px; background:var(--accent); border-radius:50%; animation: blink 1s infinite;"></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(el);
    } else {
        const span = el.querySelector('.bubble div span:nth-child(2)');
        if (span) span.textContent = text;
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeThinking() {
    const el = document.getElementById('thinking-message');
    if (el) el.remove();
}

// 格式化内容（代码块、文件标记）
function formatContent(content) {
    if (!content) return '';
    let escaped = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    escaped = escaped.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang}">${code}</code></pre>`;
    });
    escaped = escaped.replace(/=== filename: (.+?) ===/g, '<div class="file-marker">📄 文件: $1</div>');
    escaped = escaped.replace(/\n/g, '<br>');
    return escaped;
}

// 更新顶部统计
function updateTopStats(totalTokens, dsCalls, glmCalls) {
    const topTokens = document.getElementById('topTokens');
    const topDs = document.getElementById('topDs');
    const topGlm = document.getElementById('topGlm');
    if (topTokens) topTokens.textContent = formatNumber(totalTokens);
    if (topDs) topDs.textContent = dsCalls;
    if (topGlm) topGlm.textContent = glmCalls;
}

function formatNumber(num) {
    if (num >= 1000000) return (num/1000000).toFixed(1)+'M';
    if (num >= 1000) return (num/1000).toFixed(1)+'K';
    return num.toString();
}

// 更新环形进度条
function updateProgressRing(elementId, current, total) {
    const ring = document.getElementById(elementId);
    if (!ring) return;
    ring.textContent = `${current}/${total}`;
    const percent = total > 0 ? (current/total)*360 : 0;
    ring.style.background = `conic-gradient(var(--primary) ${percent}deg, var(--progress-ring-bg) ${percent}deg)`;
}

// 更新讨论进度显示
function updateDiscussionProgress(current, total, status) {
    const progressRing = document.getElementById('discussionProgressRing');
    const statusEl = document.getElementById('discussionStatus');
    const timeRemaining = document.getElementById('discussionTimeRemaining');
    if (progressRing) updateProgressRing('discussionProgressRing', current, total);
    if (statusEl) statusEl.textContent = status || (current === total ? '完成' : (current > 0 ? '讨论中' : '空闲'));
    if (timeRemaining) {
        const remaining = total - current;
        timeRemaining.textContent = remaining > 0 ? `约 ${remaining * 2} 分钟` : '-';
    }
}

// 更新制作进度显示
function updateProductionProgress(current, total, status) {
    const progressRing = document.getElementById('productionProgressRing');
    const statusEl = document.getElementById('productionStatus');
    const timeRemaining = document.getElementById('productionTimeRemaining');
    if (progressRing) updateProgressRing('productionProgressRing', current, total);
    if (statusEl) statusEl.textContent = status || (current === total ? '完成' : (current > 0 ? '制作中' : '空闲'));
    if (timeRemaining) {
        const remaining = total - current;
        timeRemaining.textContent = remaining > 0 ? `约 ${remaining * 3} 分钟` : '-';
    }
}
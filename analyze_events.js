const fs = require('fs');
const path = require('path');

// 读取 events.jsonl
const filePath = path.join(__dirname, 'aios/data/events.jsonl');
const content = fs.readFileSync(filePath, 'utf-8');
const lines = content.trim().split('\n');

// 解析所有事件
const allEvents = lines.map(line => JSON.parse(line));

// 取最后 100 条
const events = allEvents.slice(-100);

console.log(`总事件数: ${allEvents.length}, 分析最后 ${events.length} 条\n`);

// 查看前 100 条事件的分布
const first100 = allEvents.slice(0, 100);
const sourceCounts100 = {};
const errorCounts100 = {};
const durationCounts100 = [];

first100.forEach(event => {
    const source = event.source || 'unknown';
    sourceCounts100[source] = (sourceCounts100[source] || 0) + 1;
    
    const eventType = event.type || '';
    const payload = event.payload || {};
    
    if (eventType.includes('error') || eventType.includes('failed') || payload.error) {
        errorCounts100[eventType] = (errorCounts100[eventType] || 0) + 1;
    }
    
    if (payload.duration_ms !== undefined && payload.duration_ms !== null) {
        durationCounts100.push(payload.duration_ms);
    }
});

console.log('=== 前 100 条事件 Source 分布 ===');
Object.entries(sourceCounts100)
    .sort((a, b) => b[1] - a[1])
    .forEach(([source, count]) => {
        console.log(`${source}: ${count}`);
    });

console.log('\n=== 前 100 条错误类型 ===');
Object.entries(errorCounts100)
    .sort((a, b) => b[1] - a[1])
    .forEach(([type, count]) => {
        console.log(`${type}: ${count}`);
    });

console.log(`\n=== 前 100 条平均耗时 ===`);
const avgDuration100 = durationCounts100.length > 0 
    ? durationCounts100.reduce((a, b) => a + b, 0) / durationCounts100.length 
    : 0;
console.log(`${avgDuration100.toFixed(2)} ms (样本数: ${durationCounts100.length})`);

// 使用前 100 条进行分析
const layerCounts = {
    'KERNEL': 0,
    'COMMS': 0,
    'TOOL': 0,
    'MEM': 0,
    'SEC': 0
};

first100.forEach(event => {
    const source = event.source || '';
    
    if (['pipeline', 'scheduler', 'score_engine', 'agent_system', 'agent_test_agent', 'agent_demo_agent'].includes(source)) {
        layerCounts.KERNEL++;
    }
    else if (source.includes('comms') || source.includes('message')) {
        layerCounts.COMMS++;
    }
    else if (['monitor', 'resource_monitor', 'stress_test', 'threshold_monitor'].includes(source)) {
        layerCounts.TOOL++;
    }
    else if (source.includes('memory') || source.includes('storage')) {
        layerCounts.MEM++;
    }
    else if (['circuit_breaker', 'reactor'].includes(source)) {
        layerCounts.SEC++;
    }
    else {
        layerCounts.KERNEL++;
    }
});

const topErrors = Object.entries(errorCounts100)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

console.log('\n=== 层级统计（前 100 条）===');
Object.entries(layerCounts).forEach(([layer, count]) => {
    console.log(`${layer}: ${count}`);
});

console.log('\n=== Top 3 错误类型 ===');
if (topErrors.length > 0) {
    topErrors.forEach(([errorType, count]) => {
        console.log(`${errorType}: ${count}`);
    });
} else {
    console.log('无错误事件');
}

// 生成报告数据
const reportData = {
    layer_counts: layerCounts,
    top_errors: topErrors,
    avg_duration: avgDuration100,
    duration_samples: durationCounts100.length,
    total_events: first100.length
};

// 保存为 JSON
fs.writeFileSync(
    path.join(__dirname, 'report_data.json'),
    JSON.stringify(reportData, null, 2),
    'utf-8'
);

console.log('\n数据已保存到 report_data.json');

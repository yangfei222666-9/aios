#!/usr/bin/env node

/**
 * Perplexity Research - Deep multi-round research
 * Usage: node research.mjs "topic" [options]
 */

import { parseArgs } from 'node:util';
import { writeFile } from 'node:fs/promises';
import { search } from './search.mjs';

async function research(topic, options = {}) {
  const depth = Math.min(options.depth || 3, 5);
  const model = options.model || 'sonar-pro';
  
  const results = [];
  let currentQuery = topic;

  console.error(`Starting research on: ${topic}`);
  console.error(`Depth: ${depth} rounds\n`);

  for (let round = 1; round <= depth; round++) {
    console.error(`Round ${round}/${depth}: ${currentQuery}`);
    
    const result = await search(currentQuery, { model });
    results.push({
      round: round,
      query: currentQuery,
      answer: result.answer,
      citations: result.citations
    });

    // Generate follow-up question for next round
    if (round < depth) {
      currentQuery = await generateFollowUp(topic, results);
      console.error(`  -> Follow-up: ${currentQuery}\n`);
    }
  }

  return {
    topic: topic,
    depth: depth,
    model: model,
    rounds: results,
    summary: generateSummary(results)
  };
}

async function generateFollowUp(topic, previousResults) {
  // Simple follow-up generation based on previous results
  const lastResult = previousResults[previousResults.length - 1];
  const round = previousResults.length;

  const followUps = [
    `What are the latest developments in ${topic}?`,
    `What are the challenges and limitations of ${topic}?`,
    `What are the best practices for implementing ${topic}?`,
    `What are the future trends in ${topic}?`,
    `What are real-world examples of ${topic}?`
  ];

  return followUps[round - 1] || `Tell me more about ${topic}`;
}

function generateSummary(results) {
  let summary = '# Research Summary\n\n';
  
  results.forEach((result, i) => {
    summary += `## Round ${result.round}: ${result.query}\n\n`;
    summary += `${result.answer}\n\n`;
    
    if (result.citations && result.citations.length > 0) {
      summary += `**Sources:**\n`;
      result.citations.forEach((citation, j) => {
        summary += `- ${citation}\n`;
      });
      summary += '\n';
    }
  });

  return summary;
}

function formatOutput(result, asJson = false) {
  if (asJson) {
    return JSON.stringify(result, null, 2);
  }

  return result.summary;
}

// CLI
if (import.meta.url === `file://${process.argv[1]}`) {
  const { values, positionals } = parseArgs({
    args: process.argv.slice(2),
    options: {
      depth: { type: 'string', default: '3' },
      model: { type: 'string', default: 'sonar-pro' },
      output: { type: 'string' },
      json: { type: 'boolean', default: false }
    },
    allowPositionals: true
  });

  const topic = positionals.join(' ');

  if (!topic) {
    console.error('Usage: node research.mjs "topic" [options]');
    console.error('Options:');
    console.error('  --depth <n>       Research depth (1-5, default: 3)');
    console.error('  --model <model>   Model: sonar-pro (default), sonar, sonar-reasoning');
    console.error('  --output <file>   Save report to file');
    console.error('  --json            Output JSON format');
    process.exit(1);
  }

  try {
    const result = await research(topic, {
      depth: parseInt(values.depth),
      model: values.model
    });

    const output = formatOutput(result, values.json);

    if (values.output) {
      await writeFile(values.output, output, 'utf-8');
      console.error(`\nReport saved to: ${values.output}`);
    } else {
      console.log(output);
    }
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

export { research, formatOutput };

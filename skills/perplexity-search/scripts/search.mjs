#!/usr/bin/env node

/**
 * Perplexity Search - Basic search with citations
 * Usage: node search.mjs "query" [options]
 */

import { parseArgs } from 'node:util';

const API_KEY = process.env.PERPLEXITY_API_KEY;
const API_URL = 'https://api.perplexity.ai/chat/completions';

// Available models
const MODELS = {
  'sonar-pro': 'llama-3.1-sonar-large-128k-online',
  'sonar': 'llama-3.1-sonar-small-128k-online',
  'sonar-reasoning': 'llama-3.1-sonar-huge-128k-online'
};

async function search(query, options = {}) {
  if (!API_KEY) {
    throw new Error('PERPLEXITY_API_KEY environment variable not set');
  }

  const model = MODELS[options.model || 'sonar-pro'];
  const maxResults = Math.min(options.count || 5, 10);

  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: model,
      messages: [
        {
          role: 'system',
          content: 'You are a helpful research assistant. Provide accurate, well-cited answers.'
        },
        {
          role: 'user',
          content: query
        }
      ],
      max_tokens: 2000,
      temperature: 0.2,
      top_p: 0.9,
      return_citations: true,
      return_images: false,
      search_recency_filter: 'month'
    })
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Perplexity API error: ${response.status} ${error}`);
  }

  const data = await response.json();
  
  return {
    query: query,
    answer: data.choices[0].message.content,
    citations: data.citations || [],
    model: options.model || 'sonar-pro',
    usage: data.usage
  };
}

function formatOutput(result, asJson = false) {
  if (asJson) {
    return JSON.stringify(result, null, 2);
  }

  let output = `Query: ${result.query}\n`;
  output += `Model: ${result.model}\n`;
  output += `---\n\n`;
  output += `${result.answer}\n\n`;

  if (result.citations && result.citations.length > 0) {
    output += `Sources:\n`;
    result.citations.forEach((citation, i) => {
      output += `${i + 1}. ${citation}\n`;
    });
  }

  if (result.usage) {
    output += `\n---\n`;
    output += `Tokens: ${result.usage.total_tokens} (prompt: ${result.usage.prompt_tokens}, completion: ${result.usage.completion_tokens})\n`;
  }

  return output;
}

// CLI
if (import.meta.url === `file://${process.argv[1]}`) {
  const { values, positionals } = parseArgs({
    args: process.argv.slice(2),
    options: {
      count: { type: 'string', short: 'n', default: '5' },
      model: { type: 'string', default: 'sonar-pro' },
      json: { type: 'boolean', default: false }
    },
    allowPositionals: true
  });

  const query = positionals.join(' ');

  if (!query) {
    console.error('Usage: node search.mjs "query" [options]');
    console.error('Options:');
    console.error('  -n <count>       Number of results (default: 5, max: 10)');
    console.error('  --model <model>  Model: sonar-pro (default), sonar, sonar-reasoning');
    console.error('  --json           Output JSON format');
    process.exit(1);
  }

  try {
    const result = await search(query, {
      count: parseInt(values.count),
      model: values.model
    });

    console.log(formatOutput(result, values.json));
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

export { search, formatOutput };

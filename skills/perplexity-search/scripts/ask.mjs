#!/usr/bin/env node

/**
 * Perplexity Ask - Conversational search with context
 * Usage: node ask.mjs "question" [options]
 */

import { parseArgs } from 'node:util';

const API_KEY = process.env.PERPLEXITY_API_KEY;
const API_URL = 'https://api.perplexity.ai/chat/completions';

const MODELS = {
  'sonar-pro': 'llama-3.1-sonar-large-128k-online',
  'sonar': 'llama-3.1-sonar-small-128k-online',
  'sonar-reasoning': 'llama-3.1-sonar-huge-128k-online'
};

async function ask(question, options = {}) {
  if (!API_KEY) {
    throw new Error('PERPLEXITY_API_KEY environment variable not set');
  }

  const model = MODELS[options.model || 'sonar-pro'];
  const messages = [
    {
      role: 'system',
      content: 'You are a helpful research assistant. Provide accurate, well-cited answers based on context.'
    }
  ];

  // Add context if provided
  if (options.context) {
    messages.push({
      role: 'assistant',
      content: options.context
    });
  }

  messages.push({
    role: 'user',
    content: question
  });

  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: model,
      messages: messages,
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
    question: question,
    context: options.context || null,
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

  let output = '';
  
  if (result.context) {
    output += `Context: ${result.context}\n`;
  }
  
  output += `Question: ${result.question}\n`;
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
    output += `Tokens: ${result.usage.total_tokens}\n`;
  }

  return output;
}

// CLI
if (import.meta.url === `file://${process.argv[1]}`) {
  const { values, positionals } = parseArgs({
    args: process.argv.slice(2),
    options: {
      context: { type: 'string' },
      model: { type: 'string', default: 'sonar-pro' },
      json: { type: 'boolean', default: false }
    },
    allowPositionals: true
  });

  const question = positionals.join(' ');

  if (!question) {
    console.error('Usage: node ask.mjs "question" [options]');
    console.error('Options:');
    console.error('  --context <text>  Previous conversation context');
    console.error('  --model <model>   Model: sonar-pro (default), sonar, sonar-reasoning');
    console.error('  --json            Output JSON format');
    process.exit(1);
  }

  try {
    const result = await ask(question, {
      context: values.context,
      model: values.model
    });

    console.log(formatOutput(result, values.json));
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

export { ask, formatOutput };

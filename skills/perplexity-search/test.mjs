#!/usr/bin/env node

/**
 * Test Perplexity Search Skill
 * Tests basic search, conversational search, and research modes
 */

import { search } from './scripts/search.mjs';
import { ask } from './scripts/ask.mjs';
import { research } from './scripts/research.mjs';

console.log('=== Perplexity Search Skill Test ===\n');

// Check API key
if (!process.env.PERPLEXITY_API_KEY) {
  console.error('❌ PERPLEXITY_API_KEY not set');
  console.error('Get your API key from: https://www.perplexity.ai/settings/api');
  console.error('\nSet it with:');
  console.error('  Windows: set PERPLEXITY_API_KEY=pplx-xxxxx');
  console.error('  Linux/Mac: export PERPLEXITY_API_KEY=pplx-xxxxx');
  process.exit(1);
}

console.log('✅ API key found\n');

// Test 1: Basic Search
console.log('Test 1: Basic Search');
console.log('Query: "Perplexity AI funding 2026"\n');

try {
  const result1 = await search('Perplexity AI funding 2026', {
    model: 'sonar',
    count: 3
  });

  console.log('Answer:', result1.answer.substring(0, 200) + '...');
  console.log('Citations:', result1.citations.length);
  console.log('Tokens:', result1.usage?.total_tokens || 'N/A');
  console.log('✅ Test 1 passed\n');
} catch (error) {
  console.error('❌ Test 1 failed:', error.message);
  process.exit(1);
}

// Test 2: Conversational Search
console.log('Test 2: Conversational Search');
console.log('Context: "Perplexity is an AI search engine"');
console.log('Question: "How does it compare to Google?"\n');

try {
  const result2 = await ask('How does it compare to Google?', {
    context: 'Perplexity is an AI search engine with real-time web access and citations',
    model: 'sonar'
  });

  console.log('Answer:', result2.answer.substring(0, 200) + '...');
  console.log('Citations:', result2.citations.length);
  console.log('�� Test 2 passed\n');
} catch (error) {
  console.error('❌ Test 2 failed:', error.message);
  process.exit(1);
}

// Test 3: Deep Research (2 rounds only for testing)
console.log('Test 3: Deep Research (2 rounds)');
console.log('Topic: "AIOS architecture patterns"\n');

try {
  const result3 = await research('AIOS architecture patterns', {
    depth: 2,
    model: 'sonar'
  });

  console.log('Rounds completed:', result3.rounds.length);
  console.log('Summary length:', result3.summary.length, 'chars');
  console.log('✅ Test 3 passed\n');
} catch (error) {
  console.error('❌ Test 3 failed:', error.message);
  process.exit(1);
}

console.log('=== All Tests Passed ✅ ===');
console.log('\nNext steps:');
console.log('1. Try: node scripts/search.mjs "your query"');
console.log('2. Try: node scripts/ask.mjs "your question" --context "previous answer"');
console.log('3. Try: node scripts/research.mjs "your topic" --depth 3 --output report.md');

import { safeParsePartialJson } from "../../src/lib/partial-json";

function assert(condition: boolean, message: string) {
  if (!condition) {
    console.error(`❌ FAILED: ${message}`);
    process.exit(1);
  } else {
    console.log(`✅ PASSED: ${message}`);
  }
}

function assertEqual(actual: any, expected: any, message: string) {
  const actualStr = JSON.stringify(actual);
  const expectedStr = JSON.stringify(expected);
  if (actualStr !== expectedStr) {
    console.error(`❌ FAILED: ${message}`);
    console.error(`   Expected: ${expectedStr}`);
    console.error(`   Actual:   ${actualStr}`);
    process.exit(1);
  } else {
    console.log(`✅ PASSED: ${message}`);
  }
}

console.log("Running safeParsePartialJson tests...");

// Test 1: Valid JSON
const input1 = '{"type": "quiz", "question": "What is AI?"}';
const result1 = safeParsePartialJson(input1);
assertEqual(result1, { type: "quiz", question: "What is AI?" }, "Valid JSON");

// Test 2: Missing closing brace
const input2 = '{"type": "quiz"';
const result2 = safeParsePartialJson(input2);
assertEqual(result2, { type: "quiz" }, "Missing closing brace");

// Test 3: Missing closing brace and quote
const input3 = '{"type": "quiz", "question": "What is';
const result3 = safeParsePartialJson(input3);
assertEqual(result3, { type: "quiz", question: "What is" }, "Missing closing brace and quote");

// Test 4: Nested objects
const input4 = '{"type": "quiz", "data": {"id": 1';
const result4 = safeParsePartialJson(input4);
assertEqual(result4, { type: "quiz", data: { id: 1 } }, "Nested objects");

// Test 5: Invalid JSON (should return null)
const input5 = 'not json';
const result5 = safeParsePartialJson(input5);
assertEqual(result5, null, "Invalid JSON returns null");

console.log("All tests passed!");

/**
 * Wrapper for best-effort-json-parser or a simple custom implementation.
 * If you don't want an external dependency, here is a simple regex-based 'fixer' 
 * for common truncation, but using a robust library is safer.
 * * For this example, we assume you install 'best-effort-json-parser' 
 * OR use this simple fallback logic for the specific schema we have.
 */

export function safeParsePartialJson(jsonString: string): any {
  try {
    return JSON.parse(jsonString); // Try standard parse first
  } catch (e) {
    // If it fails, try to "close" the string blindly to make it valid JSON
    // This is a naive implementation; for production, use a library like 'partial-json'
    try {
      // Very naive attempt to close braces
      // 1. Count open braces vs closed
      const openBraces = (jsonString.match(/\{/g) || []).length;
      const closedBraces = (jsonString.match(/\}/g) || []).length;
      const missingBraces = openBraces - closedBraces;
      
      // 2. Count open quotes
      const quoteCount = (jsonString.match(/"/g) || []).length;
      let fixedString = jsonString;
      
      // If we are inside a string, close it
      if (quoteCount % 2 !== 0) {
        fixedString += '"';
      }
      
      // Close missing braces
      fixedString += "}".repeat(missingBraces);
      
      return JSON.parse(fixedString);
    } catch (err) {
      return null; // Still failed, return null (wait for more data)
    }
  }
}

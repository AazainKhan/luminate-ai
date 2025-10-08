/**
 * Student ID Management
 * Generates and persists browser fingerprint for student identification
 */

/**
 * Generate a browser fingerprint based on available information
 */
function generateFingerprint(): string {
  const navigator = window.navigator;
  const screen = window.screen;
  
  // Collect browser characteristics
  const components = [
    navigator.userAgent,
    navigator.language,
    screen.colorDepth,
    screen.width + 'x' + screen.height,
    new Date().getTimezoneOffset(),
    navigator.hardwareConcurrency || 'unknown',
    (navigator as any).deviceMemory || 'unknown',
  ];
  
  // Create a simple hash
  const str = components.join('|');
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  
  return `fp_${Math.abs(hash).toString(36)}_${Date.now().toString(36)}`;
}

/**
 * Get or create student ID
 */
export async function getStudentId(): Promise<string> {
  try {
    // Try to get from chrome.storage first
    const result = await chrome.storage.local.get(['studentId']);
    
    if (result.studentId) {
      return result.studentId;
    }
    
    // Generate new fingerprint
    const studentId = generateFingerprint();
    
    // Store it
    await chrome.storage.local.set({ studentId });
    
    return studentId;
  } catch (error) {
    console.error('Error managing student ID:', error);
    // Fallback to sessionStorage for non-extension environments
    let studentId = sessionStorage.getItem('studentId');
    if (!studentId) {
      studentId = generateFingerprint();
      sessionStorage.setItem('studentId', studentId);
    }
    return studentId;
  }
}

/**
 * Clear student ID (for testing or reset)
 */
export async function clearStudentId(): Promise<void> {
  try {
    await chrome.storage.local.remove(['studentId']);
  } catch (error) {
    sessionStorage.removeItem('studentId');
  }
}

/**
 * Get session ID (generates new one each session)
 */
export function getSessionId(): string {
  let sessionId = sessionStorage.getItem('luminateSessionId');
  if (!sessionId) {
    sessionId = `session_${Date.now().toString(36)}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('luminateSessionId', sessionId);
  }
  return sessionId;
}


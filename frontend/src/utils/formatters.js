/**
 * Utility functions for formatting UI data
 */

export function getConfidenceLabel(confidence) {
  if (confidence == null) return 'Unknown';
  if (confidence >= 0.80) return 'High Confidence';
  if (confidence >= 0.60) return 'Medium Confidence';
  return 'Low Confidence';
}

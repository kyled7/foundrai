/**
 * Sound playback utility for FoundrAI
 * Handles audio notification sounds with volume control and error handling
 */

/**
 * Play a notification sound
 * @param soundPath - Path to the sound file (relative to public directory or absolute URL)
 * @param volume - Volume level (0.0 to 1.0), defaults to 0.5
 * @returns Promise that resolves when sound finishes playing or rejects on error
 */
export async function playSound(soundPath: string, volume: number = 0.5): Promise<void> {
  try {
    // Validate volume
    const clampedVolume = Math.max(0, Math.min(1, volume));

    // Create audio element
    const audio = new Audio(soundPath);
    audio.volume = clampedVolume;

    // Play the sound
    await audio.play();

    // Wait for sound to finish
    return new Promise((resolve, reject) => {
      audio.onended = () => resolve();
      audio.onerror = () => {
        const error = new Error(`Failed to play sound: ${soundPath}`);
        reject(error);
      };
    });
  } catch (err) {
    const error = err instanceof Error ? err : new Error('Failed to play sound');
    throw error;
  }
}

/**
 * Play the notification sound for approval requests
 * Uses the default notification sound with standard volume
 */
export async function playNotificationSound(volume: number = 0.5): Promise<void> {
  const soundPath = '/notification.mp3';
  return playSound(soundPath, volume);
}

/**
 * Check if audio playback is supported in the current browser
 */
export function isAudioSupported(): boolean {
  try {
    return typeof Audio !== 'undefined';
  } catch {
    return false;
  }
}

/**
 * Preload a sound file for instant playback
 * Useful for ensuring sounds play without delay
 * @param soundPath - Path to the sound file to preload
 * @returns Promise that resolves when sound is loaded
 */
export async function preloadSound(soundPath: string): Promise<HTMLAudioElement> {
  return new Promise((resolve, reject) => {
    const audio = new Audio(soundPath);
    audio.oncanplaythrough = () => resolve(audio);
    audio.onerror = () => {
      const error = new Error(`Failed to preload sound: ${soundPath}`);
      reject(error);
    };
    // Trigger loading
    audio.load();
  });
}

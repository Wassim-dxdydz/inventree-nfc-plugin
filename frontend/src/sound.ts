import './assets/click.mp3?url';
import './assets/success.mp3?url';
import './assets/error.mp3?url';
import './assets/timeout.mp3?url';

export type NfcSoundName = 'click' | 'success' | 'error' | 'timeout';

export function playSound(enabled: boolean, sound: NfcSoundName) {
  if (!enabled) return;
  try {
    const audio = new Audio(`/static/plugins/nfc/assets/${sound}.mp3`);
    audio.volume = 0.5;
    void audio.play().catch(() => {});
  } catch {
    // silently ignore
  }
}
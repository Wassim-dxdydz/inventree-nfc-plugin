import clickSound from './assets/sounds/click.mp3'
import successSound from './assets/sounds/success.mp3'
import errorSound from './assets/sounds/error.mp3'
import timeoutSound from './assets/sounds/timeout.mp3'

export type NfcSoundName =
    | "click"
    | "success"
    | "error"
    | "timeout";

const SOUND_MAP: Record<NfcSoundName, string> = {
    click: clickSound,
    success: successSound,
    error: errorSound,
    timeout: timeoutSound,
}

export function playSound(enabled: boolean, sound: NfcSoundName){
    if (!enabled) return;
    try {
        const audio =  new Audio(SOUND_MAP[sound]);
        audio.volume = 0.5;
        void audio.play().catch(() => {});
    } catch {
        
    }
}
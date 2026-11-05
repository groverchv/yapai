// PWA: captura el evento nativo de instalación y expone la acción instalar().
// El navegador solo dispara beforeinstallprompt cuando el sitio es instalable
// (manifest + service worker + contexto seguro). En iOS/Safari no existe:
// instalar() devuelve false y la UI muestra instrucciones manuales.

interface BeforeInstallPromptEvent extends Event {
	prompt(): Promise<void>;
	userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

let diferido = $state<BeforeInstallPromptEvent | null>(null);
let instalada = $state(false);
let inicializado = false;

export const pwa = {
	/** El navegador ofreció prompt nativo (Chrome/Edge/Android). */
	get instalable() {
		return diferido !== null;
	},
	/** Ya corre como app instalada (display-mode standalone). */
	get instalada() {
		return instalada;
	},
	/** Llamar una vez desde el layout raíz (onMount). */
	registrar() {
		if (inicializado || typeof window === 'undefined') return;
		inicializado = true;
		instalada = window.matchMedia('(display-mode: standalone)').matches;
		window.addEventListener('beforeinstallprompt', (e) => {
			e.preventDefault();
			diferido = e as BeforeInstallPromptEvent;
		});
		window.addEventListener('appinstalled', () => {
			diferido = null;
			instalada = true;
		});
	},
	/** Lanza el diálogo nativo. false = el navegador no lo ofrece (mostrar instrucciones). */
	async instalar(): Promise<boolean> {
		if (!diferido) return false;
		const d = diferido;
		diferido = null;
		await d.prompt();
		const { outcome } = await d.userChoice;
		if (outcome === 'accepted') instalada = true;
		return outcome === 'accepted';
	},
};

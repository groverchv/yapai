// SvelteKit 3 dejó de generar tipos para el módulo compat $env/dynamic/public
// (sigue funcionando en runtime con adapter-node). Declaración propia:
declare module '$env/dynamic/public' {
	export const env: Record<string, string | undefined>;
}

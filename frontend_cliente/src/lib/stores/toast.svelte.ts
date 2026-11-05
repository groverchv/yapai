export type ToastTipo = 'exito' | 'error' | 'info';

interface Toast {
	id: number;
	tipo: ToastTipo;
	texto: string;
}

let lista = $state<Toast[]>([]);
let nextId = 1;

function quitar(id: number) {
	lista = lista.filter((t) => t.id !== id);
}

function agregar(texto: string, tipo: ToastTipo, duracion = 4000) {
	const id = nextId++;
	lista = [...lista, { id, tipo, texto }];
	setTimeout(() => quitar(id), duracion);
}

export const toast = {
	get lista() { return lista; },
	exito: (texto: string) => agregar(texto, 'exito'),
	error: (texto: string) => agregar(texto, 'error', 5000),
	info: (texto: string) => agregar(texto, 'info'),
	quitar,
};

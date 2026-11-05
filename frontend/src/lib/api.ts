import { PUBLIC_API_BASE_URL } from '$app/env/public';

export type Tier = 'guest' | 'member';

export interface User {
	id: string;
	email: string;
	name: string;
}

export interface CatalogItem {
	id: string;
	name: string;
	category: string;
	brand: string;
	model: string;
	material: string;
	form_factor: string;
	socket: string;
	condition: string;
	grade: string;
	color: string;
	shop: string;
	price: number;
	noise: string;
	power: string;
	purposes: string[];
	summary: string;
	specs: Record<string, string>;
	url?: string;
	image?: string;
	source: 'naver' | 'reference';
	availability?: 'selling' | 'discontinued' | 'sold' | 'upcoming' | 'unverified' | 'reference';
	fetched_at?: string;
}

export interface FacetValue {
	value: string;
	count: number;
}

export interface CatalogResponse {
	snapshot: string;
	note: string;
	price_kind: string;
	live_fetched_at: string;
	live_count: number;
	tier: Tier;
	total: number;
	offset: number;
	limit: number;
	shortlist_limit: number;
	recommend_limit: number;
	locked_filters: string[];
	facets: Record<string, FacetValue[]>;
	items: CatalogItem[];
}

export interface CatalogFilters {
	part_name: string;
	purpose: string;
	price_max: string;
	condition: string;
	category: string;
	brand: string;
	model: string;
	material: string;
	form_factor: string;
	socket: string;
	shop: string;
	color: string;
	noise: string;
	power: string;
	grade: string;
	source: '' | 'naver' | 'reference';
	offset: number;
}

export interface RecommendRequest {
	purpose: string;
	budget_krw: number;
	condition: 'new' | 'used' | 'mixed';
	part_name?: string;
	category?: string;
	brand?: string;
	model?: string;
	material?: string;
	shop?: string;
	form_factor?: string;
	socket?: string;
	color?: string;
	noise?: string;
	power?: string;
	grade?: string;
	selected_ids?: string[];
	notes?: string;
	priorities?: string[];
}

export interface Recommendation {
	id: string;
	product_name: string;
	category: string;
	price: number;
	site: string;
	is_used: boolean;
	is_mock: boolean;
	score: number;
	reason: string;
	model: string;
	brand: string;
	material: string;
	grade: string;
	summary: string;
	url?: string | null;
}

export interface AgentResult {
	recommendations: Recommendation[];
	warnings: string[];
	explanation: string;
	steps: string[];
	tier?: Tier;
	session_id?: string | null;
}

export interface SavedSession {
	id: string;
	created_at: string;
	status: string;
	purpose: string;
	budget_krw: number;
	explanation: string;
	recommendations: { product_name: string; price: number; site: string; reason: string }[];
}

function authHeaders(token?: string | null, json = false): Record<string, string> {
	const headers: Record<string, string> = {};
	if (json) headers['Content-Type'] = 'application/json';
	if (token) headers.Authorization = `Bearer ${token}`;
	return headers;
}

async function readError(response: Response): Promise<string> {
	try {
		const body = await response.json();
		if (typeof body.error === 'string') return body.error;
		if (Array.isArray(body.detail)) {
			const messages = body.detail
				.map((item: { msg?: string }) => item.msg)
				.filter((item: string | undefined): item is string => Boolean(item));
			if (messages.length) return messages.join(' ');
		}
	} catch {
		// 본문이 JSON이 아니면 상태 코드만 알린다.
	}
	return `요청이 거절되었습니다 (${response.status})`;
}

async function send(path: string, init: RequestInit): Promise<Response> {
	try {
		return await fetch(`${PUBLIC_API_BASE_URL}${path}`, init);
	} catch {
		throw new Error('서버에 연결하지 못했습니다');
	}
}

export async function fetchCatalog(
	filters: CatalogFilters,
	token: string | null,
	unlimited: boolean
): Promise<CatalogResponse> {
	const params = new URLSearchParams();
	const textFields: (keyof CatalogFilters)[] = [
		'part_name',
		'purpose',
		'condition',
		'category',
		'brand',
		'model',
		'material',
		'form_factor',
		'socket',
		'shop',
		'color',
		'noise',
		'power',
		'grade',
		'source'
	];
	for (const key of textFields) {
		const value = filters[key];
		if (typeof value === 'string' && value) params.set(key, value);
	}
	if (!unlimited && filters.price_max) params.set('price_max', filters.price_max);
	if (filters.offset > 0) params.set('offset', String(filters.offset));
	const response = await send(`/api/catalog?${params}`, { headers: authHeaders(token) });
	if (!response.ok) throw new Error(await readError(response));
	return response.json();
}

export async function requestRecommendation(
	requirements: RecommendRequest,
	token: string | null
): Promise<AgentResult> {
	const response = await send('/api/recommend', {
		method: 'POST',
		headers: authHeaders(token, true),
		body: JSON.stringify(requirements)
	});
	if (!response.ok) throw new Error(await readError(response));
	return response.json();
}

export async function register(email: string, password: string, name: string) {
	const response = await send('/api/auth/register', {
		method: 'POST',
		headers: authHeaders(null, true),
		body: JSON.stringify({ email, password, name })
	});
	if (!response.ok) throw new Error(await readError(response));
	return response.json() as Promise<{ token: string; user: User }>;
}

export async function login(email: string, password: string) {
	const response = await send('/api/auth/login', {
		method: 'POST',
		headers: authHeaders(null, true),
		body: JSON.stringify({ email, password })
	});
	if (!response.ok) throw new Error(await readError(response));
	return response.json() as Promise<{ token: string; user: User }>;
}

export async function logout(token: string) {
	await send('/api/auth/logout', { method: 'POST', headers: authHeaders(token) });
}

export async function me(token: string): Promise<User> {
	const response = await send('/api/auth/me', { headers: authHeaders(token) });
	if (!response.ok) throw new Error(await readError(response));
	return response.json();
}

export async function listSessions(token: string): Promise<SavedSession[]> {
	const response = await send('/api/sessions', { headers: authHeaders(token) });
	if (!response.ok) throw new Error(await readError(response));
	const body = (await response.json()) as { sessions: SavedSession[] };
	return body.sessions;
}

import { logout, me, type User } from '#lib/api.ts';

const browser = typeof window !== 'undefined';

const TOKEN_KEY = 'pcforge.token';

export const session = $state<{ token: string | null; user: User | null; ready: boolean }>({
	token: null,
	user: null,
	ready: false
});

export async function restore() {
	if (!browser) return;
	const token = localStorage.getItem(TOKEN_KEY);
	session.token = token;
	if (!token) {
		session.user = null;
		session.ready = true;
		return;
	}
	try {
		session.user = await me(token);
	} catch {
		localStorage.removeItem(TOKEN_KEY);
		session.token = null;
		session.user = null;
	} finally {
		session.ready = true;
	}
}

export function signIn(token: string, user: User) {
	if (browser) localStorage.setItem(TOKEN_KEY, token);
	session.token = token;
	session.user = user;
	session.ready = true;
}

export async function signOut() {
	const token = session.token;
	session.token = null;
	session.user = null;
	if (browser) localStorage.removeItem(TOKEN_KEY);
	if (token) {
		try {
			await logout(token);
		} catch {
			// 로컬 로그인 상태는 이미 비웠다.
		}
	}
}

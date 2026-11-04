import { PUBLIC_API_BASE_URL } from '$app/env/public';

export type Condition = 'new' | 'used' | 'mixed';

export interface Requirements {
	purpose: string;
	budget_krw: number;
	condition: Condition;
}

export interface Recommendation {
	product_name: string;
	category: string;
	price: number;
	site: string;
	url: string | null;
	is_used: boolean;
	is_mock: boolean;
	score: number;
	reason: string;
}

export interface AgentResult {
	recommendations: Recommendation[];
	warnings: string[];
	explanation: string;
	steps: string[];
}

export async function requestRecommendation(requirements: Requirements): Promise<AgentResult> {
	const response = await fetch(`${PUBLIC_API_BASE_URL}/api/recommend`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(requirements)
	});
	if (!response.ok) {
		throw new Error(`추천 요청 실패 (${response.status})`);
	}
	return response.json();
}

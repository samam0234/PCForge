import { defineEnvVars } from '@sveltejs/kit/env';

export const variables = defineEnvVars({
	PUBLIC_API_BASE_URL: {
		public: true,
		description: 'Axum 백엔드 주소',
		schema: (value) => value || 'http://localhost:3000'
	}
});

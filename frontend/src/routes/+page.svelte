<script lang="ts">
	import RecommendationCard from '../components/RecommendationCard.svelte';
	import RequirementForm from '../components/RequirementForm.svelte';
	import { requestRecommendation, type AgentResult, type Requirements } from '#lib/api.ts';

	let result = $state<AgentResult | null>(null);
	let error = $state<string | null>(null);
	let loading = $state(false);

	async function recommend(requirements: Requirements) {
		loading = true;
		error = null;
		try {
			result = await requestRecommendation(requirements);
		} catch (e) {
			result = null;
			error = e instanceof Error ? e.message : '알 수 없는 오류가 발생했습니다';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>PCForge</title>
</svelte:head>

<main>
	<h1>PCForge</h1>
	<RequirementForm disabled={loading} onsubmit={recommend} />

	{#if loading}
		<p>추천을 만드는 중입니다…</p>
	{/if}

	{#if error}
		<p role="alert">{error}</p>
	{/if}

	{#if result}
		<p>{result.explanation}</p>
		{#each result.warnings as warning}
			<p role="alert">{warning}</p>
		{/each}
		{#each result.recommendations as item}
			<RecommendationCard {item} />
		{/each}
	{/if}
</main>

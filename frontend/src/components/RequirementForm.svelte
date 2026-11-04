<script lang="ts">
	import type { Condition, Requirements } from '#lib/api.ts';

	let {
		disabled = false,
		onsubmit
	}: { disabled?: boolean; onsubmit: (requirements: Requirements) => void } = $props();

	const purposes = ['게이밍', '영상편집', '개발', 'AI 학습', '사무'];

	let purpose = $state(purposes[0]);
	let budget = $state(1500000);
	let condition = $state<Condition>('mixed');

	function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		onsubmit({ purpose, budget_krw: budget, condition });
	}
</script>

<form onsubmit={handleSubmit}>
	<label>
		용도
		<select bind:value={purpose}>
			{#each purposes as item}
				<option value={item}>{item}</option>
			{/each}
		</select>
	</label>

	<label>
		예산 (원)
		<input type="number" min="1" step="10000" required bind:value={budget} />
	</label>

	<label>
		상태
		<select bind:value={condition}>
			<option value="mixed">신품 + 중고</option>
			<option value="new">신품만</option>
			<option value="used">중고만</option>
		</select>
	</label>

	<button type="submit" {disabled}>추천 받기</button>
</form>

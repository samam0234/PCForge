<script lang="ts">
	import type { Recommendation } from '#lib/api.ts';

	let { item }: { item: Recommendation } = $props();
</script>

<article>
	<h3>{item.product_name}</h3>
	<p>{item.price.toLocaleString('ko-KR')}원 · {item.site} · {item.is_used ? '중고' : '신품'}</p>
	<p>{item.reason}</p>
</article>

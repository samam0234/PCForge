<script lang="ts">
	import { articles, type Article } from '#lib/journal.ts';

	let { data }: { data: { article: Article } } = $props();
	const others = $derived(articles.filter((article) => article.slug !== data.article.slug));
</script>

<svelte:head>
	<title>{data.article.title} — PCForge</title>
</svelte:head>

<article class="story-page">
	<header class="page-head center">
		<p class="eyebrow">{data.article.kicker} · {data.article.date}</p>
		<h1>{data.article.title}</h1>
		<p class="byline">PCForge 편집부</p>
	</header>
	<div class="column wide">
		{#each data.article.paragraphs as paragraph, index (`p-${index}`)}
			<p class:first={index === 0}>{paragraph}</p>
		{/each}
	</div>
	<footer class="story-foot">
		<a class="btn primary" href="/#desk">이 내용으로 목록 펼치기</a>
		<a class="btn ghost" href="/journal">조립 노트 목록</a>
	</footer>
</article>

<section class="reading compact" aria-label="다른 글">
	{#each others as article (article.slug)}
		<a class="read-card" href="/journal/{article.slug}">
			<span class="eyebrow">{article.kicker}</span>
			<strong>{article.title}</strong>
		</a>
	{/each}
</section>

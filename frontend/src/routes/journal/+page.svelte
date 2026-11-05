<script lang="ts">
	import { articles } from '#lib/journal.ts';
</script>

<svelte:head>
	<title>조립 노트 — PCForge</title>
</svelte:head>

<header class="page-head">
	<p class="eyebrow">연재 · 조립 노트</p>
	<h1>부품을 고르기 전에 읽는 글</h1>
	<p class="lead">소켓, 소재, 중고 등급, 쇼핑몰. 목록을 펼치기 전에 알아 두면 고르는 시간이 줄어드는 이야기입니다.</p>
</header>

<div class="journal-grid">
	{#each articles as article, index (article.slug)}
		<a class="story" class:lead-story={index === 0} href="/journal/{article.slug}">
			<span class="read-no">{String(index + 1).padStart(2, '0')}</span>
			<p class="eyebrow">{article.kicker} · {article.date}</p>
			<h2>{article.title}</h2>
			<p>{article.paragraphs[0]}</p>
			<span class="more">읽기 →</span>
		</a>
	{/each}
</div>

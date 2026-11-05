<script lang="ts">
	import CatalogDesk from '../components/CatalogDesk.svelte';
	import { requestRecommendation, type AgentResult, type RecommendRequest } from '#lib/api.ts';
	import { articles } from '#lib/journal.ts';
	import { session } from '#lib/session.svelte.ts';

	let result = $state<AgentResult | null>(null);
	let error = $state<string | null>(null);
	let loading = $state(false);

	const total = $derived(result?.recommendations.reduce((sum, item) => sum + item.price, 0) ?? 0);
	const paragraphs = $derived(
		(result?.explanation ?? '')
			.split(/\n+/)
			.map((line) => line.replace(/^#+\s*/, '').replace(/\*\*/g, '').trim())
			.filter(Boolean)
	);

	async function recommend(requirements: RecommendRequest) {
		loading = true;
		error = null;
		document.getElementById('recommendation')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
		try {
			result = await requestRecommendation(requirements, session.token);
		} catch (reason) {
			result = null;
			error = reason instanceof Error ? reason.message : '추천을 만들지 못했습니다';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>PCForge — 이번 호의 부품 노트</title>
</svelte:head>

<section class="hero">
	<div class="hero-copy">
		<p class="eyebrow">이번 호 특집 · 조립 전에 읽는 지면</p>
		<h1>고르기 전에,<br /><em>시장을 길게</em> 펼칩니다</h1>
		<p class="lead">
			용도와 예산부터 모델, 부품명, 소재, 소켓, 쇼핑몰까지 열다섯 칸으로 매물을 걸러 담아 두고,
			그 목록 안에서 편집부가 구성을 골라 드립니다.
		</p>
		<div class="hero-actions">
			<a class="btn primary" href="#desk">목록 펼치기</a>
			<a class="btn ghost" href="/journal">조립 노트 읽기</a>
		</div>
	</div>
	<aside class="hero-card">
		<p class="eyebrow light">이번 호를 읽는 순서</p>
		<ol class="steps-list">
			<li><b>01</b><div><strong>칸을 고릅니다</strong><span>용도·예산·소켓·쇼핑몰 등 열다섯 칸</span></div></li>
			<li><b>02</b><div><strong>매물을 담습니다</strong><span>같은 모델도 판매처마다 한 줄씩</span></div></li>
			<li><b>03</b><div><strong>추천을 받습니다</strong><span>호환 메모를 근거로 로컬 모델이 씁니다</span></div></li>
		</ol>
		{#if session.ready && !session.user}
			<a class="hero-link" href="/login">로그인하면 모델·소재·색·소음이 열리고 기록이 남습니다 →</a>
		{:else if session.user}
			<p class="hero-link">{session.user.name} 님, 회원 칸이 모두 열려 있습니다.</p>
		{/if}
	</aside>
</section>

<section class="reading" aria-label="조립 노트">
	{#each articles as article, index (article.slug)}
		<a class="read-card" href="/journal/{article.slug}">
			<span class="read-no">{String(index + 1).padStart(2, '0')}</span>
			<span class="eyebrow">{article.kicker}</span>
			<strong>{article.title}</strong>
		</a>
	{/each}
</section>

<CatalogDesk disabled={loading} onrecommend={recommend} />

<section class="essay" id="recommendation">
	<header class="section-head">
		<div>
			<p class="eyebrow">편집부가 고른 것</p>
			<h2>추천 구성</h2>
		</div>
		{#if result}
			<dl class="stats">
				<div><dt>구성</dt><dd>{result.recommendations.length}개</dd></div>
				<div><dt>합계</dt><dd>{total.toLocaleString('ko-KR')}원</dd></div>
				<div><dt>열람</dt><dd>{result.tier === 'member' ? '회원' : '비로그인'}</dd></div>
			</dl>
		{/if}
	</header>

	{#if loading}
		<div class="loading-card">
			<span class="spinner" aria-hidden="true"></span>
			<div>
				<strong>기준 시세와 호환 메모를 읽고 있습니다</strong>
				<p>로컬 모델을 처음 깨우면 20초 남짓 걸립니다.</p>
			</div>
		</div>
	{:else if error}
		<p class="note warn" role="alert">{error}</p>
	{:else if !result}
		<div class="placeholder">
			<p>위 지면에서 용도를 고르고 <b>이 목록으로 추천받기</b>를 누르면, 이 자리에 편집부의 구성이 실립니다.</p>
		</div>
	{/if}

	{#if result && !loading}
		<div class="essay-grid">
			<article class="column">
				{#each paragraphs as paragraph, index (`p-${index}`)}
					<p class:first={index === 0}>{paragraph}</p>
				{/each}
				{#if result.session_id}
					<p class="saved"><a href="/history">이 추천은 기록에 남았습니다 →</a></p>
				{/if}
			</article>

			<div class="side">
				<table class="build">
					<thead>
						<tr><th>No.</th><th>분류 · 제품</th><th class="num">기준 시세</th></tr>
					</thead>
					<tbody>
						{#each result.recommendations as item, index (item.id || item.product_name)}
							<tr>
								<td class="no">{String(index + 1).padStart(2, '0')}</td>
								<td>
									<span class="eyebrow">{item.category}</span>
									{#if item.url}
										<a class="product-link" href={item.url} target="_blank" rel="noopener noreferrer"><strong>{item.product_name}</strong></a>
										<a class="proof" href={item.url} target="_blank" rel="noopener noreferrer">원본 링크 ↗</a>
									{:else}
										<strong>{item.product_name}</strong>
									{/if}
									<span class="quiet">{item.site} · {item.is_used ? '중고' : '신품'} {item.grade}</span>
								</td>
								<td class="num">{item.price.toLocaleString('ko-KR')}원</td>
							</tr>
						{/each}
					</tbody>
					<tfoot>
						<tr><td></td><td>합계</td><td class="num">{total.toLocaleString('ko-KR')}원</td></tr>
					</tfoot>
				</table>

				{#if result.warnings.length}
					<div class="notes">
						<p class="eyebrow">편집부 메모</p>
						{#each result.warnings as warning, index (`w-${index}`)}
							<p class="note">{warning}</p>
						{/each}
					</div>
				{/if}

				<details class="process">
					<summary>편집 과정 보기</summary>
					<ol>
						{#each result.steps as step, index (`s-${index}`)}
							<li>{step}</li>
						{/each}
					</ol>
				</details>
			</div>
		</div>
	{/if}
</section>

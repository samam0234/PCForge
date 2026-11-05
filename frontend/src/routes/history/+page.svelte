<script lang="ts">
	import { listSessions, type SavedSession } from '#lib/api.ts';
	import { session } from '#lib/session.svelte.ts';

	let rows = $state<SavedSession[]>([]);
	let error = $state('');
	let loaded = $state(false);

	$effect(() => {
		if (!session.ready || !session.token) return;
		const token = session.token;
		listSessions(token)
			.then((sessions) => {
				rows = sessions;
				error = '';
			})
			.catch((reason) => {
				error = reason instanceof Error ? reason.message : '기록을 불러오지 못했습니다';
			})
			.finally(() => {
				loaded = true;
			});
	});

	function sum(row: SavedSession) {
		return row.recommendations.reduce((total, item) => total + item.price, 0);
	}
</script>

<svelte:head>
	<title>기록 — PCForge</title>
</svelte:head>

<header class="page-head">
	<p class="eyebrow">지난 호</p>
	<h1>남긴 추천</h1>
	<p class="lead">회원으로 받은 추천은 구성과 설명까지 이곳에 쌓입니다.</p>
</header>

{#if !session.ready || (session.user && !loaded)}
	<div class="loading-card"><span class="spinner" aria-hidden="true"></span><strong>기록을 확인하는 중입니다</strong></div>
{:else if !session.user}
	<div class="placeholder">
		<p>기록은 로그인한 뒤에 남습니다. 비로그인 추천은 이 페이지에 쌓이지 않습니다.</p>
		<a class="btn primary" href="/login">로그인</a>
	</div>
{:else if error}
	<p class="note warn" role="alert">{error}</p>
{:else if rows.length === 0}
	<div class="placeholder">
		<p>아직 남긴 추천이 없습니다. 이번 호에서 목록을 담고 추천을 누르면 여기에 쌓입니다.</p>
		<a class="btn primary" href="/#desk">목록 펼치기</a>
	</div>
{:else}
	<div class="history">
		{#each rows as row (row.id)}
			<article class="entry">
				<header>
					<p class="eyebrow">{row.created_at.slice(0, 16).replace('T', ' ')}</p>
					<h2>{row.purpose} <span>· 예산 {row.budget_krw.toLocaleString('ko-KR')}원</span></h2>
					<p class="entry-sum">{row.recommendations.length}개 · 합계 {sum(row).toLocaleString('ko-KR')}원</p>
				</header>
				{#if row.explanation}
					<p class="entry-text">{row.explanation.replace(/\*\*/g, '').slice(0, 260)}{row.explanation.length > 260 ? '…' : ''}</p>
				{/if}
				<ul class="entry-list">
					{#each row.recommendations as item, index (`${row.id}-${index}`)}
						<li><span>{item.product_name}</span><span class="quiet">{item.site}</span><span class="num">{item.price.toLocaleString('ko-KR')}원</span></li>
					{/each}
				</ul>
			</article>
		{/each}
	</div>
{/if}

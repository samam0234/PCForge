<script lang="ts">
	import favicon from '#lib/assets/favicon.svg';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import type { LayoutProps } from './$types';
	import '../app.css';
	import { session, restore, signOut } from '#lib/session.svelte.ts';

	let { children }: LayoutProps = $props();
	const path = $derived(page.url.pathname);

	onMount(() => {
		restore();
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="paper">
	<div class="ticker">
		<div class="wrap">
			<span>VOL. 01 · 2026년 11월호</span>
			<span class="hide-sm">신품과 중고 · 판매 페이지 링크</span>
			<span>
				{#if !session.ready}확인 중{:else if session.user}{session.user.name} 님의 회원 지면{:else}비로그인 열람{/if}
			</span>
		</div>
	</div>

	<header class="masthead">
		<div class="wrap masthead-inner">
			<a class="logo" href="/">PC<span>Forge</span></a>
			<p class="tagline">고르기 전에 시장을 길게 펼치는<br />PC 부품 일지</p>
		</div>
	</header>

	<nav class="menubar" aria-label="주 메뉴">
		<div class="wrap menubar-inner">
			<div class="menu">
				<a href="/" aria-current={path === '/' ? 'page' : undefined}>이번 호</a>
				<a href="/#desk">지면</a>
				<a href="/assistant" aria-current={path === '/assistant' ? 'page' : undefined}>상담</a>
				<a href="/journal" aria-current={path.startsWith('/journal') ? 'page' : undefined}>조립 노트</a>
				<a href="/history" aria-current={path === '/history' ? 'page' : undefined}>기록</a>
			</div>
			<div class="account">
				{#if !session.ready}
					<span class="quiet">확인 중</span>
				{:else if session.user}
					<span class="avatar" aria-hidden="true">{session.user.name.slice(0, 1)}</span>
					<span class="hide-sm">{session.user.name}</span>
					<button type="button" class="btn ghost sm" onclick={() => signOut()}>로그아웃</button>
				{:else}
					<a class="btn primary sm" href="/login" aria-current={path === '/login' ? 'page' : undefined}>로그인</a>
				{/if}
			</div>
		</div>
	</nav>

	<main class="wrap sheet">
		{@render children()}
	</main>

	<footer class="colophon">
		<div class="wrap colophon-grid">
			<div>
				<p class="logo small">PC<span>Forge</span></p>
				<p>용도와 예산을 먼저 정하고, 목록을 넓게 본 뒤에 고릅니다.</p>
			</div>
			<div>
				<p class="eyebrow light">가격에 대하여</p>
				<p>'판매중'은 판매 페이지에서 재고를 확인한 매물입니다. 단종, 판매중단, 판매완료로 확인되면 흐리게 빼고 추천에도 넣지 않습니다. '실시간'은 네이버 쇼핑 검색이고, 그 밖의 가격은 2026-11-01 기준 시세입니다. 1,000만 원 넘는 매물은 예산의 '전체'나 '1000만 이상'으로 봅니다. 쿠폰과 배송비는 판매처에서 확인하세요.</p>
			</div>
			<div>
				<p class="eyebrow light">추천에 대하여</p>
				<p>로컬 언어 모델이 담아 둔 목록과 호환 메모만 보고 씁니다. 구매 전에 판매처에서 한 번 더 확인하세요.</p>
			</div>
		</div>
	</footer>
</div>

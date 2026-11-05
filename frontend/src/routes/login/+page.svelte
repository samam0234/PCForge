<script lang="ts">
	import { goto } from '$app/navigation';
	import { login, register } from '#lib/api.ts';
	import { session, signIn } from '#lib/session.svelte.ts';

	let mode = $state<'login' | 'register'>('login');
	let email = $state('');
	let password = $state('');
	let name = $state('');
	let error = $state('');
	let pending = $state(false);

	$effect(() => {
		if (session.user) goto('/');
	});

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		pending = true;
		error = '';
		try {
			const result =
				mode === 'register'
					? await register(email, password, name)
					: await login(email, password);
			signIn(result.token, result.user);
			await goto('/');
		} catch (reason) {
			error = reason instanceof Error ? reason.message : '로그인하지 못했습니다';
		} finally {
			pending = false;
		}
	}
</script>

<svelte:head>
	<title>{mode === 'login' ? '로그인' : '가입'} — PCForge</title>
</svelte:head>

<div class="auth">
	<section class="auth-pitch">
		<p class="eyebrow light">회원 지면</p>
		<h1>더 넓게 고르고,<br />고른 것을 남깁니다</h1>
		<table class="compare">
			<thead><tr><th></th><th>비로그인</th><th>회원</th></tr></thead>
			<tbody>
				<tr><td>필터</td><td>11칸</td><td>15칸 전부</td></tr>
				<tr><td>한 쪽에 펼치는 매물</td><td>48개</td><td>96개</td></tr>
				<tr><td>담아 두는 목록</td><td>30개</td><td>120개</td></tr>
				<tr><td>추천 구성</td><td>6개</td><td>12개</td></tr>
				<tr><td>메모·우선순위</td><td>—</td><td>반영</td></tr>
				<tr><td>추천 기록</td><td>—</td><td>저장</td></tr>
			</tbody>
		</table>
	</section>

	<section class="auth-card">
		<div class="tabs" role="tablist">
			<button type="button" role="tab" aria-selected={mode === 'login'} class:on={mode === 'login'} onclick={() => (mode = 'login')}>로그인</button>
			<button type="button" role="tab" aria-selected={mode === 'register'} class:on={mode === 'register'} onclick={() => (mode = 'register')}>가입</button>
		</div>
		<h2>{mode === 'login' ? '다시 오셨군요' : '처음 오셨군요'}</h2>
		<p class="quiet">로그인하지 않아도 목록과 추천은 열려 있습니다.</p>
		<form class="auth-form" onsubmit={submit}>
			{#if mode === 'register'}
				<label class="field">
					<span class="field-label">이름</span>
					<input bind:value={name} required maxlength="40" autocomplete="nickname" />
				</label>
			{/if}
			<label class="field">
				<span class="field-label">이메일</span>
				<input type="email" bind:value={email} required autocomplete="email" placeholder="you@example.com" />
			</label>
			<label class="field">
				<span class="field-label">비밀번호 <small class="quiet">8자 이상</small></span>
				<input
					type="password"
					bind:value={password}
					required
					minlength="8"
					autocomplete={mode === 'register' ? 'new-password' : 'current-password'}
				/>
			</label>
			{#if error}<p class="note warn" role="alert">{error}</p>{/if}
			<button type="submit" class="btn primary block" disabled={pending}>
				{pending ? '확인 중…' : mode === 'login' ? '들어가기' : '가입하고 들어가기'}
			</button>
		</form>
	</section>
</div>

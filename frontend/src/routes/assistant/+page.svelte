<script lang="ts">
	import { onDestroy, tick } from 'svelte';
	import { streamChat, type ChatEvent, type ChatPart, type ChatTurn } from '#lib/api.ts';
	import { session } from '#lib/session.svelte.ts';

	interface ToolStep {
		label: string;
		summary: string;
	}

	interface Turn {
		role: 'user' | 'assistant';
		content: string;
		tools: ToolStep[];
		parts: ChatPart[];
		warnings: string[];
		model: string;
		failed: boolean;
		stopped: boolean;
	}

	const MAX_QUESTION = 1000;
	const EXAMPLES = [
		'150만원으로 게이밍 PC 맞춰 줘',
		'AM5 메인보드에 DDR4 메모리를 쓸 수 있어?',
		'RTX 4070 SUPER 중고 매물을 싼 순으로 찾아 줘',
		'7800X3D에 맞는 메인보드를 찾아서 호환을 검사해 줘'
	];

	let turns = $state<Turn[]>([]);
	let question = $state('');
	let running = $state(false);
	let restoredKey = $state<string | null>(null);
	let controller: AbortController | null = null;

	const storageKey = $derived(session.ready ? `pcforge.chat.${session.user?.id ?? 'guest'}` : null);
	const current = $derived(running ? turns[turns.length - 1] : null);

	// 대화는 서버에 저장하지 않고, 이 탭이 열려 있는 동안만 브라우저에 둔다.
	$effect(() => {
		if (!storageKey || storageKey === restoredKey) return;
		controller?.abort();
		restoredKey = storageKey;
		try {
			const raw = sessionStorage.getItem(storageKey);
			turns = raw ? (JSON.parse(raw) as Turn[]) : [];
		} catch {
			turns = [];
		}
	});

	function save() {
		if (!restoredKey) return;
		try {
			sessionStorage.setItem(restoredKey, JSON.stringify(turns));
		} catch {
			// 저장하지 못해도 대화는 이어 간다.
		}
	}

	function newTurn(role: Turn['role'], content: string): Turn {
		return { role, content, tools: [], parts: [], warnings: [], model: '', failed: false, stopped: false };
	}

	/** 화면 맨 아래를 보고 있을 때만 따라 내려간다. 위 내용을 읽는 중이면 두지 않는다. */
	async function follow() {
		const atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 220;
		await tick();
		if (atBottom) window.scrollTo({ top: document.documentElement.scrollHeight });
	}

	function apply(event: ChatEvent, turn: Turn) {
		switch (event.type) {
			case 'start':
				turn.model = event.model;
				break;
			case 'tool':
				// 도구를 부르기 전에 쓴 글은 중간 메모이므로 최종 답변에서 뺀다.
				turn.content = '';
				turn.tools.push({ label: event.label, summary: '' });
				break;
			case 'tool_result': {
				const step = turn.tools[turn.tools.length - 1];
				if (step) step.summary = event.summary;
				break;
			}
			case 'token':
				turn.content += event.text;
				break;
			case 'done':
				turn.content = event.answer;
				turn.parts = event.parts;
				turn.warnings = event.warnings;
				turn.model = event.model;
				break;
			case 'error':
				turn.content = event.message;
				turn.failed = true;
				break;
		}
	}

	function history(): ChatTurn[] {
		return turns
			.filter((turn) => !turn.failed && turn.content.trim())
			.map((turn) => ({ role: turn.role, content: turn.content }));
	}

	async function ask(text: string) {
		const content = text.trim();
		if (!content || running || content.length > MAX_QUESTION) return;
		question = '';
		running = true;
		turns.push(newTurn('user', content));
		const messages = history();
		turns.push(newTurn('assistant', ''));
		const turn = turns[turns.length - 1];
		const active = new AbortController();
		controller = active;
		await follow();
		try {
			await streamChat(
				messages,
				session.token,
				(event) => {
					apply(event, turn);
					follow();
				},
				active.signal
			);
			if (!turn.content.trim()) {
				turn.content = '응답이 끊겼습니다. 다시 물어봐 주세요.';
				turn.failed = true;
			}
		} catch (reason) {
			if (active.signal.aborted) {
				turn.stopped = true;
				if (!turn.content.trim()) turn.failed = true;
				if (turn.failed) turn.content = '답변을 멈췄습니다.';
			} else {
				turn.content = reason instanceof Error ? reason.message : '상담 응답을 받지 못했습니다';
				turn.failed = true;
			}
		} finally {
			if (controller === active) {
				controller = null;
				running = false;
			}
			save();
			await follow();
		}
	}

	function submit(event: SubmitEvent) {
		event.preventDefault();
		ask(question);
	}

	function onKeydown(event: KeyboardEvent) {
		// 한글 조합 중의 Enter는 글자를 확정할 뿐이므로 보내지 않는다.
		if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
			event.preventDefault();
			ask(question);
		}
	}

	function clear() {
		controller?.abort();
		turns = [];
		save();
	}

	// 모델이 표시를 넣어도 글로 읽히게 강조와 제목 기호만 뺀다. 내용은 텍스트로만 그린다.
	function plain(text: string) {
		return text.replace(/\*\*/g, '').replace(/^#+\s*/gm, '').trim();
	}

	onDestroy(() => controller?.abort());
</script>

<svelte:head>
	<title>편집자에게 묻기 — PCForge</title>
</svelte:head>

<header class="page-head center">
	<p class="eyebrow">상담 데스크</p>
	<h1>편집자에게 묻기</h1>
	<p class="lead">
		로컬 언어 모델이 카탈로그와 호환 메모를 직접 찾아보고 답합니다.
		{#if session.ready && !session.user}비로그인 구성은 핵심 부품 6개까지입니다.{/if}
	</p>
</header>

<section class="chat" aria-label="상담">
	{#if turns.length === 0}
		<div class="placeholder">
			<p>용도와 예산, 맞는지 궁금한 부품을 그대로 적어 보세요.</p>
			<div class="chat-start">
				{#each EXAMPLES as example (example)}
					<button type="button" class="chip" disabled={running} onclick={() => ask(example)}>{example}</button>
				{/each}
			</div>
		</div>
	{/if}

	<div class="chat-log" aria-live="polite">
		{#each turns as turn, index (index)}
			<article class="chat-turn {turn.role}" class:failed={turn.failed}>
				{#if turn.tools.length}
					<ul class="chat-tools" aria-label="찾아본 것">
						{#each turn.tools as step, stepIndex (stepIndex)}
							<li class:busy={!step.summary}>{step.label}{step.summary ? ` · ${step.summary}` : ' 중'}</li>
						{/each}
					</ul>
				{/if}

				{#if turn.content}
					<div class="chat-bubble" role={turn.failed ? 'alert' : undefined}>{plain(turn.content)}</div>
				{:else if current === turn}
					<p class="chat-wait"><span class="spinner" aria-hidden="true"></span>로컬 모델이 읽고 있습니다. 처음 깨울 때는 20초 남짓 걸립니다.</p>
				{/if}

				{#if turn.parts.length}
					<table class="chat-parts">
						<tbody>
							{#each turn.parts as part (part.id)}
								<tr>
									<td>
										<span class="kind">{part.category} · {part.shop} · {part.condition} {part.grade}</span>
										{#if part.url}
											<a class="product-link" href={part.url} target="_blank" rel="noopener noreferrer"><strong>{part.name}</strong></a>
										{:else}
											<strong>{part.name}</strong>
										{/if}
									</td>
									<td class="num">
										{part.price.toLocaleString('ko-KR')}원
										<span class="kind">{part.price_kind}</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				{/if}

				{#each turn.warnings as warning, warningIndex (warningIndex)}
					<p class="note warn">{warning}</p>
				{/each}

				{#if turn.stopped && !turn.failed}
					<p class="chat-meta">답변을 중간에 멈췄습니다.</p>
				{:else if turn.role === 'assistant' && turn.model && !turn.failed && current !== turn}
					<p class="chat-meta">{turn.model} · 구매 전에 판매처에서 가격과 규격을 다시 확인하세요.</p>
				{/if}
			</article>
		{/each}
	</div>

	<form class="chat-form" onsubmit={submit}>
		<textarea
			aria-label="질문"
			bind:value={question}
			onkeydown={onKeydown}
			maxlength={MAX_QUESTION}
			placeholder="예: 200만원으로 영상편집 PC를 조용하게 맞춰 줘"
		></textarea>
		<div class="chat-actions">
			<span class="chat-meta">Enter로 보내고 Shift+Enter로 줄을 바꿉니다.</span>
			<div>
				{#if turns.length}
					<button type="button" class="btn ghost sm" onclick={clear}>새 상담</button>
				{/if}
				{#if running}
					<button type="button" class="btn ghost sm" onclick={() => controller?.abort()}>멈추기</button>
				{:else}
					<button type="submit" class="btn primary sm" disabled={!question.trim()}>보내기</button>
				{/if}
			</div>
		</div>
	</form>
</section>

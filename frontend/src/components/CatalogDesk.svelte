<script lang="ts">
	import { onMount } from 'svelte';
	import {
		fetchCatalog,
		type CatalogFilters,
		type CatalogItem,
		type CatalogResponse,
		type RecommendRequest
	} from '#lib/api.ts';
	import { session } from '#lib/session.svelte.ts';

	let {
		disabled = false,
		onrecommend
	}: {
		disabled?: boolean;
		onrecommend: (requirements: RecommendRequest) => void;
	} = $props();

	const FIELDS = [
		{ key: 'purpose', label: '용도' },
		{ key: 'price_max', label: '예산' },
		{ key: 'condition', label: '신품/중고' },
		{ key: 'category', label: '부품 분류' },
		{ key: 'brand', label: '브랜드' },
		{ key: 'model', label: '모델' },
		{ key: 'part_name', label: '부품명' },
		{ key: 'material', label: '소재' },
		{ key: 'form_factor', label: '폼팩터' },
		{ key: 'socket', label: '소켓' },
		{ key: 'shop', label: '쇼핑몰' },
		{ key: 'color', label: '색상' },
		{ key: 'noise', label: '소음' },
		{ key: 'power', label: '전력' },
		{ key: 'grade', label: '상태 등급' }
	] as const;

	type FieldKey = (typeof FIELDS)[number]['key'];

	const GROUPS: { title: string; note: string; keys: FieldKey[] }[] = [
		{ title: '목적과 예산', note: '추천의 기준', keys: ['purpose', 'price_max', 'condition'] },
		{
			title: '부품',
			note: '모델·소재는 회원',
			keys: ['category', 'brand', 'model', 'part_name', 'material', 'form_factor', 'socket']
		},
		{ title: '구매처와 상태', note: '색·소음은 회원', keys: ['shop', 'grade', 'color', 'noise', 'power'] }
	];
	const LABEL = Object.fromEntries(FIELDS.map((field) => [field.key, field.label])) as Record<FieldKey, string>;
	const BUDGETS = [1_000_000, 1_500_000, 2_000_000, 3_000_000];
	const PRIORITIES = ['가격', '성능', '소음', '전력'];
	const SHORTLIST_KEY = 'pcforge.shortlist';
	const LOCKED = ['model', 'material', 'color', 'noise'];
	const TONES: Record<string, string> = {
		CPU: '#a3341f',
		메인보드: '#2f5d50',
		메모리: '#6b4f9b',
		GPU: '#1f4e8c',
		SSD: '#8a6a1f',
		HDD: '#6d655a',
		파워: '#9b5b1f',
		케이스: '#3c3a36',
		쿨러: '#2a7a8c',
		모니터: '#7a2f5d',
		키보드: '#55606b',
		마우스: '#55606b',
		케이스팬: '#2a7a8c'
	};

	let filters = $state<CatalogFilters>({
		part_name: '',
		purpose: '',
		price_max: '2000000',
		condition: '',
		category: '',
		brand: '',
		model: '',
		material: '',
		form_factor: '',
		socket: '',
		shop: '',
		color: '',
		noise: '',
		power: '',
		grade: '',
		source: '',
		offset: 0
	});
	const SOURCES = [
		{ value: '', label: '전체' },
		{ value: 'naver', label: '실시간 매물' },
		{ value: 'reference', label: '기준 시세' }
	] as const;
	let unlimited = $state(false);
	let notes = $state('');
	let priorities = $state<string[]>([]);
	let shortlist = $state<CatalogItem[]>([]);
	let listReady = $state(false);
	let catalog = $state<CatalogResponse | null>(null);
	let loading = $state(false);
	let localError = $state('');
	let requestId = 0;

	const browser = typeof window !== 'undefined';
	const member = $derived(Boolean(session.user));
	const limit = $derived(catalog?.shortlist_limit ?? (member ? 120 : 30));
	const totalPrice = $derived(shortlist.reduce((sum, item) => sum + item.price, 0));
	const budget = $derived(Number(filters.price_max) || 0);
	const usage = $derived(budget > 0 ? Math.min(100, (totalPrice / budget) * 100) : 0);
	const over = $derived(budget > 0 && totalPrice > budget);
	const active = $derived(
		FIELDS.filter((field) => field.key !== 'price_max' && filters[field.key]).map((field) => ({
			key: field.key,
			label: field.label,
			value: optionLabel(field.key, filters[field.key])
		}))
	);
	const page = $derived(catalog ? Math.floor(catalog.offset / catalog.limit) + 1 : 1);
	const pages = $derived(catalog ? Math.max(1, Math.ceil(catalog.total / catalog.limit)) : 1);

	onMount(() => {
		try {
			const raw = sessionStorage.getItem(SHORTLIST_KEY);
			if (raw) shortlist = JSON.parse(raw) as CatalogItem[];
		} catch {
			shortlist = [];
		}
		listReady = true;
	});

	$effect(() => {
		if (!browser || !listReady) return;
		sessionStorage.setItem(SHORTLIST_KEY, JSON.stringify(shortlist));
	});

	$effect(() => {
		const cap = catalog?.shortlist_limit;
		if (!cap || shortlist.length <= cap) return;
		shortlist = shortlist.slice(0, cap);
	});

	$effect(() => {
		if (!browser || !session.ready) return;
		const token = session.token;
		const snapshot: CatalogFilters = { ...filters };
		const openBudget = member && unlimited;
		const handle = setTimeout(() => {
			void load(snapshot, token, openBudget);
		}, 160);
		return () => clearTimeout(handle);
	});

	async function load(snapshot: CatalogFilters, token: string | null, openBudget: boolean) {
		const id = ++requestId;
		loading = true;
		try {
			const data = await fetchCatalog(snapshot, token, openBudget);
			if (id !== requestId) return;
			catalog = data;
			localError = '';
		} catch (error) {
			if (id !== requestId) return;
			localError = error instanceof Error ? error.message : '목록을 불러오지 못했습니다';
		} finally {
			if (id === requestId) loading = false;
		}
	}

	function won(value: number) {
		return value.toLocaleString('ko-KR');
	}

	function stamp(iso: string) {
		const date = new Date(iso);
		if (Number.isNaN(date.getTime())) return iso;
		return date.toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
	}

	function isLocked(key: string) {
		if (member) return false;
		return (catalog?.locked_filters ?? LOCKED).includes(key);
	}

	function setFilter(key: FieldKey, value: string) {
		filters[key] = value;
		filters.offset = 0;
	}

	function clearFilters() {
		for (const field of FIELDS) {
			if (field.key !== 'price_max') filters[field.key] = '';
		}
		filters.source = '';
		filters.offset = 0;
	}

	function optionLabel(field: string, value: string) {
		if (field === 'condition') return value === 'new' ? '신품' : value === 'used' ? '중고' : value;
		return value;
	}

	function specChips(item: CatalogItem) {
		const chips: string[] = [];
		if (item.socket && item.socket !== '없음') chips.push(item.socket);
		const specs = item.specs;
		if (specs.memory) chips.push(specs.memory);
		if (specs.chipset) chips.push(specs.chipset);
		if (specs.cores) chips.push(`${specs.cores}코어`);
		if (specs.vram) chips.push(`VRAM ${specs.vram}`);
		if (specs.capacity) chips.push(specs.capacity);
		if (specs.watt) chips.push(`${specs.watt}W`);
		if (specs.tdp_w) chips.push(`TDP ${specs.tdp_w}W`);
		if (item.form_factor && chips.length < 3) chips.push(item.form_factor);
		return chips.slice(0, 4);
	}

	function inList(item: CatalogItem) {
		return shortlist.some((row) => row.id === item.id);
	}

	function stale(item: CatalogItem) {
		return item.availability === 'discontinued' || item.availability === 'sold' || item.availability === 'upcoming' || item.availability === 'unverified';
	}

	function offerable(item: CatalogItem) {
		if (stale(item)) return false;
		if (item.source === 'naver') return item.availability === 'selling' && Boolean(item.url);
		return true;
	}

	function closedLabel(item: CatalogItem) {
		if (item.availability === 'sold') return '판매완료';
		if (item.availability === 'upcoming') return '판매예정';
		if (item.availability === 'unverified') return '링크 없음';
		return '단종';
	}

	function add(item: CatalogItem) {
		if (!offerable(item) && !inList(item)) return;
		if (inList(item)) {
			shortlist = shortlist.filter((row) => row.id !== item.id);
			return;
		}
		if (shortlist.length >= limit) {
			localError = `지금은 ${limit}개까지 담을 수 있습니다.`;
			return;
		}
		shortlist = [...shortlist, item];
		localError = '';
	}

	function addPage() {
		if (!catalog || !member) return;
		const next = [...shortlist];
		for (const item of catalog.items) {
			if (next.length >= catalog.shortlist_limit) break;
			if (!offerable(item) || next.some((row) => row.id === item.id)) continue;
			next.push(item);
		}
		shortlist = next;
	}

	function togglePriority(priority: string) {
		if (!member) return;
		priorities = priorities.includes(priority)
			? priorities.filter((item) => item !== priority)
			: [...priorities, priority];
	}

	function movePage(step: number) {
		if (!catalog) return;
		filters.offset = Math.max(0, filters.offset + step * catalog.limit);
		document.getElementById('desk')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	function recommend() {
		if (!filters.purpose) {
			localError = '추천을 받으려면 용도를 고르세요. 목록은 용도를 비운 채로 넓게 볼 수 있습니다.';
			return;
		}
		if (!Number.isFinite(budget) || budget <= 0) {
			localError = '예산은 1원 이상이어야 합니다.';
			return;
		}
		const selected = shortlist.filter(offerable).slice(0, limit);
		const body: RecommendRequest = {
			purpose: filters.purpose,
			budget_krw: budget,
			condition: filters.condition === 'new' || filters.condition === 'used' ? filters.condition : 'mixed',
			selected_ids: selected.map((item) => item.id),
			notes: member ? notes : '',
			priorities: member ? priorities : []
		};
		if (selected.length === 0) {
			const keys = [
				'part_name',
				'category',
				'brand',
				'model',
				'material',
				'shop',
				'form_factor',
				'socket',
				'color',
				'noise',
				'power',
				'grade'
			] as const;
			for (const key of keys) {
				if (filters[key]) body[key] = filters[key];
			}
		}
		localError = '';
		onrecommend(body);
	}
</script>

<section class="desk" id="desk">
	<header class="section-head">
		<div>
			<p class="eyebrow">이번 호 지면</p>
			<h2>부품 목록을 펼칩니다</h2>
		</div>
		<dl class="stats">
			<div><dt>조건에 맞는 매물</dt><dd>{catalog ? won(catalog.total) : '—'}</dd></div>
			<div><dt>쇼핑몰</dt><dd>{catalog?.facets.shop?.length ?? '—'}</dd></div>
			<div><dt>부품 분류</dt><dd>{catalog?.facets.category?.length ?? '—'}</dd></div>
			{#if catalog?.live_count}
				<div><dt>실시간 갱신</dt><dd>{stamp(catalog.live_fetched_at)}</dd></div>
			{:else}
				<div><dt>기준 시세</dt><dd>{catalog?.snapshot ?? '—'}</dd></div>
			{/if}
		</dl>
	</header>

	<div class="spread">
		<aside class="filters" aria-label="필터">
			<div class="filters-head">
				<h3>고르는 칸 <span>15</span></h3>
				{#if active.length}
					<button type="button" class="link" onclick={clearFilters}>모두 지우기</button>
				{/if}
			</div>

			{#each GROUPS as group (group.title)}
				<fieldset class="group">
					<legend><span>{group.title}</span><small>{group.note}</small></legend>
					{#each group.keys as key (key)}
						{@const locked = isLocked(key)}
						<label class="field" class:locked>
							<span class="field-label">
								{LABEL[key]}
								{#if locked}<em class="badge">회원</em>{/if}
							</span>
							{#if key === 'part_name'}
								<input
									type="search"
									placeholder="예: 4070, 990 PRO"
									value={filters.part_name}
									oninput={(event) => setFilter('part_name', event.currentTarget.value)}
								/>
							{:else if key === 'price_max'}
								<div class="money">
									<input
										type="number"
										min="1"
										step="10000"
										value={filters.price_max}
										oninput={(event) => setFilter('price_max', event.currentTarget.value)}
									/>
									<span>원</span>
								</div>
								<div class="presets">
									{#each BUDGETS as preset (preset)}
										<button
											type="button"
											class="chip"
											class:on={budget === preset}
											onclick={() => setFilter('price_max', String(preset))}
										>{preset / 10_000}만</button>
									{/each}
								</div>
							{:else}
								<select
									value={filters[key]}
									disabled={locked}
									onchange={(event) => setFilter(key, event.currentTarget.value)}
								>
									<option value="">전체</option>
									{#each catalog?.facets[key] ?? [] as facet (facet.value)}
										<option value={facet.value}>{optionLabel(key, facet.value)} · {facet.count}</option>
									{/each}
								</select>
							{/if}
						</label>
					{/each}
				</fieldset>
			{/each}

			<fieldset class="group member" class:locked={!member}>
				<legend><span>회원 칸</span><small>{member ? '열림' : '로그인 필요'}</small></legend>
				<label class="switch">
					<input
						type="checkbox"
						checked={unlimited}
						disabled={!member}
						onchange={(event) => {
							unlimited = event.currentTarget.checked;
							filters.offset = 0;
						}}
					/>
					<span class="track" aria-hidden="true"></span>
					<span>목록에서 예산 상한 풀기</span>
				</label>
				<p class="field-label">우선순위</p>
				<div class="presets">
					{#each PRIORITIES as priority (priority)}
						<button
							type="button"
							class="chip"
							class:on={priorities.includes(priority)}
							aria-pressed={priorities.includes(priority)}
							disabled={!member}
							onclick={() => togglePriority(priority)}
						>{priority}</button>
					{/each}
				</div>
				<label class="field">
					<span class="field-label">메모</span>
					<textarea bind:value={notes} disabled={!member} placeholder="소음이 적고, 화이트 위주로"></textarea>
				</label>
				{#if !member}
					<a class="unlock" href="/login">로그인하고 모델·소재·색·소음 열기 →</a>
				{/if}
			</fieldset>
		</aside>

		<section class="board" aria-live="polite">
			<div class="board-bar">
				<p class="count">
					{#if catalog}
						<strong>{won(catalog.total)}</strong>개 중 {catalog.items.length}개 · {page}/{pages}쪽
					{:else}
						목록을 펼치는 중입니다
					{/if}
				</p>
				<div class="pager">
					<button type="button" class="icon" aria-label="이전 쪽" disabled={!catalog || filters.offset === 0} onclick={() => movePage(-1)}>←</button>
					<button
						type="button"
						class="icon"
						aria-label="다음 쪽"
						disabled={!catalog || filters.offset + catalog.limit >= catalog.total}
						onclick={() => movePage(1)}>→</button>
				</div>
			</div>

			<div class="sources" role="group" aria-label="매물 출처">
				{#each SOURCES as option (option.value)}
					<button
						type="button"
						class="chip"
						class:on={filters.source === option.value}
						aria-pressed={filters.source === option.value}
						disabled={option.value === 'naver' && !catalog?.live_count}
						onclick={() => {
							filters.source = option.value;
							filters.offset = 0;
						}}
					>{option.label}</button>
				{/each}
				<span class="quiet">
					{#if catalog?.live_count}
						네이버 쇼핑 검색 {won(catalog.live_count)}건 · {stamp(catalog.live_fetched_at)} 기준
					{:else}
						실시간 매물은 아직 수집되지 않았습니다
					{/if}
				</span>
			</div>

			{#if active.length}
				<ul class="active">
					{#each active as chip (chip.key)}
						<li>
							<button type="button" class="chip on" onclick={() => setFilter(chip.key, '')}>
								<span class="quiet">{chip.label}</span> {chip.value} <span aria-hidden="true">×</span>
							</button>
						</li>
					{/each}
				</ul>
			{/if}

			{#if localError}<p class="note warn" role="alert">{localError}</p>{/if}

			<div class="cards" class:dim={loading && catalog}>
				{#if !catalog}
					{#each Array(6) as _, index (index)}
						<div class="card skeleton" aria-hidden="true"></div>
					{/each}
				{:else if catalog.items.length === 0}
					<p class="empty">조건에 맞는 매물이 없습니다. 칸을 하나씩 풀어 보세요.</p>
				{:else}
					{#each catalog.items as item (item.id)}
						<article class="card" class:picked={inList(item)} class:stale={stale(item)} style={`--tone:${TONES[item.category] ?? '#3c3a36'}`}>
							<header class="card-top">
								<span class="cat">{item.category}</span>
								{#if stale(item)}
									<span class="closed">{closedLabel(item)}</span>
								{:else if item.source === 'naver'}
									<span class="live">실시간</span>
								{/if}
								<span class="pill" class:used={item.condition === 'used'}>
									{item.condition === 'used' ? '중고' : '신품'} · {item.grade}
								</span>
							</header>
							{#if item.image}
								<img class="thumb" src={item.image} alt="" loading="lazy" referrerpolicy="no-referrer" />
							{/if}
							<h3>{item.name}</h3>
							<p class="card-meta">{item.brand} · {item.material} · {item.color}</p>
							<ul class="specs">
								{#each specChips(item) as chip (chip)}<li>{chip}</li>{/each}
							</ul>
							<footer class="card-foot">
								<div>
									<p class="price">{won(item.price)}<small>원</small></p>
									<p class="shop">{item.shop}</p>
									{#if offerable(item) && item.url}
										<a class="proof" href={item.url} target="_blank" rel="noopener noreferrer">판매 페이지 증거 ↗</a>
									{:else if stale(item)}
										<p class="proof dead">추천에서 제외</p>
										{#if item.url}
											<a class="proof dead" href={item.url} target="_blank" rel="noopener noreferrer">이전 페이지 ↗</a>
										{/if}
									{/if}
								</div>
								<button
									type="button"
									class="add"
									class:on={inList(item)}
									aria-pressed={inList(item)}
									disabled={stale(item) && !inList(item)}
									onclick={() => add(item)}
								>{stale(item) ? '제외' : inList(item) ? '담김' : '담기'}</button>
							</footer>
						</article>
					{/each}
				{/if}
			</div>

			{#if catalog && pages > 1}
				<div class="pager bottom">
					<button type="button" class="btn ghost" disabled={filters.offset === 0} onclick={() => movePage(-1)}>이전 쪽</button>
					<span class="quiet">{page} / {pages}</span>
					<button
						type="button"
						class="btn ghost"
						disabled={filters.offset + catalog.limit >= catalog.total}
						onclick={() => movePage(1)}>다음 쪽</button>
				</div>
			{/if}
		</section>

		<aside class="tray" aria-label="담아 둔 목록">
			<div class="tray-head">
				<p class="eyebrow light">담아 둔 목록</p>
				<p class="tray-count">{shortlist.length}<small> / {limit}</small></p>
			</div>

			<div class="meter" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow={Math.round(usage)} aria-label="예산 사용">
				<div class="meter-bar" class:over style:width={`${usage}%`}></div>
			</div>
			<dl class="tray-sum">
				<div><dt>합계</dt><dd>{won(totalPrice)}원</dd></div>
				<div><dt>예산</dt><dd>{won(budget)}원</dd></div>
				<div class:over><dt>{over ? '초과' : '남음'}</dt><dd>{won(Math.abs(budget - totalPrice))}원</dd></div>
			</dl>

			<div class="tray-actions">
				{#if member}
					<button type="button" class="btn dark" onclick={addPage}>이 쪽 전부 담기</button>
				{/if}
				<button type="button" class="btn dark" onclick={() => (shortlist = [])} disabled={shortlist.length === 0}>비우기</button>
			</div>

			{#if shortlist.length === 0}
				<p class="tray-empty">카드의 <b>담기</b>를 눌러 후보를 모으세요. 비워 두면 지금 고른 칸으로 바로 추천합니다.</p>
			{:else}
				<ol class="tray-list">
					{#each shortlist as item (item.id)}
						<li style={`--tone:${TONES[item.category] ?? '#3c3a36'}`}>
							<div>
								<p class="tray-name">{item.name}</p>
								<p class="tray-meta">{item.category} · {item.shop} · {won(item.price)}원</p>
							</div>
							<button
								type="button"
								class="icon dark"
								aria-label={`${item.name} 빼기`}
								onclick={() => (shortlist = shortlist.filter((row) => row.id !== item.id))}>×</button>
						</li>
					{/each}
				</ol>
			{/if}

			<button type="button" class="btn primary block" onclick={recommend} {disabled}>
				{disabled ? '추천을 만드는 중…' : '이 목록으로 추천받기'}
			</button>
			<p class="tray-foot">
				{member ? '회원 추천은 12개까지, 기록에 남습니다.' : '비로그인 추천은 6개까지입니다.'}
			</p>
		</aside>
	</div>
</section>

import { error } from '@sveltejs/kit';
import { getArticle } from '#lib/journal.ts';

export function load({ params }: { params: { slug: string } }) {
	const article = getArticle(params.slug);
	if (!article) error(404, '글을 찾지 못했습니다');
	return { article };
}

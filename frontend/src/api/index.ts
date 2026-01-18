/**
 * API client for the AI-Readwise backend
 */

const API_BASE = '/api';

export interface Book {
    id: string;
    title: string;
    description: string;
    file: string;
    has_chapters: boolean;
}

export interface Chapter {
    name: string;
    filename: string;
    order: number;
    title?: string;  // Added for translation API
}

export interface ExtractProgress {
    status: 'idle' | 'pending' | 'extracting' | 'extracted' | 'splitting' | 'completed' | 'error' | 'cancelled';
    progress: number;
    message: string;
    current_step?: string;
}

/**
 * Fetch all books
 */
export async function fetchBooks(): Promise<Book[]> {
    const response = await fetch(`${API_BASE}/books`);
    if (!response.ok) {
        throw new Error('Failed to fetch books');
    }
    return response.json();
}

/**
 * Fetch a specific book
 */
export async function fetchBook(bookId: string): Promise<Book> {
    const response = await fetch(`${API_BASE}/books/${bookId}`);
    if (!response.ok) {
        throw new Error('Failed to fetch book');
    }
    return response.json();
}

/**
 * Fetch all chapters of a book
 */
export async function fetchChapters(bookId: string): Promise<Chapter[]> {
    const response = await fetch(`${API_BASE}/books/${bookId}/chapters`);
    if (!response.ok) {
        throw new Error('Failed to fetch chapters');
    }
    return response.json();
}

/**
 * Fetch content of a specific chapter
 */
export async function fetchChapterContent(
    bookId: string,
    chapterFilename: string
): Promise<string> {
    const response = await fetch(
        `${API_BASE}/books/${bookId}/chapters/${encodeURIComponent(chapterFilename)}`
    );
    if (!response.ok) {
        throw new Error('Failed to fetch chapter content');
    }
    const data = await response.json();
    return data.content;
}

/**
 * Extract PDF to markdown chapters with progress callback
 */
export async function extractBook(
    bookId: string,
    onProgress: (progress: ExtractProgress) => void
): Promise<void> {
    const response = await fetch(`${API_BASE}/books/${bookId}/extract`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error('Failed to start extraction');
    }

    const reader = response.body?.getReader();
    if (!reader) {
        throw new Error('No response body');
    }

    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        const lines = text.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') {
                    return;
                }
                try {
                    const progress = JSON.parse(data) as ExtractProgress;
                    onProgress(progress);
                } catch {
                    // Ignore parse errors
                }
            }
        }
    }
}

/**
 * Fetch the source (original) markdown content
 */
export async function fetchSourceMarkdown(bookId: string): Promise<string> {
    const response = await fetch(`${API_BASE}/books/${bookId}/source`);
    if (!response.ok) {
        throw new Error('Failed to fetch source markdown');
    }
    const data = await response.json();
    return data.content;
}

/**
 * Update the source markdown content
 */
export async function updateSourceMarkdown(
    bookId: string,
    content: string
): Promise<void> {
    const response = await fetch(`${API_BASE}/books/${bookId}/source`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
    });
    if (!response.ok) {
        throw new Error('Failed to update source markdown');
    }
}

/**
 * Re-split chapters from the source markdown
 */
export async function resplitChapters(
    bookId: string
): Promise<{ success: boolean; message: string; chapter_count: number }> {
    const response = await fetch(`${API_BASE}/books/${bookId}/resplit`, {
        method: 'POST',
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to re-split chapters');
    }
    return response.json();
}

/**
 * Fetch current extraction status (from persisted progress file)
 */
export async function fetchExtractionStatus(bookId: string): Promise<ExtractProgress> {
    const response = await fetch(`${API_BASE}/books/${bookId}/extract/status`);
    if (!response.ok) {
        throw new Error('Failed to fetch extraction status');
    }
    return response.json();
}

/**
 * Cancel an ongoing extraction
 */
export async function cancelExtraction(bookId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/books/${bookId}/extract/cancel`, {
        method: 'POST',
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to cancel extraction');
    }
}

// ============= Translation API =============

export interface ModelsConfig {
    models: string[];
    default: string;
}

export interface BookLanguages {
    source_lang: 'en' | 'zh';
    available_langs: string[];
    has_translation: {
        en: boolean;
        zh: boolean;
    };
    translation_progress?: {
        en?: number;
        zh?: number;
    };
}

export interface TranslationProgress {
    progress?: number;
    message?: string;
    status?: 'completed' | 'error';
    chapter_count?: number;
}

/**
 * Get available LLM models for translation
 */
export async function getAvailableModels(): Promise<ModelsConfig> {
    const response = await fetch(`${API_BASE}/config/models`);
    if (!response.ok) {
        throw new Error('Failed to fetch models');
    }
    return response.json();
}

/**
 * Get language information for a book
 */
export async function getBookLanguages(bookId: string): Promise<BookLanguages> {
    const response = await fetch(`${API_BASE}/books/${encodeURIComponent(bookId)}/languages`);
    if (!response.ok) {
        throw new Error('Failed to fetch language info');
    }
    return response.json();
}

/**
 * Cancel ongoing translation for a book
 */
export async function cancelTranslation(bookId: string): Promise<void> {
    const response = await fetch(
        `${API_BASE}/books/${encodeURIComponent(bookId)}/translate/cancel`,
        { method: 'POST' }
    );
    if (!response.ok) {
        throw new Error('Failed to cancel translation');
    }
}

/**
 * Translate book with SSE progress updates
 */
export async function translateBook(
    bookId: string,
    targetLang: string,
    model: string,
    onProgress: (progress: TranslationProgress) => void,
    signal?: AbortSignal
): Promise<void> {
    const response = await fetch(
        `${API_BASE}/books/${encodeURIComponent(bookId)}/translate?target_lang=${targetLang}&model=${model}`,
        { method: 'POST', signal }
    );

    if (!response.ok) {
        throw new Error('Failed to start translation');
    }

    const reader = response.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = '';

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        onProgress(data);
                    } catch {
                        // ignore parse errors
                    }
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
}

/**
 * Get chapters for a specific language version
 */
export async function getChaptersForLang(bookId: string, lang: string): Promise<Chapter[]> {
    const response = await fetch(`${API_BASE}/books/${encodeURIComponent(bookId)}/chapters/${lang}`);
    if (!response.ok) {
        throw new Error('Failed to fetch chapters');
    }
    return response.json();
}

/**
 * Get chapter content for a specific language
 */
export async function getChapterContentForLang(
    bookId: string,
    lang: string,
    chapterFilename: string
): Promise<string> {
    const response = await fetch(
        `${API_BASE}/books/${encodeURIComponent(bookId)}/chapters/${lang}/${encodeURIComponent(chapterFilename)}`
    );
    if (!response.ok) {
        throw new Error('Failed to fetch chapter content');
    }
    const data = await response.json();
    return data.content;
}

// ============= Summary API =============

export interface ChapterSummary {
    key_points: string[];
    conclusions: string[];
    examples: string[];
    voice_script: string;
    generated_at?: string;
    edited_at?: string;
    domain?: string;
    model?: string;
    chapter_title?: string;
    error?: string;
}

/**
 * Get existing summary for a chapter
 */
export async function getChapterSummary(
    bookId: string,
    lang: string,
    chapterFilename: string
): Promise<{ summary: ChapterSummary | null; has_mp3: boolean }> {
    const response = await fetch(
        `${API_BASE}/books/${encodeURIComponent(bookId)}/chapters/${lang}/${encodeURIComponent(chapterFilename)}/summary`
    );
    if (!response.ok) {
        throw new Error('Failed to fetch summary');
    }
    const data = await response.json();
    return { summary: data.summary, has_mp3: data.has_mp3 || false };
}

/**
 * Generate a new summary for a chapter
 */
export async function generateChapterSummary(
    bookId: string,
    lang: string,
    chapterFilename: string,
    model?: string
): Promise<ChapterSummary> {
    const url = new URL(`${window.location.origin}${API_BASE}/books/${encodeURIComponent(bookId)}/chapters/${lang}/${encodeURIComponent(chapterFilename)}/summary`);
    if (model) {
        url.searchParams.set('model', model);
    }

    const response = await fetch(url.toString(), {
        method: 'POST',
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate summary');
    }
    const data = await response.json();
    return data.summary;
}

/**
 * Save edited summary for a chapter
 */
export async function saveChapterSummary(
    bookId: string,
    lang: string,
    chapterFilename: string,
    summary: ChapterSummary
): Promise<ChapterSummary> {
    const response = await fetch(
        `${API_BASE}/books/${encodeURIComponent(bookId)}/chapters/${lang}/${encodeURIComponent(chapterFilename)}/summary`,
        {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(summary),
        }
    );
    if (!response.ok) {
        throw new Error('Failed to save summary');
    }
    const data = await response.json();
    return data.summary;
}

/**
 * Generate MP3 from voice script
 */
export async function generateSummaryMp3(
    bookId: string,
    lang: string,
    chapterFilename: string
): Promise<{ success: boolean; has_mp3: boolean }> {
    const response = await fetch(
        `${API_BASE}/books/${encodeURIComponent(bookId)}/chapters/${lang}/${encodeURIComponent(chapterFilename)}/summary/mp3`,
        { method: 'POST' }
    );
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate MP3');
    }
    return response.json();
}

/**
 * Get MP3 URL for voice script
 */
export function getSummaryMp3Url(
    bookId: string,
    lang: string,
    chapterFilename: string
): string {
    return `${API_BASE}/books/${encodeURIComponent(bookId)}/chapters/${lang}/${encodeURIComponent(chapterFilename)}/summary/mp3`;
}

// ============= Batch Summary API =============

export interface ChapterSummaryStatus {
    filename: string;
    title: string;
    has_summary: boolean;
    has_mp3: boolean;
}

export interface AllSummariesStatus {
    chapters: ChapterSummaryStatus[];
    total: number;
    with_summary: number;
    with_mp3: number;
}

export interface BatchProgress {
    type: 'progress' | 'error' | 'complete';
    current?: number;
    total?: number;
    chapter?: string;
    step?: 'summary' | 'mp3';
    message?: string;
    generated_summaries?: number;
    generated_mp3s?: number;
}

/**
 * Get summary/MP3 status for all chapters
 */
export async function getAllSummariesStatus(
    bookId: string,
    lang: string
): Promise<AllSummariesStatus> {
    const response = await fetch(
        `${API_BASE}/books/${encodeURIComponent(bookId)}/summaries/${lang}/status`
    );
    if (!response.ok) {
        throw new Error('Failed to fetch summaries status');
    }
    return response.json();
}

/**
 * Generate all summaries and MP3s with SSE progress
 */
export async function generateAllSummaries(
    bookId: string,
    lang: string,
    onProgress: (progress: BatchProgress) => void,
    signal?: AbortSignal
): Promise<void> {
    const response = await fetch(
        `${API_BASE}/books/${encodeURIComponent(bookId)}/summaries/${lang}/generate-all`,
        { method: 'POST', signal }
    );

    if (!response.ok) {
        throw new Error('Failed to start batch generation');
    }

    const reader = response.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = '';

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6)) as BatchProgress;
                        onProgress(data);
                    } catch {
                        // ignore parse errors
                    }
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
}

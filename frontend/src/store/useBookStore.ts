/**
 * Zustand store for book state management
 */

import { create } from 'zustand';
import type { Book, Chapter, ExtractProgress } from '../api';
import {
    fetchBooks,
    fetchBook,
    fetchChapters,
    fetchChapterContent,
    extractBook,
    fetchExtractionStatus,
    cancelExtraction as apiCancelExtraction,
} from '../api';

interface BookState {
    // Books list
    books: Book[];
    booksLoading: boolean;
    booksError: string | null;

    // Current book
    currentBook: Book | null;
    currentBookLoading: boolean;

    // Chapters
    chapters: Chapter[];
    chaptersLoading: boolean;

    // Current chapter content
    currentChapterFilename: string | null;
    currentChapterContent: string | null;
    chapterContentLoading: boolean;

    // Extraction
    extractProgress: ExtractProgress | null;
    extracting: boolean;

    // Actions
    loadBooks: () => Promise<void>;
    loadBook: (bookId: string) => Promise<void>;
    loadChapters: (bookId: string) => Promise<void>;
    loadChapterContent: (bookId: string, chapterFilename: string) => Promise<void>;
    startExtraction: (bookId: string) => Promise<void>;
    checkExtractionStatus: (bookId: string) => Promise<void>;
    cancelExtraction: (bookId: string) => Promise<void>;
    clearCurrentBook: () => void;
}

export const useBookStore = create<BookState>((set, get) => ({
    // Initial state
    books: [],
    booksLoading: false,
    booksError: null,

    currentBook: null,
    currentBookLoading: false,

    chapters: [],
    chaptersLoading: false,

    currentChapterFilename: null,
    currentChapterContent: null,
    chapterContentLoading: false,

    extractProgress: null,
    extracting: false,

    // Actions
    loadBooks: async () => {
        set({ booksLoading: true, booksError: null });
        try {
            const books = await fetchBooks();
            set({ books, booksLoading: false });
        } catch (error) {
            set({
                booksError: error instanceof Error ? error.message : 'Failed to load books',
                booksLoading: false,
            });
        }
    },

    loadBook: async (bookId: string) => {
        set({ currentBookLoading: true });
        try {
            const book = await fetchBook(bookId);
            set({ currentBook: book, currentBookLoading: false });
        } catch (error) {
            set({ currentBook: null, currentBookLoading: false });
        }
    },

    loadChapters: async (bookId: string) => {
        set({ chaptersLoading: true, chapters: [] });
        try {
            const chapters = await fetchChapters(bookId);
            set({ chapters, chaptersLoading: false });

            // Auto-select first chapter if available
            if (chapters.length > 0 && !get().currentChapterFilename) {
                get().loadChapterContent(bookId, chapters[0].filename);
            }
        } catch (error) {
            set({ chapters: [], chaptersLoading: false });
        }
    },

    loadChapterContent: async (bookId: string, chapterFilename: string) => {
        set({ chapterContentLoading: true, currentChapterFilename: chapterFilename });
        try {
            const content = await fetchChapterContent(bookId, chapterFilename);
            set({ currentChapterContent: content, chapterContentLoading: false });
        } catch (error) {
            set({ currentChapterContent: null, chapterContentLoading: false });
        }
    },

    startExtraction: async (bookId: string) => {
        set({ extracting: true, extractProgress: null });
        try {
            await extractBook(bookId, (progress) => {
                set({ extractProgress: progress });

                // Reload book and chapters when completed
                if (progress.status === 'completed') {
                    get().loadBook(bookId);
                    get().loadChapters(bookId);
                }
            });
        } catch (error) {
            set({
                extractProgress: {
                    status: 'error',
                    progress: 0,
                    message: error instanceof Error ? error.message : 'Extraction failed',
                },
            });
        } finally {
            set({ extracting: false });
        }
    },

    checkExtractionStatus: async (bookId: string) => {
        try {
            const status = await fetchExtractionStatus(bookId);

            // If extraction is in progress, set extracting flag and progress
            if (status.status === 'extracting' || status.status === 'splitting') {
                set({
                    extracting: true,
                    extractProgress: status
                });

                // Start polling for updates
                const pollInterval = setInterval(async () => {
                    try {
                        const newStatus = await fetchExtractionStatus(bookId);
                        set({ extractProgress: newStatus });

                        // Stop polling when done
                        if (newStatus.status === 'completed' ||
                            newStatus.status === 'error' ||
                            newStatus.status === 'cancelled' ||
                            newStatus.status === 'idle') {
                            clearInterval(pollInterval);
                            set({ extracting: false });

                            // Reload book and chapters on completion
                            if (newStatus.status === 'completed') {
                                get().loadBook(bookId);
                                get().loadChapters(bookId);
                            }
                        }
                    } catch {
                        clearInterval(pollInterval);
                        set({ extracting: false });
                    }
                }, 1000);
            } else if (status.status !== 'idle') {
                // Show completed/error/cancelled status
                set({ extractProgress: status });
            }
        } catch (error) {
            // Ignore errors - just means no status available
        }
    },

    cancelExtraction: async (bookId: string) => {
        try {
            await apiCancelExtraction(bookId);
            set({
                extracting: false,
                extractProgress: {
                    status: 'cancelled',
                    progress: 0,
                    message: 'Extraction cancelled',
                    current_step: 'Cancelled'
                }
            });
        } catch (error) {
            console.error('Failed to cancel extraction:', error);
        }
    },

    clearCurrentBook: () => {
        // Don't clear extractProgress if extraction is in progress
        const { extracting } = get();
        set({
            currentBook: null,
            chapters: [],
            currentChapterFilename: null,
            currentChapterContent: null,
            // Keep extractProgress if extracting, otherwise clear it
            extractProgress: extracting ? get().extractProgress : null,
        });
    },
}));

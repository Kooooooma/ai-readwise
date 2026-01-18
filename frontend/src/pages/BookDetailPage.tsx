/**
 * BookDetailPage - displays book chapters with sidebar navigation
 * 
 * Features:
 * - Chapter navigation with source markdown option
 * - Preview/Edit mode for source markdown
 * - Re-split chapters after editing
 * - Progress persistence and cancel support
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout, Typography, Button, Spin, Menu } from 'antd';
import { ArrowLeftOutlined, FileTextOutlined, FileMarkdownOutlined } from '@ant-design/icons';
import MarkdownViewer from '../components/MarkdownViewer';
import ExtractPanel from '../components/ExtractPanel';
import SourceEditor from '../components/SourceEditor';
import LanguageSelector from '../components/LanguageSelector';
import ChapterSummary from '../components/ChapterSummary';
import BatchSummaryPanel from '../components/BatchSummaryPanel';
import { useBookStore } from '../store/useBookStore';
import { getChaptersForLang, getChapterContentForLang } from '../api';

const { Header, Sider, Content } = Layout;

// Special key for source markdown
const SOURCE_KEY = '__SOURCE__';

const BookDetailPage: React.FC = () => {
    const { bookId } = useParams<{ bookId: string }>();
    const navigate = useNavigate();

    // Local state for view mode
    const [viewMode, setViewMode] = useState<'chapter' | 'source'>('chapter');
    // Language state
    const [currentLang, setCurrentLang] = useState<'en' | 'zh'>('en');
    const [langChapters, setLangChapters] = useState<Array<{ name: string, filename: string, order: number }>>([]);
    const [langChapterContent, setLangChapterContent] = useState<string | null>(null);
    const [langContentLoading, setLangContentLoading] = useState(false);
    const [selectedChapterFilename, setSelectedChapterFilename] = useState<string | null>(null);

    const {
        currentBook,
        currentBookLoading,
        chapters,
        chaptersLoading,
        currentChapterFilename,
        currentChapterContent,
        chapterContentLoading,
        extracting,
        extractProgress,
        loadBook,
        loadChapters,
        loadChapterContent,
        startExtraction,
        checkExtractionStatus,
        cancelExtraction,
        clearCurrentBook,
    } = useBookStore();

    useEffect(() => {
        if (bookId) {
            loadBook(bookId);
            loadChapters(bookId);
            // Check if there's an ongoing extraction
            checkExtractionStatus(bookId);
        }

        return () => {
            clearCurrentBook();
        };
    }, [bookId, loadBook, loadChapters, checkExtractionStatus, clearCurrentBook]);


    const handleChapterSelect = (key: string) => {
        if (key === SOURCE_KEY) {
            setViewMode('source');
            setSelectedChapterFilename(null);
        } else {
            setViewMode('chapter');
            setSelectedChapterFilename(key);
            if (bookId) {
                // If we have lang chapters loaded, use lang content loading
                if (langChapters.length > 0) {
                    handleLangChapterClick(key);
                } else {
                    loadChapterContent(bookId, key);
                }
            }
        }
    };

    const handleResplitComplete = () => {
        // Reload chapters after re-split
        if (bookId) {
            loadChapters(bookId);
            setViewMode('chapter');
        }
    };

    const handleExtract = () => {
        if (bookId) {
            startExtraction(bookId);
        }
    };

    const handleBack = () => {
        navigate('/');
    };

    // Handle language change - reload chapters for new language
    const handleLanguageChange = async (lang: 'en' | 'zh') => {
        setCurrentLang(lang);
        if (bookId) {
            try {
                const chapters = await getChaptersForLang(bookId, lang);
                setLangChapters(chapters.map(c => ({
                    name: c.title || c.filename,
                    filename: c.filename,
                    order: c.order || 0
                })));
                // Clear current chapter content
                setLangChapterContent(null);
                setViewMode('chapter');
            } catch (error) {
                console.error('Failed to load chapters for language:', error);
            }
        }
    };

    // Load chapter content for current language
    const handleLangChapterClick = async (filename: string) => {
        if (!bookId) return;
        setViewMode('chapter');
        setLangContentLoading(true);
        try {
            const content = await getChapterContentForLang(bookId, currentLang, filename);
            setLangChapterContent(content);
        } catch (error) {
            console.error('Failed to load chapter content:', error);
        } finally {
            setLangContentLoading(false);
        }
    };

    if (currentBookLoading) {
        return (
            <div style={{
                height: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <Spin size="large" />
            </div>
        );
    }

    if (!currentBook) {
        return (
            <div style={{
                height: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                gap: 16,
            }}>
                <Typography.Text>Book not found</Typography.Text>
                <Button onClick={handleBack}>Back to Home</Button>
            </div>
        );
    }

    // Show extract panel if no chapters
    if (!currentBook.has_chapters && chapters.length === 0 && !chaptersLoading) {
        return (
            <Layout style={{ minHeight: '100vh' }}>
                <Header style={{
                    background: '#fff',
                    padding: '0 24px',
                    display: 'flex',
                    alignItems: 'center',
                    borderBottom: '1px solid #f0f0f0',
                }}>
                    <Button
                        type="text"
                        icon={<ArrowLeftOutlined />}
                        onClick={handleBack}
                        style={{ marginRight: 16 }}
                    >
                        Back
                    </Button>
                    <Typography.Title level={4} style={{ margin: 0 }}>
                        {currentBook.title}
                    </Typography.Title>
                </Header>
                <Content>
                    <ExtractPanel
                        bookTitle={currentBook.title}
                        extracting={extracting}
                        progress={extractProgress}
                        onExtract={handleExtract}
                        onCancel={() => bookId && cancelExtraction(bookId)}
                    />
                </Content>
            </Layout>
        );
    }

    // Build menu items: Source markdown + Chapters
    // Use langChapters if we have translations, otherwise use original chapters
    const displayChapters = langChapters.length > 0 ? langChapters : chapters;

    const menuItems = [
        {
            key: SOURCE_KEY,
            icon: <FileMarkdownOutlined />,
            label: 'Source Document (Edit)',
            style: {
                fontWeight: viewMode === 'source' ? 600 : 400,
                background: viewMode === 'source' ? '#e6f7ff' : undefined,
            },
        },
        {
            type: 'divider' as const,
        },
        ...displayChapters.map((chapter) => ({
            key: chapter.filename,
            icon: <FileTextOutlined />,
            label: chapter.name,
        })),
    ];

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Header style={{
                background: '#fff',
                padding: '0 24px',
                display: 'flex',
                alignItems: 'center',
                borderBottom: '1px solid #f0f0f0',
            }}>
                <Button
                    type="text"
                    icon={<ArrowLeftOutlined />}
                    onClick={handleBack}
                    style={{ marginRight: 16 }}
                >
                    Back
                </Button>
                <Typography.Title level={4} style={{ margin: 0, flex: 1 }}>
                    {currentBook.title}
                </Typography.Title>
                <LanguageSelector
                    bookId={bookId!}
                    currentLang={currentLang}
                    onLanguageChange={handleLanguageChange}
                    showTranslation={viewMode === 'source'}
                />
            </Header>
            <Layout>
                <Sider
                    width={280}
                    style={{
                        background: '#fff',
                        borderRight: '1px solid #f0f0f0',
                        overflow: 'auto',
                        height: 'calc(100vh - 64px)',
                    }}
                >
                    {chaptersLoading ? (
                        <div style={{ padding: 24, textAlign: 'center' }}>
                            <Spin />
                        </div>
                    ) : (
                        <Menu
                            mode="inline"
                            selectedKeys={
                                viewMode === 'source'
                                    ? [SOURCE_KEY]
                                    : currentChapterFilename
                                        ? [currentChapterFilename]
                                        : []
                            }
                            items={menuItems}
                            onClick={({ key }) => handleChapterSelect(key)}
                            style={{
                                height: '100%',
                                borderRight: 0,
                            }}
                        />
                    )}
                </Sider>
                <Content style={{
                    overflow: 'auto',
                    height: 'calc(100vh - 64px)',
                    background: '#fff',
                }}>
                    {viewMode === 'source' && bookId ? (
                        <SourceEditor
                            bookId={bookId}
                            onResplitComplete={handleResplitComplete}
                        />
                    ) : (
                        <div style={{ padding: 24 }}>
                            {/* Batch Summary Panel */}
                            {bookId && (
                                <BatchSummaryPanel
                                    bookId={bookId}
                                    lang={currentLang}
                                />
                            )}
                            {/* Chapter Summary */}
                            {selectedChapterFilename && bookId && (
                                <ChapterSummary
                                    bookId={bookId}
                                    lang={currentLang}
                                    chapterFilename={selectedChapterFilename}
                                />
                            )}
                            <MarkdownViewer
                                content={langChapterContent ?? currentChapterContent}
                                loading={langContentLoading || chapterContentLoading}
                                bookId={bookId}
                            />
                        </div>
                    )}
                </Content>
            </Layout>
        </Layout>
    );
};

export default BookDetailPage;

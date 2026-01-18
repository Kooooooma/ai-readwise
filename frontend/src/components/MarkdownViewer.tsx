/**
 * MarkdownViewer component - renders markdown content
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Spin, Typography } from 'antd';

interface MarkdownViewerProps {
    content: string | null;
    loading: boolean;
    bookId?: string;  // Optional: used to resolve image paths
}

const MarkdownViewer: React.FC<MarkdownViewerProps> = ({ content, loading, bookId }) => {
    if (loading) {
        return (
            <div style={{ padding: 48, textAlign: 'center' }}>
                <Spin size="large" />
            </div>
        );
    }

    if (!content) {
        return (
            <div style={{ padding: 48, textAlign: 'center' }}>
                <Typography.Text type="secondary">
                    Please select a chapter from the left
                </Typography.Text>
            </div>
        );
    }

    // Transform relative image paths to API URLs
    const transformedContent = bookId
        ? content.replace(
            /!\[([^\]]*)\]\(images\/([^)]+)\)/g,
            `![$1](/api/books/${encodeURIComponent(bookId)}/images/images/$2)`
        )
        : content;

    return (
        <div className="markdown-content">
            <ReactMarkdown>{transformedContent}</ReactMarkdown>
        </div>
    );
};

export default MarkdownViewer;

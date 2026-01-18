/**
 * SourceEditor component - Edit and preview source markdown
 * 
 * Features:
 * - Toggle between Preview and Edit modes
 * - Real-time save when editing
 * - Re-split chapters button
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Button, Space, Spin, message, Switch, Typography, Divider, Modal } from 'antd';
import { EditOutlined, EyeOutlined, SyncOutlined, SaveOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { fetchSourceMarkdown, updateSourceMarkdown, resplitChapters } from '../api';

const { Text } = Typography;

interface SourceEditorProps {
    bookId: string;
    onResplitComplete?: () => void;
}

const SourceEditor: React.FC<SourceEditorProps> = ({ bookId, onResplitComplete }) => {
    // State
    const [content, setContent] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [resplitting, setResplitting] = useState(false);
    const [editMode, setEditMode] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);
    const [originalContent, setOriginalContent] = useState<string>('');

    // Load source markdown
    useEffect(() => {
        const loadContent = async () => {
            setLoading(true);
            try {
                const markdown = await fetchSourceMarkdown(bookId);
                setContent(markdown);
                setOriginalContent(markdown);
            } catch (error) {
                message.error('Failed to load source document');
                console.error('Failed to load source markdown:', error);
            } finally {
                setLoading(false);
            }
        };
        loadContent();
    }, [bookId]);

    // Handle content change
    const handleContentChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newContent = e.target.value;
        setContent(newContent);
        setHasChanges(newContent !== originalContent);
    }, [originalContent]);

    // Save content
    const handleSave = async () => {
        setSaving(true);
        try {
            await updateSourceMarkdown(bookId, content);
            setOriginalContent(content);
            setHasChanges(false);
            message.success('Saved successfully');
        } catch (error) {
            message.error('Save failed');
            console.error('Failed to save:', error);
        } finally {
            setSaving(false);
        }
    };

    // Re-split chapters
    const handleResplit = async () => {
        // Confirm if there are unsaved changes
        if (hasChanges) {
            Modal.confirm({
                title: 'Unsaved Changes',
                content: 'You need to save changes before re-splitting. Save and continue?',
                onOk: async () => {
                    await handleSave();
                    doResplit();
                },
            });
            return;
        }
        doResplit();
    };

    const doResplit = async () => {
        setResplitting(true);
        try {
            const result = await resplitChapters(bookId);
            message.success(`Re-split successful. Generated ${result.chapter_count} chapters.`);
            onResplitComplete?.();
        } catch (error) {
            message.error('Re-split failed');
            console.error('Failed to resplit:', error);
        } finally {
            setResplitting(false);
        }
    };

    // Toggle edit mode
    const handleModeChange = (checked: boolean) => {
        // Warn if switching away from edit mode with unsaved changes
        if (!checked && hasChanges) {
            Modal.confirm({
                title: 'Unsaved Changes',
                content: 'Switching to preview mode will discard unsaved changes. Continue?',
                onOk: () => {
                    setContent(originalContent);
                    setHasChanges(false);
                    setEditMode(false);
                },
            });
            return;
        }
        setEditMode(checked);
    };

    if (loading) {
        return (
            <div style={{ padding: 48, textAlign: 'center' }}>
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>
                    <Text type="secondary">Loading source document...</Text>
                </div>
            </div>
        );
    }

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Toolbar */}
            <div style={{
                padding: '12px 16px',
                borderBottom: '1px solid #f0f0f0',
                background: '#fafafa',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
            }}>
                <Space>
                    <Switch
                        checked={editMode}
                        onChange={handleModeChange}
                        checkedChildren={<><EditOutlined /> Edit</>}
                        unCheckedChildren={<><EyeOutlined /> Preview</>}
                    />
                    {editMode && hasChanges && (
                        <Text type="warning">* Unsaved changes</Text>
                    )}
                </Space>

                <Space>
                    {editMode && (
                        <Button
                            type="primary"
                            icon={<SaveOutlined />}
                            onClick={handleSave}
                            loading={saving}
                            disabled={!hasChanges}
                        >
                            Save
                        </Button>
                    )}
                    <Divider type="vertical" />
                    <Button
                        icon={<SyncOutlined />}
                        onClick={handleResplit}
                        loading={resplitting}
                    >
                        Re-split Chapters
                    </Button>
                </Space>
            </div>

            {/* Content area */}
            <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
                {editMode ? (
                    // Edit mode: textarea
                    <textarea
                        value={content}
                        onChange={handleContentChange}
                        style={{
                            width: '100%',
                            height: '100%',
                            minHeight: 'calc(100vh - 200px)',
                            padding: 16,
                            border: '1px solid #d9d9d9',
                            borderRadius: 6,
                            fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                            fontSize: 14,
                            lineHeight: 1.6,
                            resize: 'none',
                        }}
                        placeholder="Edit Markdown content here..."
                    />
                ) : (() => {
                    // Preview mode: markdown viewer with image URL transformation
                    const transformedContent = content.replace(
                        /!\[([^\]]*)\]\(images\/([^)]+)\)/g,
                        `![$1](/api/books/${encodeURIComponent(bookId)}/images/images/$2)`
                    );
                    return (
                        <div className="markdown-content">
                            <ReactMarkdown>{transformedContent}</ReactMarkdown>
                        </div>
                    );
                })()}
            </div>
        </div>
    );
};

export default SourceEditor;

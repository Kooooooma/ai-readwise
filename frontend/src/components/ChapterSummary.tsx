/**
 * ChapterSummary component - Display and edit chapter summaries
 * 
 * Features:
 * - Generate summary button (calls LLM API)
 * - Display key points, conclusions, examples
 * - Editable voice script for podcast
 * - Save edited content
 */

import React, { useState, useEffect, useRef } from 'react';
import { Button, Card, Collapse, Input, List, Space, Spin, Typography, message, Tooltip } from 'antd';
import {
    BulbOutlined,
    EditOutlined,
    SaveOutlined,
    SyncOutlined,
    CheckCircleOutlined,
    ExperimentOutlined,
    SoundOutlined,
    PlayCircleOutlined,
    LoadingOutlined
} from '@ant-design/icons';
import {
    getChapterSummary,
    generateChapterSummary,
    saveChapterSummary,
    generateSummaryMp3,
    getSummaryMp3Url,
    type ChapterSummary as ChapterSummaryType
} from '../api';

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

interface ChapterSummaryProps {
    bookId: string;
    lang: string;
    chapterFilename: string;
}

const ChapterSummary: React.FC<ChapterSummaryProps> = ({
    bookId,
    lang,
    chapterFilename,
}) => {
    const [summary, setSummary] = useState<ChapterSummaryType | null>(null);
    const [loading, setLoading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [saving, setSaving] = useState(false);
    const [editing, setEditing] = useState(false);
    const [editedScript, setEditedScript] = useState('');
    const [hasMp3, setHasMp3] = useState(false);
    const [generatingMp3, setGeneratingMp3] = useState(false);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    // Cleanup audio when chapter changes or unmounts
    useEffect(() => {
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current.src = '';
                audioRef.current = null;
            }
        };
    }, [chapterFilename]);

    // Stop current audio playback
    const stopAudio = () => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
            audioRef.current.src = '';
        }
    };

    // Load existing summary on mount or when chapter changes
    useEffect(() => {
        loadSummary();
    }, [bookId, lang, chapterFilename]);

    const loadSummary = async () => {
        if (!chapterFilename) return;

        // Stop any playing audio before loading new chapter
        stopAudio();

        setLoading(true);
        try {
            const result = await getChapterSummary(bookId, lang, chapterFilename);
            setSummary(result.summary);
            setHasMp3(result.has_mp3);
            if (result.summary?.voice_script) {
                setEditedScript(result.summary.voice_script);
            }
        } catch (error) {
            console.error('Failed to load summary:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerate = async () => {
        setGenerating(true);
        try {
            const data = await generateChapterSummary(bookId, lang, chapterFilename);
            setSummary(data);
            setEditedScript(data.voice_script || '');
            setHasMp3(false);  // MP3 is deleted on regenerate
            message.success('Summary generated successfully');
        } catch (error) {
            message.error('Failed to generate summary');
            console.error('Generate error:', error);
        } finally {
            setGenerating(false);
        }
    };

    const handleGenerateMp3 = async () => {
        setGeneratingMp3(true);
        try {
            await generateSummaryMp3(bookId, lang, chapterFilename);
            setHasMp3(true);
            message.success('MP3 generated successfully');
        } catch (error) {
            message.error('Failed to generate MP3');
            console.error('Generate MP3 error:', error);
        } finally {
            setGeneratingMp3(false);
        }
    };

    const handleSave = async () => {
        if (!summary) return;

        setSaving(true);
        try {
            const updated = await saveChapterSummary(bookId, lang, chapterFilename, {
                ...summary,
                voice_script: editedScript,
            });
            setSummary(updated);
            setEditing(false);
            message.success('Summary saved successfully');
        } catch (error) {
            message.error('Failed to save summary');
            console.error('Save error:', error);
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <Card size="small" style={{ marginBottom: 16 }}>
                <Spin size="small" /> Loading summary...
            </Card>
        );
    }

    // No summary yet - show generate button
    if (!summary) {
        return (
            <Card size="small" style={{ marginBottom: 16, background: '#fafafa' }}>
                <Space>
                    <BulbOutlined style={{ color: '#faad14' }} />
                    <Text type="secondary">No summary available for this chapter.</Text>
                    <Button
                        type="primary"
                        size="small"
                        icon={<ExperimentOutlined />}
                        onClick={handleGenerate}
                        loading={generating}
                    >
                        Generate Summary
                    </Button>
                </Space>
            </Card>
        );
    }

    const collapseItems = [
        {
            key: 'key_points',
            label: (
                <Space>
                    <BulbOutlined style={{ color: '#1890ff' }} />
                    <Text strong>Key Points</Text>
                    <Text type="secondary">({summary.key_points?.length || 0})</Text>
                </Space>
            ),
            children: (
                <List
                    size="small"
                    dataSource={summary.key_points || []}
                    renderItem={(item, index) => (
                        <List.Item style={{ padding: '4px 0' }}>
                            <Text>{index + 1}. {item}</Text>
                        </List.Item>
                    )}
                />
            ),
        },
        {
            key: 'conclusions',
            label: (
                <Space>
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                    <Text strong>Conclusions</Text>
                    <Text type="secondary">({summary.conclusions?.length || 0})</Text>
                </Space>
            ),
            children: (
                <List
                    size="small"
                    dataSource={summary.conclusions || []}
                    renderItem={(item, index) => (
                        <List.Item style={{ padding: '4px 0' }}>
                            <Text>{index + 1}. {item}</Text>
                        </List.Item>
                    )}
                />
            ),
        },
        {
            key: 'examples',
            label: (
                <Space>
                    <ExperimentOutlined style={{ color: '#722ed1' }} />
                    <Text strong>Examples</Text>
                    <Text type="secondary">({summary.examples?.length || 0})</Text>
                </Space>
            ),
            children: (
                <List
                    size="small"
                    dataSource={summary.examples || []}
                    renderItem={(item, index) => (
                        <List.Item style={{ padding: '4px 0' }}>
                            <Text>{index + 1}. {item}</Text>
                        </List.Item>
                    )}
                />
            ),
        },
        {
            key: 'voice_script',
            label: (
                <Space>
                    <SoundOutlined style={{ color: '#fa541c' }} />
                    <Text strong>Voice Script</Text>
                    <Text type="secondary">(~2 min)</Text>
                </Space>
            ),
            children: (
                <div>
                    {editing ? (
                        <div>
                            <TextArea
                                value={editedScript}
                                onChange={(e) => setEditedScript(e.target.value)}
                                autoSize={{ minRows: 6, maxRows: 15 }}
                                style={{ marginBottom: 8 }}
                            />
                            <Space>
                                <Button
                                    type="primary"
                                    size="small"
                                    icon={<SaveOutlined />}
                                    onClick={handleSave}
                                    loading={saving}
                                >
                                    Save
                                </Button>
                                <Button
                                    size="small"
                                    onClick={() => {
                                        setEditing(false);
                                        setEditedScript(summary.voice_script || '');
                                    }}
                                >
                                    Cancel
                                </Button>
                            </Space>
                        </div>
                    ) : (
                        <div>
                            <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 8 }}>
                                {summary.voice_script}
                            </Paragraph>
                            <Space style={{ marginBottom: 8 }}>
                                <Button
                                    size="small"
                                    icon={<EditOutlined />}
                                    onClick={() => setEditing(true)}
                                >
                                    Edit Script
                                </Button>
                                {hasMp3 ? (
                                    <audio
                                        ref={audioRef}
                                        controls
                                        src={getSummaryMp3Url(bookId, lang, chapterFilename)}
                                        style={{ height: 32 }}
                                    />
                                ) : (
                                    <Button
                                        size="small"
                                        type="primary"
                                        icon={generatingMp3 ? <LoadingOutlined /> : <PlayCircleOutlined />}
                                        onClick={handleGenerateMp3}
                                        loading={generatingMp3}
                                    >
                                        Generate MP3
                                    </Button>
                                )}
                            </Space>
                        </div>
                    )}
                </div>
            ),
        },
    ];

    return (
        <Card
            size="small"
            style={{ marginBottom: 16 }}
            title={
                <Space>
                    <BulbOutlined style={{ color: '#faad14' }} />
                    <Text strong>Chapter Summary</Text>
                    {summary.generated_at && (
                        <Tooltip title={`Generated: ${new Date(summary.generated_at).toLocaleString()}`}>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                {summary.model && `(${summary.model})`}
                            </Text>
                        </Tooltip>
                    )}
                </Space>
            }
            extra={
                <Button
                    size="small"
                    icon={<SyncOutlined />}
                    onClick={handleGenerate}
                    loading={generating}
                >
                    Regenerate
                </Button>
            }
        >
            <Collapse
                items={collapseItems}
                defaultActiveKey={['voice_script']}
                size="small"
            />
        </Card>
    );
};

export default ChapterSummary;

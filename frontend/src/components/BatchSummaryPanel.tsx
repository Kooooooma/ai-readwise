/**
 * BatchSummaryPanel - Generate summaries and MP3 for all chapters
 * 
 * Features:
 * - Generate All button with progress
 * - Resume support (skips existing)
 * - MP3 Playlist with sequential playback
 */

import React, { useState, useEffect, useRef } from 'react';
import { Button, Card, Progress, Space, Typography, List, message, Divider } from 'antd';
import {
    ThunderboltOutlined,
    PlayCircleOutlined,
    PauseCircleOutlined,
    StopOutlined,
    CheckCircleOutlined,
    LoadingOutlined,
    SoundOutlined
} from '@ant-design/icons';
import {
    getAllSummariesStatus,
    generateAllSummaries,
    getSummaryMp3Url,
    type AllSummariesStatus,
    type BatchProgress
} from '../api';

const { Text } = Typography;

interface BatchSummaryPanelProps {
    bookId: string;
    lang: string;
}

const BatchSummaryPanel: React.FC<BatchSummaryPanelProps> = ({ bookId, lang }) => {
    const [status, setStatus] = useState<AllSummariesStatus | null>(null);
    const [loading, setLoading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [progress, setProgress] = useState<BatchProgress | null>(null);
    const [currentPlaying, setCurrentPlaying] = useState<number>(-1);
    const [isPlaying, setIsPlaying] = useState(false);

    const audioRef = useRef<HTMLAudioElement | null>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    // Load status on mount
    useEffect(() => {
        loadStatus();
    }, [bookId, lang]);

    // Cleanup audio on unmount or when bookId/lang changes
    useEffect(() => {
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current.src = '';  // Release the file
                audioRef.current = null;
            }
            setCurrentPlaying(-1);
            setIsPlaying(false);
        };
    }, [bookId, lang]);

    const loadStatus = async () => {
        setLoading(true);
        try {
            const data = await getAllSummariesStatus(bookId, lang);
            setStatus(data);
        } catch (error) {
            console.error('Failed to load status:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateAll = async () => {
        setGenerating(true);
        setProgress(null);
        abortControllerRef.current = new AbortController();

        try {
            await generateAllSummaries(
                bookId,
                lang,
                (prog) => {
                    setProgress(prog);
                    if (prog.type === 'complete') {
                        message.success(`Generated ${prog.generated_summaries} summaries, ${prog.generated_mp3s} MP3s`);
                        loadStatus();
                    }
                },
                abortControllerRef.current.signal
            );
        } catch (error: unknown) {
            if ((error as Error).name !== 'AbortError') {
                message.error('Generation failed');
                console.error('Generation error:', error);
            }
        } finally {
            setGenerating(false);
            setProgress(null);
        }
    };

    const handleStop = () => {
        abortControllerRef.current?.abort();
        setGenerating(false);
        setProgress(null);
        loadStatus();
    };

    const mp3Chapters = status?.chapters.filter(ch => ch.has_mp3) || [];

    const playTrack = (index: number) => {
        if (index < 0 || index >= mp3Chapters.length) {
            setCurrentPlaying(-1);
            setIsPlaying(false);
            return;
        }

        const chapter = mp3Chapters[index];
        const url = getSummaryMp3Url(bookId, lang, chapter.filename);

        if (!audioRef.current) {
            audioRef.current = new Audio();
            audioRef.current.onended = () => {
                // Auto-advance to next track
                playTrack(currentPlaying + 1);
            };
            audioRef.current.onplay = () => setIsPlaying(true);
            audioRef.current.onpause = () => setIsPlaying(false);
        }

        audioRef.current.src = url;
        audioRef.current.play();
        setCurrentPlaying(index);
        setIsPlaying(true);
    };

    const togglePlayPause = () => {
        if (!audioRef.current) return;

        if (isPlaying) {
            audioRef.current.pause();
        } else {
            audioRef.current.play();
        }
    };

    const stopPlayback = () => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
            audioRef.current.src = '';  // Release the file
        }
        setCurrentPlaying(-1);
        setIsPlaying(false);
    };

    const progressPercent = progress?.total
        ? Math.round((progress.current || 0) / progress.total * 100)
        : 0;

    return (
        <Card size="small" style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
                {/* Header */}
                <Space style={{ justifyContent: 'space-between', width: '100%' }}>
                    <Space>
                        <ThunderboltOutlined style={{ color: '#faad14' }} />
                        <Text strong>Batch Summary & MP3</Text>
                        {status && (
                            <Text type="secondary">
                                ({status.with_summary}/{status.total} summaries, {status.with_mp3}/{status.total} MP3s)
                            </Text>
                        )}
                    </Space>

                    {generating ? (
                        <Button size="small" danger icon={<StopOutlined />} onClick={handleStop}>
                            Stop
                        </Button>
                    ) : (
                        <Button
                            type="primary"
                            size="small"
                            icon={<ThunderboltOutlined />}
                            onClick={handleGenerateAll}
                            loading={loading}
                        >
                            Generate All
                        </Button>
                    )}
                </Space>

                {/* Progress */}
                {generating && progress && (
                    <div>
                        <Progress percent={progressPercent} size="small" />
                        <Text type="secondary">
                            {progress.current}/{progress.total} - {progress.chapter} ({progress.step})
                        </Text>
                    </div>
                )}

                {/* Playlist */}
                {mp3Chapters.length > 0 && (
                    <>
                        <Divider style={{ margin: '8px 0' }} />
                        <Space style={{ justifyContent: 'space-between', width: '100%' }}>
                            <Space>
                                <SoundOutlined />
                                <Text strong>MP3 Playlist</Text>
                                <Text type="secondary">({mp3Chapters.length} tracks)</Text>
                            </Space>
                            <Space>
                                {currentPlaying >= 0 && (
                                    <Button
                                        size="small"
                                        icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                                        onClick={togglePlayPause}
                                    >
                                        {isPlaying ? 'Pause' : 'Resume'}
                                    </Button>
                                )}
                                <Button
                                    size="small"
                                    type="primary"
                                    icon={<PlayCircleOutlined />}
                                    onClick={() => playTrack(0)}
                                    disabled={currentPlaying >= 0}
                                >
                                    Play All
                                </Button>
                                {currentPlaying >= 0 && (
                                    <Button size="small" icon={<StopOutlined />} onClick={stopPlayback}>
                                        Stop
                                    </Button>
                                )}
                            </Space>
                        </Space>

                        <List
                            size="small"
                            dataSource={mp3Chapters}
                            style={{ maxHeight: 200, overflow: 'auto' }}
                            renderItem={(item, index) => (
                                <List.Item
                                    style={{
                                        padding: '4px 8px',
                                        background: currentPlaying === index ? '#e6f7ff' : 'transparent',
                                    }}
                                >
                                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                                        <Space>
                                            {currentPlaying === index && isPlaying ? (
                                                <LoadingOutlined style={{ color: '#1890ff' }} />
                                            ) : (
                                                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                                            )}
                                            <Text>{index + 1}. {item.title || item.filename}</Text>
                                        </Space>
                                        <Button
                                            type={currentPlaying === index ? 'primary' : 'text'}
                                            size="small"
                                            icon={currentPlaying === index && isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                                            onClick={() => {
                                                if (currentPlaying === index && isPlaying) {
                                                    togglePlayPause();
                                                } else {
                                                    playTrack(index);
                                                }
                                            }}
                                        >
                                            {currentPlaying === index && isPlaying ? 'Pause' : 'Play'}
                                        </Button>
                                    </Space>
                                </List.Item>
                            )}
                        />
                    </>
                )}
            </Space>
        </Card>
    );
};

export default BatchSummaryPanel;

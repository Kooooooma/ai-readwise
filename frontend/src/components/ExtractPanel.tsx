/**
 * ExtractPanel component - shows extraction UI and progress
 * 
 * Features:
 * - Start extraction button
 * - Progress display with stages
 * - Cancel button during extraction
 * - Retry button on error
 */

import React from 'react';
import { Button, Progress, Typography, Space, Alert } from 'antd';
import { ThunderboltOutlined, StopOutlined } from '@ant-design/icons';
import type { ExtractProgress } from '../api';

const { Title, Text } = Typography;

interface ExtractPanelProps {
    bookTitle: string;
    extracting: boolean;
    progress: ExtractProgress | null;
    onExtract: () => void;
    onCancel?: () => void;
}

const ExtractPanel: React.FC<ExtractPanelProps> = ({
    bookTitle,
    extracting,
    progress,
    onExtract,
    onCancel,
}) => {
    const getProgressStatus = () => {
        if (!progress) return 'normal';
        if (progress.status === 'error' || progress.status === 'cancelled') return 'exception';
        if (progress.status === 'completed') return 'success';
        return 'active';
    };

    const getAlertType = () => {
        if (!progress) return 'info';
        if (progress.status === 'error') return 'error';
        if (progress.status === 'cancelled') return 'warning';
        if (progress.status === 'completed') return 'success';
        return 'info';
    };

    const isInProgress = progress?.status === 'extracting' || progress?.status === 'splitting';
    const showInitialButton = !extracting && !progress;
    const showCancelledRetry = progress?.status === 'cancelled';
    const showExtractedResume = progress?.status === 'extracted';  // PDF done, split pending

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            padding: 48,
        }}>
            <Title level={3} style={{ marginBottom: 24 }}>
                {bookTitle}
            </Title>

            <Text type="secondary" style={{ marginBottom: 32, textAlign: 'center' }}>
                {showExtractedResume
                    ? 'PDF extraction completed. Click to continue with chapter splitting.'
                    : showCancelledRetry
                        ? 'Previous extraction was cancelled. Click to retry.'
                        : 'This book has not been extracted yet. Click the button below to convert PDF to Markdown chapters.'}
            </Text>

            {(showInitialButton || showCancelledRetry || showExtractedResume) && (
                <Button
                    type="primary"
                    size="large"
                    icon={<ThunderboltOutlined />}
                    onClick={onExtract}
                >
                    {showExtractedResume
                        ? 'Continue Splitting'
                        : showCancelledRetry
                            ? 'Retry Extraction'
                            : 'Extract PDF Content'}
                </Button>
            )}

            {(extracting || (progress && !showCancelledRetry)) && (
                <Space direction="vertical" style={{ width: '100%', maxWidth: 500 }}>
                    <Progress
                        percent={progress?.progress || 0}
                        status={getProgressStatus()}
                    />

                    {progress?.current_step && (
                        <Text strong>Current Step: {progress.current_step}</Text>
                    )}

                    {progress?.message && (
                        <Alert
                            type={getAlertType()}
                            message={
                                <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                                    {progress.message}
                                </div>
                            }
                            showIcon
                        />
                    )}

                    <Space style={{ marginTop: 16 }}>
                        {/* Cancel button - show during extraction */}
                        {isInProgress && onCancel && (
                            <Button
                                danger
                                icon={<StopOutlined />}
                                onClick={onCancel}
                            >
                                Cancel
                            </Button>
                        )}

                        {/* Retry button - show on error */}
                        {progress?.status === 'error' && (
                            <Button
                                type="primary"
                                icon={<ThunderboltOutlined />}
                                onClick={onExtract}
                            >
                                Retry
                            </Button>
                        )}
                    </Space>
                </Space>
            )}
        </div>
    );
};

export default ExtractPanel;

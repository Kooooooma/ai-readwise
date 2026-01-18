/**
 * LanguageSelector component - Language switch and translation controls
 * 
 * Features:
 * - Language dropdown (just switches display, shows status if interrupted)
 * - Separate translate button (only on source page)
 * - Model dropdown for translation
 * - Translation progress display with stop button
 * - Resume from interrupted translation
 */

import React, { useState, useEffect, useRef } from 'react';
import { Select, Space, Progress, message, Button } from 'antd';
import { TranslationOutlined, GlobalOutlined, PauseCircleOutlined } from '@ant-design/icons';
import {
    getAvailableModels,
    getBookLanguages,
    translateBook,
    cancelTranslation,
} from '../api';
import type { BookLanguages, TranslationProgress } from '../api';

interface LanguageSelectorProps {
    bookId: string;
    onLanguageChange: (lang: 'en' | 'zh') => void;
    currentLang: 'en' | 'zh';
    showTranslation?: boolean;  // Only show translation controls on source page
}

const LANG_OPTIONS = [
    { value: 'en', label: 'English' },
    { value: 'zh', label: 'Chinese' },
];

// Consistent styling for all controls
const CONTROL_HEIGHT = 28;
const CONTROL_STYLE = { height: CONTROL_HEIGHT, lineHeight: `${CONTROL_HEIGHT}px` };

const LanguageSelector: React.FC<LanguageSelectorProps> = ({
    bookId,
    onLanguageChange,
    currentLang,
    showTranslation = false
}) => {
    const [models, setModels] = useState<string[]>([]);
    const [selectedModel, setSelectedModel] = useState<string>('');
    const [languageInfo, setLanguageInfo] = useState<BookLanguages | null>(null);
    const [translating, setTranslating] = useState(false);
    const [translateProgress, setTranslateProgress] = useState<TranslationProgress | null>(null);
    const [loadingLang, setLoadingLang] = useState(true);
    const abortControllerRef = useRef<AbortController | null>(null);

    // Load models on mount
    useEffect(() => {
        const loadModels = async () => {
            try {
                const config = await getAvailableModels();
                setModels(config.models);
                setSelectedModel(config.default);
            } catch (error) {
                console.error('Failed to load models:', error);
            }
        };
        loadModels();
    }, []);

    // Load language info when bookId changes
    useEffect(() => {
        const loadLanguageInfo = async () => {
            setLoadingLang(true);
            try {
                const info = await getBookLanguages(bookId);
                setLanguageInfo(info);
                // Set current language to source language initially
                onLanguageChange(info.source_lang);
            } catch (error) {
                console.error('Failed to load language info:', error);
            } finally {
                setLoadingLang(false);
            }
        };
        loadLanguageInfo();
    }, [bookId]);

    // Language switch - just switch the display, don't auto-translate
    const handleLanguageSwitch = (lang: 'en' | 'zh') => {
        onLanguageChange(lang);
    };

    // Stop translation
    const handleStopTranslation = async () => {
        // Call backend to cancel
        try {
            await cancelTranslation(bookId);
        } catch (error) {
            console.error('Failed to cancel translation:', error);
        }

        // Abort frontend request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        setTranslating(false);
        setTranslateProgress(null);
        message.info('Translation stopped. You can resume from where you left off.');

        // Refresh status to show saved progress
        getBookLanguages(bookId).then(info => setLanguageInfo(info));
    };

    // Translate button click - start translation
    const handleTranslateClick = async () => {
        if (!selectedModel) {
            message.warning('Please select a translation model');
            return;
        }

        // Translate to the language that doesn't exist
        const targetLang = needsTranslation('zh') ? 'zh' : 'en';

        setTranslating(true);
        setTranslateProgress({ progress: 0, message: 'Starting translation...' });

        // Create abort controller for stopping
        abortControllerRef.current = new AbortController();

        try {
            await translateBook(bookId, targetLang, selectedModel, (progress) => {
                setTranslateProgress(progress);

                if (progress.status === 'completed') {
                    message.success(`Translation completed. Generated ${progress.chapter_count} chapters.`);
                    // Reload language info
                    getBookLanguages(bookId).then(info => {
                        setLanguageInfo(info);
                        // Switch to the translated language
                        onLanguageChange(targetLang);
                    });
                } else if (progress.status === 'error') {
                    message.error(`Translation failed: ${progress.message}`);
                } else if (progress.status === 'stopped') {
                    message.info('Translation paused');
                }
            }, abortControllerRef.current.signal);
        } catch (error) {
            if ((error as Error).name === 'AbortError') {
                message.info('Translation stopped');
            } else {
                message.error('Translation request failed');
                console.error('Translation failed:', error);
            }
        } finally {
            setTranslating(false);
            setTranslateProgress(null);
            abortControllerRef.current = null;
        }
    };

    const needsTranslation = (lang: 'en' | 'zh') => {
        return languageInfo && !languageInfo.has_translation[lang];
    };

    // Get saved progress for a language
    const getSavedProgress = (lang: 'en' | 'zh') => {
        return languageInfo?.translation_progress?.[lang] || 0;
    };

    // Get target language for translation (the one that doesn't exist)
    const getTranslateTargetLang = () => {
        if (!languageInfo) return null;
        if (!languageInfo.has_translation.zh) return 'zh';
        if (!languageInfo.has_translation.en) return 'en';
        return null;
    };

    const translateTargetLang = getTranslateTargetLang();

    // Only show translate button when current language needs translation
    const showTranslateButton = translateTargetLang && translateTargetLang === currentLang;
    const savedProgress = translateTargetLang ? getSavedProgress(translateTargetLang) : 0;
    const isResuming = savedProgress > 0 && !translating;

    // Build language options to show status
    const langOptions = LANG_OPTIONS.map(opt => {
        const lang = opt.value as 'en' | 'zh';
        const progress = getSavedProgress(lang);
        const needsTrans = needsTranslation(lang);

        let label = opt.label;
        if (needsTrans && progress > 0) {
            label = `${opt.label} (${progress}%)`;
        }

        return {
            ...opt,
            label,
        };
    });

    // Get button text based on target language
    const getTranslateButtonText = () => {
        if (isResuming) {
            return `Resume (${savedProgress}%)`;
        }
        return translateTargetLang === 'zh' ? 'Translate to Chinese' : 'Translate to English';
    };

    return (
        <Space size="small" align="center" style={{ display: 'flex', alignItems: 'center' }}>
            <GlobalOutlined style={{ color: '#666', fontSize: 14 }} />

            {/* Language dropdown */}
            <Select
                value={currentLang}
                onChange={handleLanguageSwitch}
                options={langOptions}
                disabled={loadingLang || translating}
                loading={loadingLang}
                size="small"
                style={{ width: 120, ...CONTROL_STYLE }}
            />

            {/* Status message - show when current language needs translation and not translating */}
            {languageInfo && needsTranslation(currentLang) && !translating && !showTranslateButton && (
                <span style={{ color: '#999', fontSize: 12, ...CONTROL_STYLE }}>
                    {getSavedProgress(currentLang) > 0
                        ? `${getSavedProgress(currentLang)}% done (not available)`
                        : '(Not available)'}
                </span>
            )}

            {/* Translation progress */}
            {translating && translateProgress && (
                <Space size={8} align="center" style={{ display: 'flex', alignItems: 'center', height: CONTROL_HEIGHT }}>
                    <Progress
                        type="circle"
                        percent={translateProgress.progress || 0}
                        size={32}
                        strokeWidth={8}
                        format={(percent) => <span style={{ fontSize: 10 }}>{percent}</span>}
                        style={{ display: 'flex', alignItems: 'center' }}
                    />
                    <span style={{ color: '#666', fontSize: 12, lineHeight: `${CONTROL_HEIGHT}px` }}>
                        {translateProgress.message}
                    </span>
                    <Button
                        type="text"
                        size="small"
                        danger
                        icon={<PauseCircleOutlined />}
                        onClick={handleStopTranslation}
                        style={{ ...CONTROL_STYLE, padding: '0 8px' }}
                    >
                        Stop
                    </Button>
                </Space>
            )}

            {/* Model selector and translate button */}
            {showTranslation && showTranslateButton && !translating && (
                <Space size={8} align="center">
                    <Select
                        value={selectedModel}
                        onChange={setSelectedModel}
                        style={{ width: 140, ...CONTROL_STYLE }}
                        placeholder="Model"
                        size="small"
                    >
                        {models.map(model => (
                            <Select.Option key={model} value={model}>
                                {model}
                            </Select.Option>
                        ))}
                    </Select>
                    <Button
                        type="primary"
                        size="small"
                        icon={<TranslationOutlined />}
                        onClick={handleTranslateClick}
                        style={{ ...CONTROL_STYLE }}
                    >
                        {getTranslateButtonText()}
                    </Button>
                </Space>
            )}
        </Space>
    );
};

export default LanguageSelector;

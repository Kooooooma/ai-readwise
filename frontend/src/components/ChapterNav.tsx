/**
 * ChapterNav component - sidebar navigation for chapters
 */

import React from 'react';
import { Menu, Spin } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import type { Chapter } from '../api';

interface ChapterNavProps {
    chapters: Chapter[];
    loading: boolean;
    selectedFilename: string | null;
    onSelect: (filename: string) => void;
}

const ChapterNav: React.FC<ChapterNavProps> = ({
    chapters,
    loading,
    selectedFilename,
    onSelect,
}) => {
    if (loading) {
        return (
            <div style={{ padding: 24, textAlign: 'center' }}>
                <Spin />
            </div>
        );
    }

    const menuItems = chapters.map((chapter) => ({
        key: chapter.filename,
        icon: <FileTextOutlined />,
        label: chapter.name,
    }));

    return (
        <Menu
            mode="inline"
            selectedKeys={selectedFilename ? [selectedFilename] : []}
            items={menuItems}
            onClick={({ key }) => onSelect(key)}
            style={{
                height: '100%',
                borderRight: 0,
                overflowY: 'auto',
            }}
        />
    );
};

export default ChapterNav;

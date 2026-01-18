/**
 * BookCard component - displays a book's title and description
 */

import React from 'react';
import { Card, Tag } from 'antd';
import { BookOutlined, FileTextOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { Book } from '../api';

interface BookCardProps {
    book: Book;
}

const BookCard: React.FC<BookCardProps> = ({ book }) => {
    const navigate = useNavigate();

    const handleClick = () => {
        navigate(`/books/${book.id}`);
    };

    return (
        <Card
            hoverable
            onClick={handleClick}
            style={{ height: '100%' }}
            cover={
                <div
                    style={{
                        height: 150,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    }}
                >
                    <BookOutlined style={{ fontSize: 64, color: 'rgba(255,255,255,0.9)' }} />
                </div>
            }
        >
            <Card.Meta
                title={
                    <div style={{
                        whiteSpace: 'normal',
                        wordBreak: 'break-word',
                        lineHeight: 1.4,
                    }}>
                        {book.title}
                    </div>
                }
                description={
                    <div>
                        <p style={{
                            marginBottom: 12,
                            color: '#666',
                            lineHeight: 1.6,
                        }}>
                            {book.description}
                        </p>
                        <div>
                            {book.has_chapters ? (
                                <Tag color="green" icon={<FileTextOutlined />}>
                                    Extracted
                                </Tag>
                            ) : (
                                <Tag color="orange">Pending</Tag>
                            )}
                        </div>
                    </div>
                }
            />
        </Card>
    );
};

export default BookCard;

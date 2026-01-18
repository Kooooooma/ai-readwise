/**
 * HomePage - displays all books as cards
 */

import React, { useEffect } from 'react';
import { Row, Col, Typography, Spin, Empty, Alert } from 'antd';
import { BookOutlined } from '@ant-design/icons';
import BookCard from '../components/BookCard';
import { useBookStore } from '../store/useBookStore';

const { Title } = Typography;

const HomePage: React.FC = () => {
    const { books, booksLoading, booksError, loadBooks } = useBookStore();

    useEffect(() => {
        loadBooks();
    }, [loadBooks]);

    return (
        <div style={{ padding: '24px 48px' }}>
            <div style={{ textAlign: 'center', marginBottom: 48 }}>
                <Title level={2} style={{ marginBottom: 8 }}>
                    <BookOutlined style={{ marginRight: 12 }} />
                    AI Readwise
                </Title>
                <Typography.Text type="secondary">
                    Convert PDF e-books to Markdown for reading anywhere
                </Typography.Text>
            </div>

            {booksError && (
                <Alert
                    type="error"
                    message="Loading Failed"
                    description={booksError}
                    style={{ marginBottom: 24 }}
                />
            )}

            {booksLoading ? (
                <div style={{ textAlign: 'center', padding: 48 }}>
                    <Spin size="large" />
                </div>
            ) : books.length === 0 ? (
                <Empty
                    description="No books available"
                    style={{ marginTop: 48 }}
                />
            ) : (
                <Row gutter={[24, 24]}>
                    {books.map((book) => (
                        <Col key={book.id} xs={24} sm={12} md={8} lg={6}>
                            <BookCard book={book} />
                        </Col>
                    ))}
                </Row>
            )}
        </div>
    );
};

export default HomePage;

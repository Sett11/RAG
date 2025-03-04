CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS my_table (
    id SERIAL PRIMARY KEY,
    vector_column vector(5)
);
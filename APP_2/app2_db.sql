CREATE EXTENSION vector;
CREATE TABLE word_emb (id bigserial PRIMARY KEY, word text, embedding vector(100));
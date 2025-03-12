from gensim.models import Word2Vec
import psycopg2
import os
from re import findall,sub

DATABASE_URL = os.environ.get('DATABASE_URL','postgresql://postgres:password@localhost:5432/my_emb_db')

# sentences=[]

# with open('text.txt','r',encoding='utf-8') as s:
#     for i in s:
#         t=sub(r'.*?\[.*?\].*?','',i.lower()).strip()
#         c=t.replace(' ','').replace('\n','')
#         if c:
#             sentences.append([j for j in findall(r'\b[а-яa-z]+\b',t) if len(j)>3])

# model=Word2Vec(sentences, vector_size=100, window=10, min_count=1, workers=4)
# model.train(sentences, total_examples=model.corpus_count, epochs=10)

# conn = psycopg2.connect(DATABASE_URL)
# cursor = conn.cursor()

# for word in model.wv.index_to_key:
#     embedding = model.wv[word]
#     cursor.execute("INSERT INTO word_emb (word, embedding) VALUES (%s, %s)",(word, embedding.tolist()))

# conn.commit()
# cursor.close()
# conn.close()

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

N,M=10,20
cursor.execute("SELECT * FROM word_emb WHERE id > %s AND id < %s", (N,M))

rows = cursor.fetchall()
for row in rows:
    print(row[0],row[1])

cursor.execute("SELECT COUNT(*) FROM word_emb;")
print(cursor.fetchone()[0])

cursor.close()
conn.close()
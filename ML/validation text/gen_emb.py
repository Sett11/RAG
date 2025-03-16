from gensim.models import Word2Vec
from re import findall,sub

def gen_dict_emb():
    sentences,d_sentences=[],{}

    with open('texts/text_AUTHOR.txt','r',encoding='utf-8') as s:
        for i in s:
            t=sub(r'.*?\[.*?\].*?','',i.lower()).strip()
            c=t.replace(' ','').replace('\n','')
            if c:
                sentences.append([j for j in findall(r'\b[а-яa-z]+\b',t) if len(j)>3])

    model=Word2Vec(sentences, vector_size=100, window=10, min_count=1, workers=4)
    model.train(sentences, total_examples=model.corpus_count, epochs=10)

    for word in model.wv.index_to_key:
        embedding = model.wv[word]
        d_sentences[word]=embedding

    return d_sentences
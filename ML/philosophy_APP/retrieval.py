store={'скиба':'skiba','адуло':'ad','колесников':'kol','косенков':'kos','лазаревич':'laz'}
cache=set()

def search_valid_text(names=[]):
    global cache
    ouput=''
    for name in names:
        if name not in cache:
            with open(f'texts\{store[name]}.txt','r',encoding='utf-8') as s:
                ouput+=f'{s.read()}\n'
            cache.add(name)
    return ouput
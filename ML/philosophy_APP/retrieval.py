store={'скиба':'skiba','адуло':'ad','колесников':'kol','косенков':'kos','лазаревич':'laz'}

def search_valid_text(names=[]):
    ouput=''
    for i in names:
        with open(f'texts\{store[i]}.txt','r',encoding='utf-8') as s:
            ouput+=f'{s.read()}\n'
    return ouput
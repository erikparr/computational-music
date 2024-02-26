from music21 import corpus

def list_composers():
    return corpus.corpora.CoreCorpus().getComposerNames()

# Usage
composer_list = list_composers()
print(composer_list)

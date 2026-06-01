from common import preprocess_text


def test_preprocess_text():
    # Make sure nltk data is downloaded or mocked
    import nltk

    from core.config import settings
    nltk.data.path.append(settings.NLTK_DATA_PATH)
    try:
        nltk.corpus.stopwords.words("english")
    except LookupError:
        nltk.download("stopwords", download_dir=settings.NLTK_DATA_PATH)
        nltk.download("punkt", download_dir=settings.NLTK_DATA_PATH)
        
    text = "The quick brown fox jumps over the lazy dog! 123"
    processed = preprocess_text(text)
    
    # "the", "over" might be stopwords. "123", "!" should be removed.
    assert "123" not in processed
    assert "!" not in processed
    assert "the" not in processed.split()
    assert "quick" in processed.split()

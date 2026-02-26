from medicare_news_digest import extract_article_candidates, summarize_text


def test_extract_article_candidates_filters_and_deduplicates():
    html = """
    <html><body>
      <article><a href="/story-1/">A valid story title with enough words</a></article>
      <article><a href="/story-1/">A valid story title with enough words</a></article>
      <h2><a href="https://example.com/outside">Outside site story title</a></h2>
      <h3><a href="/topics/medicare/">Topic page link that should be ignored</a></h3>
    </body></html>
    """
    found = extract_article_candidates(html, base_url="https://kffhealthnews.org/topics/medicare/")
    assert len(found) == 1
    assert found[0].url == "https://kffhealthnews.org/story-1/"


def test_summarize_text_returns_first_sentences():
    text = (
        "First useful sentence has enough words for extraction and summary. "
        "Second useful sentence has enough words for extraction and summary. "
        "Third useful sentence has enough words for extraction and summary. "
        "Fourth useful sentence has enough words for extraction and summary."
    )
    summary = summarize_text(text, max_sentences=3)
    assert "First useful sentence" in summary
    assert "Second useful sentence" in summary
    assert "Third useful sentence" in summary
    assert "Fourth useful sentence" not in summary

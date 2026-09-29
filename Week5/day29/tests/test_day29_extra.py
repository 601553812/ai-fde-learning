"""One independent edge-case test belongs to the learner."""

from Week5.day29.code.chunking import Document, chunk_document, Chunk


def test_high_overlap_still_advances_and_finishes() -> None:
    document = Document("edge.txt", "ABCDE")
    chunks = chunk_document(document,max_chars=3,overlap_chars=2)
    result = []
    i = 0
    for chunk in chunks:
        start = chunk.start
        end = chunk.end
        text = chunk.text
        result.append((start,end,text))
        assert chunk.text==document.text[start:end]
        assert chunk.chunk_index == i
        i += 1
    assert result == [(0,3,"ABC"),(1,4,"BCD"),(2,5,"CDE")]

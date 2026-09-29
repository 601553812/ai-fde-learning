import pytest

from Week5.day29.code.chunking import Document, chunk_document, chunk_documents


def test_short_text_keeps_source_and_exact_offsets() -> None:
    document = Document("faq.txt", "返品は30日以内。")

    chunks = chunk_document(document, max_chars=20, overlap_chars=3)

    assert len(chunks) == 1
    assert chunks[0].source_name == "faq.txt"
    assert (chunks[0].chunk_index, chunks[0].start, chunks[0].end) == (
        0, 0, len(document.text)
    )
    assert chunks[0].text == document.text[chunks[0].start : chunks[0].end]


def test_overlap_and_last_short_chunk() -> None:
    document = Document("faq.txt", "ABCDEFGHIJK")

    chunks = chunk_document(document, max_chars=5, overlap_chars=2)

    assert [(chunk.start, chunk.end, chunk.text) for chunk in chunks] == [
        (0, 5, "ABCDE"),
        (3, 8, "DEFGH"),
        (6, 11, "GHIJK"),
    ]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]


def test_exact_boundary_does_not_make_duplicate_tail() -> None:
    chunks = chunk_document(Document("exact.txt", "ABCDE"), 5, 2)

    assert [(chunk.start, chunk.end, chunk.text) for chunk in chunks] == [
        (0, 5, "ABCDE")
    ]


def test_empty_document_has_no_chunks() -> None:
    assert chunk_document(Document("empty.txt", ""), 5, 2) == []


@pytest.mark.parametrize("max_chars,overlap_chars", [(0, 0), (-1, 0), (5, -1), (5, 5), (5, 6)])
def test_invalid_size_fails_before_slicing(max_chars: int, overlap_chars: int) -> None:
    with pytest.raises(ValueError, match="^invalid_chunk_size$"):
        chunk_document(Document("faq.txt", "ABCDE"), max_chars, overlap_chars)


def test_multiple_documents_preserve_order_and_restart_index() -> None:
    chunks = chunk_documents(
        [Document("faq.txt", "ABCDE"), Document("ticket.txt", "故障")], 3, 1
    )

    assert [(chunk.source_name, chunk.chunk_index, chunk.text) for chunk in chunks] == [
        ("faq.txt", 0, "ABC"),
        ("faq.txt", 1, "CDE"),
        ("ticket.txt", 0, "故障"),
    ]


def test_offsets_recover_each_chunk_from_original_text() -> None:
    document = Document("jp.txt", "受付時間は9時から18時です。")

    chunks = chunk_document(document, 6, 2)

    assert chunks
    assert all(chunk.text == document.text[chunk.start : chunk.end] for chunk in chunks)
    assert chunks[0].start == 0
    assert chunks[-1].end == len(document.text)

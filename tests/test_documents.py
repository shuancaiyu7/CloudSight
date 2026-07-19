import unittest

from services.documents import Document, chunk_documents, load_builtin_documents


class DocumentTests(unittest.TestCase):
    def test_builtin_handbook_covers_eight_incident_types(self):
        documents = load_builtin_documents()

        self.assertEqual(8, len(documents))
        self.assertTrue(all(document.source for document in documents))
        self.assertTrue(all(document.content for document in documents))

    def test_chunking_keeps_the_source_for_each_chunk(self):
        document = Document(
            source="demo.md",
            title="演示手册",
            content="第一段内容。\n\n第二段内容。\n\n第三段内容。",
        )

        chunks = chunk_documents([document], chunk_size=10, overlap=0)

        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(all(chunk.source == "demo.md" for chunk in chunks))


if __name__ == "__main__":
    unittest.main()

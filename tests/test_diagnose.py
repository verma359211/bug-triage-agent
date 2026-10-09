import unittest

from agent.nodes.diagnose import Citation, Diagnosis, _recover_diagnosis, _valid_citations


class CitationValidationTests(unittest.TestCase):
    def test_builds_evidence_from_simple_line_numbers(self):
        diagnosis = Diagnosis(
            file="src/service.js",
            cause="The comparison accepts zero.",
            reasoning="The condition conflicts with the contract.",
            reproduction_matches=True,
            evidence_lines=[4],
        )

        citations = _valid_citations(
            diagnosis, {"src/service.js": "src/service.js:4: if (stock >= 0)"}
        )

        self.assertEqual(citations[0]["explanation"], "if (stock >= 0)")

    def test_keeps_only_citations_visible_in_loaded_source(self):
        diagnosis = Diagnosis(
            file="src/service.js",
            cause="The comparison accepts zero.",
            reasoning="The cited condition conflicts with the contract.",
            reproduction_matches=True,
            evidence=[
                Citation(file="src/service.js", line=4, explanation="Faulty condition").model_dump(),
                Citation(file="src/service.js", line=99, explanation="Invented line").model_dump(),
            ],
            additional_files=[],
        )
        files = {"src/service.js": "src/service.js:4: if (stock >= 0)"}

        citations = _valid_citations(diagnosis, files)

        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]["line"], 4)

    def test_recovers_nested_citation_shape(self):
        diagnosis = Diagnosis(
            file="src/service.js",
            cause="The comparison accepts zero.",
            reasoning="The cited condition conflicts with the contract.",
            reproduction_matches=True,
            evidence=[
                {"": {"file": "src/service.js", "line": 4, "explanation": "Faulty"}}
            ],
        )

        citations = _valid_citations(
            diagnosis, {"src/service.js": "src/service.js:4: if (stock >= 0)"}
        )

        self.assertEqual(citations[0]["file"], "src/service.js")

    def test_recovers_single_item_list_from_parser_error(self):
        error = RuntimeError("parse failed")
        error.llm_output = (
            '[{"file":"src/service.js","cause":"bad check","reasoning":"visible",'
            '"reproduction_matches":true,"evidence_lines":[4]}]'
        )

        diagnosis = _recover_diagnosis(error)

        self.assertEqual(diagnosis.file, "src/service.js")


if __name__ == "__main__":
    unittest.main()

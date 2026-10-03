from app.ingestion.concept_mapper import ConceptAliasMapper


def test_explicit_and_alias_mapping():
    mapper = ConceptAliasMapper(
        {
            "BIO.REPLICATION": ["tái bản dna", "dna replication"],
            "BIO.OKAZAKI": ["đoạn okazaki", "okazaki fragment"],
        }
    )
    ranked = mapper.rank(
        "Trong tái bản DNA, các đoạn Okazaki xuất hiện trên mạch chậm.",
        explicit_codes=["BIO.REPLICATION"],
    )
    codes = [item[0] for item in ranked]
    assert codes[0] == "BIO.REPLICATION"
    assert "BIO.OKAZAKI" in codes

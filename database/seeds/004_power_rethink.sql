-- POWER AI v0.8 — misconception catalogue and deterministic question-to-misconception evidence rules.

INSERT INTO misconceptions(id, code, concept_id, statement_vi, statement_en, correction_vi, correction_en) VALUES
('50000000-0000-0000-0000-000000000003','MIS_LIGASE_SYNTHESIS','20000000-0000-0000-0000-000000000007','DNA ligase tổng hợp phần lớn nucleotide của các đoạn Okazaki.','DNA ligase synthesizes most nucleotides of Okazaki fragments.','DNA polymerase tổng hợp DNA; DNA ligase chủ yếu nối các đoạn DNA đã được tổng hợp.','DNA polymerase synthesizes DNA; DNA ligase primarily joins already-synthesized DNA fragments.'),
('50000000-0000-0000-0000-000000000004','MIS_BOTH_STRANDS_CONTINUOUS','20000000-0000-0000-0000-000000000003','Hai mạch DNA mới đều được tổng hợp liên tục tại chạc tái bản.','Both new DNA strands are synthesized continuously at a replication fork.','Do hai mạch khuôn ngược chiều và DNA polymerase chỉ tổng hợp 5′→3′, một mạch mới liên tục còn mạch kia gián đoạn.','Because templates are antiparallel and DNA polymerase synthesizes only 5′→3′, one new strand is continuous and the other discontinuous.')
ON CONFLICT (code) DO NOTHING;

INSERT INTO question_misconceptions(question_id, misconception_id, evidence_weight) VALUES
('40000000-0000-0000-0000-000000000001','50000000-0000-0000-0000-000000000001',0.55),
('40000000-0000-0000-0000-000000000005','50000000-0000-0000-0000-000000000001',0.55),
('40000000-0000-0000-0000-000000000002','50000000-0000-0000-0000-000000000002',0.45),
('40000000-0000-0000-0000-000000000006','50000000-0000-0000-0000-000000000002',0.65),
('40000000-0000-0000-0000-000000000003','50000000-0000-0000-0000-000000000003',0.50),
('40000000-0000-0000-0000-000000000008','50000000-0000-0000-0000-000000000003',0.70),
('40000000-0000-0000-0000-000000000004','50000000-0000-0000-0000-000000000004',0.65)
ON CONFLICT (question_id, misconception_id) DO UPDATE
SET evidence_weight = EXCLUDED.evidence_weight;

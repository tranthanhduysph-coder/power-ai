-- Deterministic demo identifiers make local API examples stable.

INSERT INTO subjects(id, code, name_vi, name_en)
VALUES ('10000000-0000-0000-0000-000000000001', 'BIOLOGY', 'Sinh học', 'Biology')
ON CONFLICT (code) DO NOTHING;

INSERT INTO grades(id, subject_id, level, name_vi, name_en)
VALUES ('11000000-0000-0000-0000-000000000010', '10000000-0000-0000-0000-000000000001', 10, 'Sinh học 10', 'Biology 10')
ON CONFLICT (subject_id, level) DO NOTHING;

INSERT INTO curriculum_units(id, subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order)
VALUES (
    '12000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    '11000000-0000-0000-0000-000000000010',
    NULL,
    'B10_NUCLEIC_ACIDS',
    'Nucleic acid',
    'Nucleic acids',
    1
)
ON CONFLICT (code) DO NOTHING;

INSERT INTO curriculum_units(id, subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order)
VALUES (
    '12000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '11000000-0000-0000-0000-000000000010',
    '12000000-0000-0000-0000-000000000001',
    'B10_DNA_REPLICATION',
    'Tái bản DNA',
    'DNA replication',
    1
)
ON CONFLICT (code) DO NOTHING;

INSERT INTO concepts(id, code, parent_id, name_vi, name_en, description_vi, description_en) VALUES
('20000000-0000-0000-0000-000000000001', 'BIO.DNA', NULL, 'DNA', 'DNA', 'Phân tử mang thông tin di truyền.', 'A molecule that stores genetic information.'),
('20000000-0000-0000-0000-000000000002', 'BIO.DNA.STRUCTURE', '20000000-0000-0000-0000-000000000001', 'Cấu trúc DNA', 'DNA structure', 'DNA gồm hai mạch polynucleotide ngược chiều.', 'DNA consists of two antiparallel polynucleotide strands.'),
('20000000-0000-0000-0000-000000000003', 'BIO.DNA.REPLICATION', '20000000-0000-0000-0000-000000000001', 'Tái bản DNA', 'DNA replication', 'Quá trình tạo bản sao DNA.', 'The process that produces copies of DNA.'),
('20000000-0000-0000-0000-000000000004', 'BIO.DNA.REPLICATION.POLYMERASE', '20000000-0000-0000-0000-000000000003', 'DNA polymerase', 'DNA polymerase', 'Enzyme kéo dài mạch DNA mới theo chiều 5′→3′.', 'An enzyme that extends new DNA in the 5′→3′ direction.'),
('20000000-0000-0000-0000-000000000005', 'BIO.DNA.REPLICATION.LEADING', '20000000-0000-0000-0000-000000000003', 'Mạch dẫn đầu', 'Leading strand', 'Mạch mới được tổng hợp liên tục.', 'The new strand synthesized continuously.'),
('20000000-0000-0000-0000-000000000006', 'BIO.DNA.REPLICATION.LAGGING', '20000000-0000-0000-0000-000000000003', 'Mạch chậm', 'Lagging strand', 'Mạch mới được tổng hợp gián đoạn.', 'The new strand synthesized discontinuously.'),
('20000000-0000-0000-0000-000000000007', 'BIO.DNA.REPLICATION.OKAZAKI', '20000000-0000-0000-0000-000000000003', 'Đoạn Okazaki', 'Okazaki fragment', 'Các đoạn DNA ngắn được tổng hợp trên mạch chậm.', 'Short DNA segments synthesized on the lagging strand.')
ON CONFLICT (code) DO NOTHING;

INSERT INTO concept_relations(source_concept_id, target_concept_id, relation_type) VALUES
('20000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000003', 'prerequisite'),
('20000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000005', 'related'),
('20000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000006', 'related')
ON CONFLICT DO NOTHING;

INSERT INTO curriculum_concepts(curriculum_unit_id, concept_id, is_core) VALUES
('12000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000002', true),
('12000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000003', true),
('12000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000004', true),
('12000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000005', true),
('12000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000006', true),
('12000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000007', true)
ON CONFLICT DO NOTHING;

INSERT INTO sources(id, code, title, language, grade_level, source_role, license_status) VALUES
('30000000-0000-0000-0000-000000000010', 'BIO10_KNTT', 'Sinh học 10 - Kết nối tri thức', 'vi', 10, 'curriculum', 'private_reference'),
('30000000-0000-0000-0000-000000000011', 'BIO11_KNTT', 'Sinh học 11 - Kết nối tri thức', 'vi', 11, 'curriculum', 'private_reference'),
('30000000-0000-0000-0000-000000000012', 'BIO12_KNTT', 'Sinh học 12 - Kết nối tri thức', 'vi', 12, 'curriculum', 'private_reference'),
('30000000-0000-0000-0000-000000000013', 'CAMPBELL_BIOLOGY', 'Campbell Biology', 'en', NULL, 'reference', 'private_reference')
ON CONFLICT (code) DO NOTHING;

-- Questions: 4 MCQ, 4 true/false, 4 short-answer.
INSERT INTO questions(id, code, question_type, difficulty, cognitive_level, stem_vi, stem_en, answer_json, explanation_vi, explanation_en, source_basis, review_status) VALUES
('40000000-0000-0000-0000-000000000001','DNA_MCQ_01','mcq','easy','understand','DNA polymerase tổng hợp mạch DNA mới theo chiều nào?','In which direction does DNA polymerase synthesize a new DNA strand?','{"option":"B"}','DNA polymerase chỉ gắn nucleotide vào đầu 3′-OH nên mạch mới kéo dài theo chiều 5′→3′.','DNA polymerase adds nucleotides to the 3′-OH end, so the new strand grows 5′→3′.','POWER seed','approved'),
('40000000-0000-0000-0000-000000000002','DNA_MCQ_02','mcq','medium','understand','Đặc điểm nào phân biệt trực tiếp mạch chậm với mạch dẫn đầu?','Which feature directly distinguishes the lagging strand from the leading strand?','{"option":"C"}','Mạch chậm được tổng hợp gián đoạn thành các đoạn Okazaki.','The lagging strand is synthesized discontinuously as Okazaki fragments.','POWER seed','approved'),
('40000000-0000-0000-0000-000000000003','DNA_MCQ_03','mcq','medium','apply','Nếu hoạt tính DNA ligase bị ức chế, cấu trúc nào có khả năng tích lũy nhiều nhất?','If DNA ligase activity is inhibited, which structure is most likely to accumulate?','{"option":"D"}','DNA ligase nối các đoạn Okazaki; khi bị ức chế, các đoạn chưa nối sẽ tích lũy.','DNA ligase joins Okazaki fragments; without it, unjoined fragments accumulate.','POWER seed','approved'),
('40000000-0000-0000-0000-000000000004','DNA_MCQ_04','mcq','hard','apply','Hai mạch khuôn ngược chiều nhưng DNA polymerase chỉ tổng hợp 5′→3′. Hệ quả trực tiếp là gì?','The templates are antiparallel but DNA polymerase synthesizes only 5′→3′. What is the direct consequence?','{"option":"A"}','Một mạch được tổng hợp liên tục và mạch kia gián đoạn.','One new strand is synthesized continuously and the other discontinuously.','POWER seed','approved'),
('40000000-0000-0000-0000-000000000005','DNA_TF_01','true_false','easy','understand','Cả mạch dẫn đầu và mạch chậm đều được tổng hợp theo chiều 5′→3′.','Both the leading and lagging strands are synthesized in the 5′→3′ direction.','{"value":true}','Đúng. Khác biệt nằm ở tính liên tục, không phải chiều hóa học của tổng hợp.','True. They differ in continuity, not in the chemical direction of synthesis.','POWER seed','approved'),
('40000000-0000-0000-0000-000000000006','DNA_TF_02','true_false','easy','understand','Các đoạn Okazaki hình thành trên mạch dẫn đầu.','Okazaki fragments form on the leading strand.','{"value":false}','Sai. Các đoạn Okazaki hình thành trên mạch chậm.','False. Okazaki fragments form on the lagging strand.','POWER seed','approved'),
('40000000-0000-0000-0000-000000000007','DNA_TF_03','true_false','medium','apply','Nếu DNA polymerase có thể tổng hợp DNA theo cả hai chiều thì nhu cầu tổng hợp gián đoạn trên một mạch có thể không còn như hiện nay.','If DNA polymerase could synthesize DNA in both directions, the current need for discontinuous synthesis on one strand could disappear.','{"value":true}','Đúng về mặt giả định: tính 5′→3′ của polymerase kết hợp với tính ngược chiều của DNA tạo ra cơ chế mạch chậm.','True as a hypothetical: 5′→3′ polymerase activity combined with antiparallel DNA creates the lagging-strand mechanism.','POWER seed','approved'),
('40000000-0000-0000-0000-000000000008','DNA_TF_04','true_false','medium','understand','DNA ligase chịu trách nhiệm tổng hợp phần lớn nucleotide của các đoạn Okazaki.','DNA ligase synthesizes most nucleotides in Okazaki fragments.','{"value":false}','Sai. DNA polymerase tổng hợp DNA; ligase chủ yếu nối các đoạn DNA.','False. DNA polymerase synthesizes DNA; ligase primarily joins DNA fragments.','POWER seed','approved'),
('40000000-0000-0000-0000-000000000009','DNA_SA_01','short_answer','easy','remember','Một phân tử DNA mẹ sau một lần tái bản tạo ra bao nhiêu phân tử DNA con? Chỉ nhập số.','How many daughter DNA molecules are produced from one parental DNA molecule after one round of replication? Enter a number only.','{"value":"2"}','Một lần tái bản tạo hai phân tử DNA con.','One round of replication produces two daughter DNA molecules.','POWER seed','approved'),
('40000000-0000-0000-0000-000000000010','DNA_SA_02','short_answer','medium','apply','Một chạc tái bản đang hoạt động có bao nhiêu mạch mới được tổng hợp liên tục? Chỉ nhập số.','At one active replication fork, how many new strands are synthesized continuously? Enter a number only.','{"value":"1"}','Tại một chạc tái bản, một mạch mới là mạch dẫn đầu và được tổng hợp liên tục.','At one replication fork, one new strand is the continuously synthesized leading strand.','POWER seed','approved'),
('40000000-0000-0000-0000-000000000011','DNA_SA_03','short_answer','medium','apply','Nếu một đoạn DNA mới có 5 đoạn Okazaki cần nối với nhau thành một đoạn liên tục, tối thiểu có bao nhiêu vị trí nối giữa các đoạn? Chỉ nhập số.','If 5 Okazaki fragments must be joined into one continuous segment, what is the minimum number of joins between fragments? Enter a number only.','{"value":"4"}','N đoạn rời nhau cần tối thiểu N−1 vị trí nối để thành một đoạn liên tục.','N separate fragments require at least N−1 joins to form one continuous segment.','POWER seed','approved'),
('40000000-0000-0000-0000-000000000012','DNA_SA_04','short_answer','hard','apply','Một phân tử DNA trải qua 3 vòng tái bản liên tiếp, giả sử mọi phân tử con đều tiếp tục tái bản. Có bao nhiêu phân tử DNA sau cùng? Chỉ nhập số.','A DNA molecule undergoes 3 consecutive rounds of replication, with every daughter molecule continuing to replicate. How many DNA molecules are present at the end? Enter a number only.','{"value":"8"}','Số phân tử tăng gấp đôi sau mỗi vòng: 2^3 = 8.','The number doubles each round: 2^3 = 8.','POWER seed','approved')
ON CONFLICT (code) DO NOTHING;

INSERT INTO question_options(question_id, option_key, text_vi, text_en, is_correct) VALUES
('40000000-0000-0000-0000-000000000001','A','3′→5′','3′→5′',false),
('40000000-0000-0000-0000-000000000001','B','5′→3′','5′→3′',true),
('40000000-0000-0000-0000-000000000001','C','Theo cả hai chiều','In both directions',false),
('40000000-0000-0000-0000-000000000001','D','Không có chiều xác định','No fixed direction',false),
('40000000-0000-0000-0000-000000000002','A','Có nhiều loại nucleotide hơn','It contains more nucleotide types',false),
('40000000-0000-0000-0000-000000000002','B','Được tổng hợp theo chiều 3′→5′','It is synthesized 3′→5′',false),
('40000000-0000-0000-0000-000000000002','C','Được tổng hợp gián đoạn','It is synthesized discontinuously',true),
('40000000-0000-0000-0000-000000000002','D','Không cần DNA polymerase','It does not require DNA polymerase',false),
('40000000-0000-0000-0000-000000000003','A','Các nucleotide tự do','Free nucleotides',false),
('40000000-0000-0000-0000-000000000003','B','Các chạc tái bản','Replication forks',false),
('40000000-0000-0000-0000-000000000003','C','Các mạch dẫn đầu hoàn chỉnh','Completed leading strands',false),
('40000000-0000-0000-0000-000000000003','D','Các đoạn Okazaki chưa được nối','Unjoined Okazaki fragments',true),
('40000000-0000-0000-0000-000000000004','A','Một mạch liên tục, một mạch gián đoạn','One strand continuous, one discontinuous',true),
('40000000-0000-0000-0000-000000000004','B','Cả hai mạch đều 3′→5′','Both strands are synthesized 3′→5′',false),
('40000000-0000-0000-0000-000000000004','C','Không cần primer','No primer is needed',false),
('40000000-0000-0000-0000-000000000004','D','DNA mất tính bổ sung','DNA loses complementarity',false)
ON CONFLICT (question_id, option_key) DO NOTHING;

INSERT INTO question_concepts(question_id, concept_id, is_primary) VALUES
('40000000-0000-0000-0000-000000000001','20000000-0000-0000-0000-000000000004',true),
('40000000-0000-0000-0000-000000000002','20000000-0000-0000-0000-000000000006',true),
('40000000-0000-0000-0000-000000000003','20000000-0000-0000-0000-000000000007',true),
('40000000-0000-0000-0000-000000000004','20000000-0000-0000-0000-000000000003',true),
('40000000-0000-0000-0000-000000000005','20000000-0000-0000-0000-000000000004',true),
('40000000-0000-0000-0000-000000000006','20000000-0000-0000-0000-000000000007',true),
('40000000-0000-0000-0000-000000000007','20000000-0000-0000-0000-000000000006',true),
('40000000-0000-0000-0000-000000000008','20000000-0000-0000-0000-000000000007',true),
('40000000-0000-0000-0000-000000000009','20000000-0000-0000-0000-000000000003',true),
('40000000-0000-0000-0000-000000000010','20000000-0000-0000-0000-000000000005',true),
('40000000-0000-0000-0000-000000000011','20000000-0000-0000-0000-000000000007',true),
('40000000-0000-0000-0000-000000000012','20000000-0000-0000-0000-000000000003',true)
ON CONFLICT DO NOTHING;

INSERT INTO misconceptions(id, code, concept_id, statement_vi, statement_en, correction_vi, correction_en) VALUES
('50000000-0000-0000-0000-000000000001','MIS_DNA_DIRECTION','20000000-0000-0000-0000-000000000004','DNA polymerase tổng hợp DNA theo chiều 3′→5′.','DNA polymerase synthesizes DNA in the 3′→5′ direction.','DNA polymerase tổng hợp mạch mới theo chiều 5′→3′.','DNA polymerase synthesizes the new strand in the 5′→3′ direction.'),
('50000000-0000-0000-0000-000000000002','MIS_OKAZAKI_LEADING','20000000-0000-0000-0000-000000000007','Các đoạn Okazaki nằm trên mạch dẫn đầu.','Okazaki fragments occur on the leading strand.','Các đoạn Okazaki hình thành trên mạch chậm.','Okazaki fragments form on the lagging strand.')
ON CONFLICT (code) DO NOTHING;

INSERT INTO products(id, code, name_vi, name_en) VALUES
('60000000-0000-0000-0000-000000000001','POWER_BIOLOGY','POWER Sinh học','POWER Biology')
ON CONFLICT (code) DO NOTHING;

INSERT INTO plans(id, product_id, code, name_vi, name_en, billing_period, price_amount, currency) VALUES
('61000000-0000-0000-0000-000000000001','60000000-0000-0000-0000-000000000001','BIOLOGY_FREE','Miễn phí','Free','free',0,'VND')
ON CONFLICT (code) DO NOTHING;

INSERT INTO plan_entitlements(plan_id, feature_code, enabled, limit_value) VALUES
('61000000-0000-0000-0000-000000000001','ai_tutor',true,20),
('61000000-0000-0000-0000-000000000001','adaptive_practice',true,5),
('61000000-0000-0000-0000-000000000001','progress_analytics',true,NULL)
ON CONFLICT (plan_id, feature_code) DO NOTHING;

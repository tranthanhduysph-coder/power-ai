-- POWER AI v0.9 — KNTT Biology 10–12 curriculum catalog skeleton and database-owned DNA POWER blueprint.


INSERT INTO grades(subject_id, level, name_vi, name_en)
SELECT id, 10, 'Sinh học 10', 'Biology 10' FROM subjects WHERE code='BIOLOGY'
ON CONFLICT (subject_id, level) DO UPDATE SET name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en;
INSERT INTO grades(subject_id, level, name_vi, name_en)
SELECT id, 11, 'Sinh học 11', 'Biology 11' FROM subjects WHERE code='BIOLOGY'
ON CONFLICT (subject_id, level) DO UPDATE SET name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en;
INSERT INTO grades(subject_id, level, name_vi, name_en)
SELECT id, 12, 'Sinh học 12', 'Biology 12' FROM subjects WHERE code='BIOLOGY'
ON CONFLICT (subject_id, level) DO UPDATE SET name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en;

-- Hide v0.1 demo-only curriculum nodes from the real catalog.
UPDATE curriculum_units SET catalog_visible=false, unit_type='legacy', is_power_ready=false
WHERE code IN ('B10_NUCLEIC_ACIDS','B10_DNA_REPLICATION');


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, NULL, 'B10_INTRO', 'Phần mở đầu', 'Introduction', 1,
       'part', NULL, 5, 22,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_INTRO'), 'B10_L01_INTRO_BIOLOGY', 'Giới thiệu khái quát môn Sinh học', 'General introduction to Biology', 1,
       'lesson', 1, 5, 11,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_INTRO'), 'B10_L02_RESEARCH_LEARNING', 'Phương pháp nghiên cứu và học tập môn Sinh học', 'Methods for researching and learning Biology', 2,
       'lesson', 2, 12, 17,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_INTRO'), 'B10_L03_LEVELS_OF_LIFE', 'Các cấp độ tổ chức của thế giới sống', 'Levels of organization of the living world', 3,
       'lesson', 3, 18, 22,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, NULL, 'B10_PART_CELL_BIOLOGY', 'Phần một. Sinh học tế bào', 'Part One. Cell Biology', 2,
       'part', NULL, 23, 115,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_PART_CELL_BIOLOGY'), 'B10_CH01_CHEMICAL_COMPONENTS', 'Chương 1. Thành phần hoá học của tế bào', 'Chapter 1. Chemical components of the cell', 1,
       'chapter', NULL, 23, 43,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_PART_CELL_BIOLOGY'), 'B10_CH02_CELL_STRUCTURE', 'Chương 2. Cấu trúc tế bào', 'Chapter 2. Cell structure', 2,
       'chapter', NULL, 44, 63,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_PART_CELL_BIOLOGY'), 'B10_CH03_MEMBRANE_SIGNALING', 'Chương 3. Trao đổi chất qua màng và truyền tin tế bào', 'Chapter 3. Membrane transport and cell signaling', 3,
       'chapter', NULL, 64, 77,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_PART_CELL_BIOLOGY'), 'B10_CH04_CELL_METABOLISM', 'Chương 4. Chuyển hoá năng lượng trong tế bào', 'Chapter 4. Cellular energy metabolism', 4,
       'chapter', NULL, 78, 96,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_PART_CELL_BIOLOGY'), 'B10_CH05_CELL_CYCLE', 'Chương 5. Chu kì tế bào và phân bào', 'Chapter 5. Cell cycle and cell division', 5,
       'chapter', NULL, 97, 115,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH01_CHEMICAL_COMPONENTS'), 'B10_L04_ELEMENTS_WATER', 'Các nguyên tố hoá học và nước', 'Chemical elements and water', 4,
       'lesson', 4, 23, 27,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH01_CHEMICAL_COMPONENTS'), 'B10_L05_BIOMOLECULES', 'Các phân tử sinh học', 'Biological molecules', 5,
       'lesson', 5, 28, 40,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH01_CHEMICAL_COMPONENTS'), 'B10_L06_LAB_BIOMOLECULES', 'Thực hành: Nhận biết một số phân tử sinh học', 'Lab: Identifying selected biological molecules', 6,
       'practice', 6, 41, 43,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH02_CELL_STRUCTURE'), 'B10_L07_PROKARYOTIC_CELL', 'Tế bào nhân sơ', 'Prokaryotic cells', 7,
       'lesson', 7, 44, 47,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH02_CELL_STRUCTURE'), 'B10_L08_EUKARYOTIC_CELL', 'Tế bào nhân thực', 'Eukaryotic cells', 8,
       'lesson', 8, 48, 60,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH02_CELL_STRUCTURE'), 'B10_L09_LAB_CELL_OBSERVATION', 'Thực hành: Quan sát tế bào', 'Lab: Cell observation', 9,
       'practice', 9, 61, 63,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH03_MEMBRANE_SIGNALING'), 'B10_L10_MEMBRANE_TRANSPORT', 'Trao đổi chất qua màng tế bào', 'Transport across the cell membrane', 10,
       'lesson', 10, 64, 70,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH03_MEMBRANE_SIGNALING'), 'B10_L11_LAB_PLASMOLYSIS', 'Thực hành: Thí nghiệm co và phản co nguyên sinh', 'Lab: Plasmolysis and deplasmolysis', 11,
       'practice', 11, 71, 72,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH03_MEMBRANE_SIGNALING'), 'B10_L12_CELL_SIGNALING', 'Truyền tin tế bào', 'Cell signaling', 12,
       'lesson', 12, 73, 77,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH04_CELL_METABOLISM'), 'B10_L13_METABOLISM_OVERVIEW', 'Khái quát về chuyển hoá vật chất và năng lượng', 'Overview of metabolism and energy transformation', 13,
       'lesson', 13, 78, 84,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH04_CELL_METABOLISM'), 'B10_L14_CATABOLISM_ANABOLISM', 'Phân giải và tổng hợp các chất trong tế bào', 'Catabolism and anabolism in cells', 14,
       'lesson', 14, 85, 93,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH04_CELL_METABOLISM'), 'B10_L15_LAB_ENZYME', 'Thực hành: Thí nghiệm phân tích ảnh hưởng của một số yếu tố đến hoạt tính của enzyme và kiểm tra hoạt tính của enzyme amylase', 'Lab: Factors affecting enzyme activity and amylase activity', 15,
       'practice', 15, 94, 96,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH05_CELL_CYCLE'), 'B10_L16_CELL_CYCLE_MITOSIS', 'Chu kì tế bào và nguyên phân', 'Cell cycle and mitosis', 16,
       'lesson', 16, 97, 103,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH05_CELL_CYCLE'), 'B10_L17_MEIOSIS', 'Giảm phân', 'Meiosis', 17,
       'lesson', 17, 104, 107,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH05_CELL_CYCLE'), 'B10_L18_LAB_MITOSIS_MEIOSIS', 'Thực hành: Làm và quan sát tiêu bản quá trình nguyên phân và giảm phân', 'Lab: Preparing and observing mitosis and meiosis slides', 18,
       'practice', 18, 108, 109,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH05_CELL_CYCLE'), 'B10_L19_CELL_TECHNOLOGY', 'Công nghệ tế bào', 'Cell technology', 19,
       'lesson', 19, 110, 115,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, NULL, 'B10_PART_MICRO_VIRUS', 'Phần hai. Sinh học vi sinh vật và virus', 'Part Two. Microbiology and Viruses', 3,
       'part', NULL, 116, 157,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_PART_MICRO_VIRUS'), 'B10_CH06_MICROBIOLOGY', 'Chương 6. Sinh học vi sinh vật', 'Chapter 6. Microbiology', 6,
       'chapter', NULL, 116, 140,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_PART_MICRO_VIRUS'), 'B10_CH07_VIRUS', 'Chương 7. Virus', 'Chapter 7. Viruses', 7,
       'chapter', NULL, 141, 157,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH06_MICROBIOLOGY'), 'B10_L20_MICRO_DIVERSITY_METHODS', 'Sự đa dạng và phương pháp nghiên cứu vi sinh vật', 'Microbial diversity and research methods', 20,
       'lesson', 20, 116, 121,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH06_MICROBIOLOGY'), 'B10_L21_MICRO_METABOLISM_GROWTH', 'Trao đổi chất, sinh trưởng và sinh sản ở vi sinh vật', 'Microbial metabolism, growth and reproduction', 21,
       'lesson', 21, 122, 130,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH06_MICROBIOLOGY'), 'B10_L22_MICRO_ROLES_APPLICATIONS', 'Vai trò và ứng dụng của vi sinh vật', 'Roles and applications of microorganisms', 22,
       'lesson', 22, 131, 137,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH06_MICROBIOLOGY'), 'B10_L23_LAB_MICROBIOLOGY', 'Thực hành: Một số phương pháp nghiên cứu vi sinh vật thông dụng, tìm hiểu về các sản phẩm công nghệ vi sinh vật và làm một số sản phẩm lên men từ vi sinh vật', 'Lab: Common microbiology methods and microbial technology products', 23,
       'practice', 23, 138, 140,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH07_VIRUS'), 'B10_L24_VIRUS_OVERVIEW', 'Khái quát về virus', 'Overview of viruses', 24,
       'lesson', 24, 141, 144,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH07_VIRUS'), 'B10_L25_VIRUS_DISEASE_APPLICATIONS', 'Một số bệnh do virus và các thành tựu nghiên cứu ứng dụng virus', 'Viral diseases and achievements in virus applications', 25,
       'lesson', 25, 145, 154,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B10_CH07_VIRUS'), 'B10_L26_LAB_VIRUS_DISEASE', 'Thực hành: Điều tra một số bệnh do virus và tuyên truyền phòng chống bệnh', 'Lab: Surveying viral diseases and disease prevention communication', 26,
       'practice', 26, 155, 157,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=10
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, NULL, 'B11_PART_ORGANISM_BIOLOGY', 'Phần ba. Sinh học cơ thể', 'Part Three. Organismal Biology', 1,
       'part', NULL, 5, 186,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_PART_ORGANISM_BIOLOGY'), 'B11_CH01_METABOLISM_ENERGY', 'Chương 1. Trao đổi chất và chuyển hoá năng lượng ở sinh vật', 'Chapter 1. Metabolism and energy transformation in organisms', 1,
       'chapter', NULL, 5, 87,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_PART_ORGANISM_BIOLOGY'), 'B11_CH02_RESPONSES', 'Chương 2. Cảm ứng ở sinh vật', 'Chapter 2. Responses in organisms', 2,
       'chapter', NULL, 88, 124,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_PART_ORGANISM_BIOLOGY'), 'B11_CH03_GROWTH_DEVELOPMENT', 'Chương 3. Sinh trưởng và phát triển ở sinh vật', 'Chapter 3. Growth and development in organisms', 3,
       'chapter', NULL, 125, 155,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_PART_ORGANISM_BIOLOGY'), 'B11_CH04_REPRODUCTION', 'Chương 4. Sinh sản ở sinh vật', 'Chapter 4. Reproduction in organisms', 4,
       'chapter', NULL, 156, 182,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_PART_ORGANISM_BIOLOGY'), 'B11_CH05_INTEGRATION_CAREERS', 'Chương 5. Mối quan hệ giữa các quá trình sinh lí trong cơ thể sinh vật và một số ngành nghề liên quan đến sinh học cơ thể', 'Chapter 5. Integration of physiological processes and related careers', 5,
       'chapter', NULL, 183, 186,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L01_METABOLISM_OVERVIEW', 'Khái quát về trao đổi chất và chuyển hoá năng lượng', 'Overview of metabolism and energy transformation', 1,
       'lesson', 1, 5, 8,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L02_WATER_MINERALS_PLANTS', 'Trao đổi nước và khoáng ở thực vật', 'Water and mineral exchange in plants', 2,
       'lesson', 2, 9, 20,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L03_LAB_WATER_MINERALS', 'Thực hành: Trao đổi nước và khoáng ở thực vật', 'Lab: Water and mineral exchange in plants', 3,
       'practice', 3, 21, 25,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L04_PHOTOSYNTHESIS', 'Quang hợp ở thực vật', 'Photosynthesis in plants', 4,
       'lesson', 4, 26, 34,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L05_LAB_PHOTOSYNTHESIS', 'Thực hành: Quang hợp ở thực vật', 'Lab: Photosynthesis in plants', 5,
       'practice', 5, 35, 37,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L06_PLANT_RESPIRATION', 'Hô hấp ở thực vật', 'Respiration in plants', 6,
       'lesson', 6, 38, 43,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L07_LAB_PLANT_RESPIRATION', 'Thực hành: Hô hấp ở thực vật', 'Lab: Respiration in plants', 7,
       'practice', 7, 44, 45,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L08_ANIMAL_NUTRITION_DIGESTION', 'Dinh dưỡng và tiêu hoá ở động vật', 'Nutrition and digestion in animals', 8,
       'lesson', 8, 46, 53,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L09_ANIMAL_RESPIRATION', 'Hô hấp ở động vật', 'Respiration in animals', 9,
       'lesson', 9, 54, 60,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L10_ANIMAL_CIRCULATION', 'Tuần hoàn ở động vật', 'Circulation in animals', 10,
       'lesson', 10, 61, 68,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L11_LAB_CIRCULATION', 'Thực hành: Một số thí nghiệm về hệ tuần hoàn', 'Lab: Selected experiments on the circulatory system', 11,
       'practice', 11, 69, 71,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L12_ANIMAL_IMMUNITY', 'Miễn dịch ở động vật', 'Immunity in animals', 12,
       'lesson', 12, 72, 79,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH01_METABOLISM_ENERGY'), 'B11_L13_EXCRETION_HOMEOSTASIS', 'Bài tiết và cân bằng nội môi', 'Excretion and homeostasis', 13,
       'lesson', 13, 80, 87,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH02_RESPONSES'), 'B11_L14_RESPONSE_OVERVIEW', 'Khái quát về cảm ứng ở sinh vật', 'Overview of responses in organisms', 14,
       'lesson', 14, 88, 89,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH02_RESPONSES'), 'B11_L15_PLANT_RESPONSES', 'Cảm ứng ở thực vật', 'Responses in plants', 15,
       'lesson', 15, 90, 96,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH02_RESPONSES'), 'B11_L16_LAB_PLANT_RESPONSES', 'Thực hành: Cảm ứng ở thực vật', 'Lab: Responses in plants', 16,
       'practice', 16, 97, 99,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH02_RESPONSES'), 'B11_L17_ANIMAL_RESPONSES', 'Cảm ứng ở động vật', 'Responses in animals', 17,
       'lesson', 17, 100, 114,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH02_RESPONSES'), 'B11_L18_ANIMAL_BEHAVIOR', 'Tập tính động vật', 'Animal behavior', 18,
       'lesson', 18, 115, 124,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH03_GROWTH_DEVELOPMENT'), 'B11_L19_GROWTH_DEVELOPMENT_OVERVIEW', 'Khái quát về sinh trưởng và phát triển ở sinh vật', 'Overview of growth and development in organisms', 19,
       'lesson', 19, 125, 128,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH03_GROWTH_DEVELOPMENT'), 'B11_L20_PLANT_GROWTH_DEVELOPMENT', 'Sinh trưởng và phát triển ở thực vật', 'Growth and development in plants', 20,
       'lesson', 20, 129, 140,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH03_GROWTH_DEVELOPMENT'), 'B11_L21_LAB_PRUNING_AGE', 'Thực hành: Bấm ngọn, tỉa cành, tính tuổi cây', 'Lab: Pinching, pruning and estimating plant age', 21,
       'practice', 21, 141, 144,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH03_GROWTH_DEVELOPMENT'), 'B11_L22_ANIMAL_GROWTH_DEVELOPMENT', 'Sinh trưởng và phát triển ở động vật', 'Growth and development in animals', 22,
       'lesson', 22, 145, 152,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH03_GROWTH_DEVELOPMENT'), 'B11_L23_LAB_METAMORPHOSIS', 'Thực hành: Quan sát quá trình biến thái ở động vật', 'Lab: Observing metamorphosis in animals', 23,
       'practice', 23, 153, 155,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH04_REPRODUCTION'), 'B11_L24_REPRODUCTION_OVERVIEW', 'Khái quát về sinh sản ở sinh vật', 'Overview of reproduction in organisms', 24,
       'lesson', 24, 156, 158,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH04_REPRODUCTION'), 'B11_L25_PLANT_REPRODUCTION', 'Sinh sản ở thực vật', 'Reproduction in plants', 25,
       'lesson', 25, 159, 166,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH04_REPRODUCTION'), 'B11_L26_LAB_PLANT_PROPAGATION', 'Thực hành: Nhân giống vô tính và thụ phấn cho cây', 'Lab: Asexual propagation and pollination in plants', 26,
       'practice', 26, 167, 169,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH04_REPRODUCTION'), 'B11_L27_ANIMAL_REPRODUCTION', 'Sinh sản ở động vật', 'Reproduction in animals', 27,
       'lesson', 27, 170, 182,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH05_INTEGRATION_CAREERS'), 'B11_L28_PHYSIOLOGY_INTEGRATION', 'Mối quan hệ giữa các quá trình sinh lí trong cơ thể sinh vật', 'Relationships among physiological processes in organisms', 28,
       'lesson', 28, 183, 184,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B11_CH05_INTEGRATION_CAREERS'), 'B11_L29_ORGANISM_BIOLOGY_CAREERS', 'Một số ngành nghề liên quan đến sinh học cơ thể', 'Careers related to organismal biology', 29,
       'lesson', 29, 185, 186,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=11
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, NULL, 'B12_PART_GENETICS', 'Phần bốn. Di truyền học', 'Part Four. Genetics', 1,
       'part', NULL, 5, 96,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_PART_GENETICS'), 'B12_MOLECULAR_GENETICS', 'Chương I. Di truyền phân tử', 'Chapter I. Molecular Genetics', 1,
       'chapter', NULL, 5, 35,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_PART_GENETICS'), 'B12_CH02_CHROMOSOME_GENETICS', 'Chương II. Di truyền nhiễm sắc thể', 'Chapter II. Chromosome Genetics', 2,
       'chapter', NULL, 36, 77,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_PART_GENETICS'), 'B12_CH03_EXTENDED_CHROMOSOME_INHERITANCE', 'Chương III. Mở rộng học thuyết di truyền nhiễm sắc thể', 'Chapter III. Extensions of Chromosome Inheritance', 3,
       'chapter', NULL, 78, 90,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_PART_GENETICS'), 'B12_CH04_POPULATION_GENETICS', 'Chương IV. Di truyền quần thể', 'Chapter IV. Population Genetics', 4,
       'chapter', NULL, 91, 96,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, NULL, 'B12_PART_EVOLUTION', 'Phần năm. Tiến hoá', 'Part Five. Evolution', 2,
       'part', NULL, 97, 121,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_PART_EVOLUTION'), 'B12_CH05_EVOLUTION', 'Chương V. Bằng chứng và các học thuyết tiến hoá', 'Chapter V. Evidence and Theories of Evolution', 5,
       'chapter', NULL, 97, 121,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, NULL, 'B12_PART_ECOLOGY', 'Phần sáu. Sinh thái học và môi trường', 'Part Six. Ecology and Environment', 3,
       'part', NULL, 122, 193,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_PART_ECOLOGY'), 'B12_CH06_ENV_POPULATION', 'Chương VI. Môi trường và sinh thái học quần thể', 'Chapter VI. Environment and Population Ecology', 6,
       'chapter', NULL, 122, 140,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_PART_ECOLOGY'), 'B12_CH07_COMMUNITY_ECOSYSTEM', 'Chương VII. Sinh thái học quần xã', 'Chapter VII. Community Ecology', 7,
       'chapter', NULL, 141, 174,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_PART_ECOLOGY'), 'B12_CH08_RESTORATION_SUSTAINABILITY', 'Chương VIII. Sinh thái học phục hồi, bảo tồn và phát triển bền vững', 'Chapter VIII. Restoration Ecology, Conservation and Sustainable Development', 8,
       'chapter', NULL, 175, 193,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_MOLECULAR_GENETICS'), 'B12_DNA_REPLICATION', 'DNA và cơ chế tái bản DNA', 'DNA and DNA replication', 1,
       'lesson', 1, 5, 8,
       true, true, '{"primary_concept_code": "BIO.DNA.REPLICATION"}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_MOLECULAR_GENETICS'), 'B12_L02_GENE_EXPRESSION_GENOME', 'Gene, quá trình truyền đạt thông tin di truyền và hệ gene', 'Genes, genetic information flow and the genome', 2,
       'lesson', 2, 9, 17,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_MOLECULAR_GENETICS'), 'B12_L03_GENE_REGULATION', 'Điều hoà biểu hiện gene', 'Regulation of gene expression', 3,
       'lesson', 3, 18, 22,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_MOLECULAR_GENETICS'), 'B12_L04_GENE_MUTATION', 'Đột biến gene', 'Gene mutation', 4,
       'lesson', 4, 23, 26,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_MOLECULAR_GENETICS'), 'B12_L05_GENETIC_TECHNOLOGY', 'Công nghệ di truyền', 'Genetic technology', 5,
       'lesson', 5, 27, 33,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_MOLECULAR_GENETICS'), 'B12_L06_LAB_DNA_EXTRACTION', 'Thực hành: Tách chiết DNA', 'Lab: DNA extraction', 6,
       'practice', 6, 34, 35,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH02_CHROMOSOME_GENETICS'), 'B12_L07_CHROMOSOME_STRUCTURE', 'Cấu trúc và chức năng của nhiễm sắc thể', 'Chromosome structure and function', 7,
       'lesson', 7, 36, 39,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH02_CHROMOSOME_GENETICS'), 'B12_L08_MENDEL', 'Học thuyết di truyền của Mendel', 'Mendelian inheritance', 8,
       'lesson', 8, 40, 45,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH02_CHROMOSOME_GENETICS'), 'B12_L09_EXTENDED_MENDEL', 'Mở rộng học thuyết Mendel', 'Extensions of Mendelian inheritance', 9,
       'lesson', 9, 46, 49,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH02_CHROMOSOME_GENETICS'), 'B12_L10_SEX_LINKED_INHERITANCE', 'Di truyền giới tính và di truyền liên kết với giới tính', 'Sex determination and sex-linked inheritance', 10,
       'lesson', 10, 50, 53,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH02_CHROMOSOME_GENETICS'), 'B12_L11_LINKAGE_CROSSING_OVER', 'Liên kết gene và hoán vị gene', 'Gene linkage and crossing over', 11,
       'lesson', 11, 54, 59,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH02_CHROMOSOME_GENETICS'), 'B12_L12_CHROMOSOME_MUTATION', 'Đột biến nhiễm sắc thể', 'Chromosome mutation', 12,
       'lesson', 12, 60, 67,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH02_CHROMOSOME_GENETICS'), 'B12_L13_HUMAN_MEDICAL_GENETICS', 'Di truyền học người và di truyền y học', 'Human and medical genetics', 13,
       'lesson', 13, 68, 74,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH02_CHROMOSOME_GENETICS'), 'B12_L14_LAB_CHROMOSOME_MUTATION', 'Thực hành: Quan sát một số dạng đột biến nhiễm sắc thể', 'Lab: Observing chromosome mutations', 14,
       'practice', 14, 75, 77,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH03_EXTENDED_CHROMOSOME_INHERITANCE'), 'B12_L15_EXTRANUCLEAR_INHERITANCE', 'Di truyền gene ngoài nhân', 'Extranuclear inheritance', 15,
       'lesson', 15, 78, 82,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH03_EXTENDED_CHROMOSOME_INHERITANCE'), 'B12_L16_GENOTYPE_ENVIRONMENT_BREEDING', 'Tương tác giữa kiểu gene với môi trường và thành tựu chọn giống', 'Genotype–environment interaction and breeding achievements', 16,
       'lesson', 16, 83, 87,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH03_EXTENDED_CHROMOSOME_INHERITANCE'), 'B12_L17_LAB_VARIATION_PLANTS', 'Thực hành: Thí nghiệm về thường biến ở cây trồng', 'Lab: Environmental variation in crops', 17,
       'practice', 17, 88, 90,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH04_POPULATION_GENETICS'), 'B12_L18_POPULATION_GENETICS', 'Di truyền quần thể', 'Population genetics', 18,
       'lesson', 18, 91, 96,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH05_EVOLUTION'), 'B12_L19_EVOLUTION_EVIDENCE', 'Các bằng chứng tiến hoá', 'Evidence of evolution', 19,
       'lesson', 19, 97, 100,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH05_EVOLUTION'), 'B12_L20_DARWIN', 'Quan niệm của Darwin về chọn lọc tự nhiên và hình thành loài', 'Darwin’s view of natural selection and species formation', 20,
       'lesson', 20, 101, 105,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH05_EVOLUTION'), 'B12_L21_MODERN_SYNTHESIS', 'Học thuyết tiến hoá tổng hợp hiện đại', 'Modern evolutionary synthesis', 21,
       'lesson', 21, 106, 112,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH05_EVOLUTION'), 'B12_L22_MACROEVOLUTION_PHYLOGENY', 'Tiến hoá lớn và quá trình phát sinh chủng loại', 'Macroevolution and phylogeny', 22,
       'lesson', 22, 113, 121,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH06_ENV_POPULATION'), 'B12_L23_ENVIRONMENT_FACTORS', 'Môi trường và các nhân tố sinh thái', 'Environment and ecological factors', 23,
       'lesson', 23, 122, 127,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH06_ENV_POPULATION'), 'B12_L24_POPULATION_ECOLOGY', 'Sinh thái học quần thể', 'Population ecology', 24,
       'lesson', 24, 128, 137,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH06_ENV_POPULATION'), 'B12_L25_LAB_POPULATION', 'Thực hành: Xác định khu vực phân bố, kiểu phân bố cá thể và ước tính kích thước mật độ của quần thể thực vật hoặc động vật ít di chuyển', 'Lab: Population distribution and density estimation', 25,
       'practice', 25, 138, 140,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH07_COMMUNITY_ECOSYSTEM'), 'B12_L26_COMMUNITY', 'Quần xã sinh vật', 'Biological communities', 26,
       'lesson', 26, 141, 149,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH07_COMMUNITY_ECOSYSTEM'), 'B12_L27_LAB_COMMUNITY', 'Thực hành: Tìm hiểu một số đặc trưng cơ bản của quần xã trong tự nhiên', 'Lab: Investigating community characteristics', 27,
       'practice', 27, 150, 151,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH07_COMMUNITY_ECOSYSTEM'), 'B12_L28_ECOSYSTEM', 'Hệ sinh thái', 'Ecosystems', 28,
       'lesson', 28, 152, 154,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH07_COMMUNITY_ECOSYSTEM'), 'B12_L29_ECOSYSTEM_ENERGY', 'Trao đổi vật chất và chuyển hoá năng lượng trong hệ sinh thái', 'Matter cycling and energy transformation in ecosystems', 29,
       'lesson', 29, 155, 160,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH07_COMMUNITY_ECOSYSTEM'), 'B12_L30_SUCCESSION', 'Diễn thế', 'Ecological succession', 30,
       'lesson', 30, 161, 164,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH07_COMMUNITY_ECOSYSTEM'), 'B12_L31_BIOSPHERE_BIOMES_CYCLES', 'Sinh quyển, khu sinh học và chu trình sinh - địa - hoá', 'Biosphere, biomes and biogeochemical cycles', 31,
       'lesson', 31, 165, 171,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH07_COMMUNITY_ECOSYSTEM'), 'B12_L32_LAB_ARTIFICIAL_ECOSYSTEM', 'Thực hành: Thiết kế một hệ sinh thái nhân tạo', 'Lab: Designing an artificial ecosystem', 32,
       'practice', 32, 172, 174,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH08_RESTORATION_SUSTAINABILITY'), 'B12_L33_RESTORATION_CONSERVATION', 'Sinh thái học phục hồi và bảo tồn đa dạng sinh học', 'Restoration ecology and biodiversity conservation', 33,
       'lesson', 33, 175, 179,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH08_RESTORATION_SUSTAINABILITY'), 'B12_L34_SUSTAINABLE_DEVELOPMENT', 'Phát triển bền vững', 'Sustainable development', 34,
       'lesson', 34, 180, 187,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_units(subject_id, grade_id, parent_id, code, name_vi, name_en, sort_order,
                             unit_type, lesson_number, printed_page_start, printed_page_end,
                             is_power_ready, catalog_visible, metadata_json)
SELECT s.id, g.id, (SELECT id FROM curriculum_units WHERE code = 'B12_CH08_RESTORATION_SUSTAINABILITY'), 'B12_L35_PROJECT_LOCAL_CONSERVATION', 'Dự án: Tìm hiểu thực trạng bảo tồn sinh thái tại địa phương và đề xuất giải pháp bảo tồn', 'Project: Local ecological conservation and proposed solutions', 35,
       'project', 35, 188, 193,
       false, true, '{}'::jsonb
FROM subjects s JOIN grades g ON g.subject_id=s.id
WHERE s.code='BIOLOGY' AND g.level=12
ON CONFLICT (code) DO UPDATE SET
    parent_id=EXCLUDED.parent_id, name_vi=EXCLUDED.name_vi, name_en=EXCLUDED.name_en,
    sort_order=EXCLUDED.sort_order, unit_type=EXCLUDED.unit_type, lesson_number=EXCLUDED.lesson_number,
    printed_page_start=EXCLUDED.printed_page_start, printed_page_end=EXCLUDED.printed_page_end,
    is_power_ready=EXCLUDED.is_power_ready, catalog_visible=true, metadata_json=EXCLUDED.metadata_json;


INSERT INTO curriculum_unit_sources(curriculum_unit_id, source_id, source_role, printed_page_start, printed_page_end, metadata_json)
SELECT cu.id, s.id, 'primary', cu.printed_page_start, cu.printed_page_end,
       jsonb_build_object('mapping','toc_seed_v09')
FROM curriculum_units cu
JOIN grades g ON g.id=cu.grade_id
JOIN sources s ON s.code = CASE g.level WHEN 10 THEN 'BIO10_KNTT' WHEN 11 THEN 'BIO11_KNTT' WHEN 12 THEN 'BIO12_KNTT' END
WHERE cu.catalog_visible=true AND cu.unit_type IN ('lesson','practice','project')
ON CONFLICT (curriculum_unit_id, source_id, source_role) DO UPDATE
SET printed_page_start=EXCLUDED.printed_page_start,
    printed_page_end=EXCLUDED.printed_page_end,
    metadata_json=EXCLUDED.metadata_json;

-- Known PDF-page mapping for the v0.3/v0.9 DNA replication vertical slice.
UPDATE curriculum_unit_sources cus
SET pdf_page_start=7, pdf_page_end=10,
    metadata_json = cus.metadata_json || '{"pdf_mapping":"verified_vertical_slice"}'::jsonb
WHERE cus.curriculum_unit_id=(SELECT id FROM curriculum_units WHERE code='B12_DNA_REPLICATION')
  AND cus.source_id=(SELECT id FROM sources WHERE code='BIO12_KNTT');


INSERT INTO power_unit_blueprints(curriculum_unit_id, version, prepare_json, work_json, policy_json, updated_at)
SELECT id, 1, '{"title_vi": "DNA và cơ chế tái bản DNA", "title_en": "DNA and DNA replication", "outcomes_vi": ["Nêu được nguyên tắc và ý nghĩa của quá trình tái bản DNA.", "Giải thích được vì sao xuất hiện mạch dẫn đầu, mạch chậm và các đoạn Okazaki.", "Phân biệt được vai trò cơ bản của DNA polymerase và DNA ligase trong tái bản DNA."], "outcomes_en": ["State the principles and significance of DNA replication.", "Explain why leading and lagging strands, including Okazaki fragments, arise.", "Distinguish the basic roles of DNA polymerase and DNA ligase in DNA replication."], "keywords": ["dna", "tái bản", "replication", "polymerase", "mạch", "strand", "okazaki", "ligase"], "diagnostic_items": [{"code": "PREP_DNA_01", "concept_code": "BIO.DNA.STRUCTURE", "question_type": "true_false", "prompt_vi": "Hai mạch polynucleotide của DNA chạy ngược chiều nhau.", "prompt_en": "The two polynucleotide strands of DNA run antiparallel to each other.", "options": [], "expected": true}, {"code": "PREP_DNA_02", "concept_code": "BIO.DNA.STRUCTURE", "question_type": "mcq", "prompt_vi": "Trong DNA, adenine (A) bắt cặp bổ sung với base nào?", "prompt_en": "In DNA, which base pairs complementarily with adenine (A)?", "options": [{"key": "A", "text_vi": "Thymine (T)", "text_en": "Thymine (T)"}, {"key": "B", "text_vi": "Guanine (G)", "text_en": "Guanine (G)"}, {"key": "C", "text_vi": "Cytosine (C)", "text_en": "Cytosine (C)"}, {"key": "D", "text_vi": "Uracil (U)", "text_en": "Uracil (U)"}], "expected": "A"}, {"code": "PREP_DNA_03", "concept_code": "BIO.DNA.STRUCTURE", "question_type": "mcq", "prompt_vi": "Một nucleotide DNA gồm ba thành phần nào?", "prompt_en": "Which three components make up a DNA nucleotide?", "options": [{"key": "A", "text_vi": "Đường ribose, phosphate và base nitrogen", "text_en": "Ribose, phosphate and a nitrogenous base"}, {"key": "B", "text_vi": "Đường deoxyribose, phosphate và base nitrogen", "text_en": "Deoxyribose, phosphate and a nitrogenous base"}, {"key": "C", "text_vi": "Glucose, phosphate và amino acid", "text_en": "Glucose, phosphate and an amino acid"}, {"key": "D", "text_vi": "Deoxyribose, lipid và base nitrogen", "text_en": "Deoxyribose, lipid and a nitrogenous base"}], "expected": "B"}]}'::jsonb, '{"vi": {"title": "Làm việc sâu với cơ chế tái bản DNA", "intro": "Work là pha bạn tự xử lý kiến thức. Hãy dùng sơ đồ ở Organize, SGK và POWER Tutor để giải thích bằng lời của chính bạn; Tutor chỉ gợi ý và phản hồi, không làm thay nhiệm vụ.", "tasks": [{"code": "W1_DIRECTION", "title": "Nhiệm vụ 1 · Chiều tổng hợp DNA", "prompt": "Giải thích vì sao việc DNA polymerase chỉ tổng hợp mạch mới theo chiều 5′→3′ lại dẫn đến hai kiểu tổng hợp khác nhau tại chạc tái bản.", "concept_codes": ["BIO.DNA.REPLICATION"], "minimum_chars": 90, "scaffold": ["Hai mạch khuôn DNA có chiều tương đối như thế nào?", "DNA polymerase chỉ kéo dài đầu nào của mạch mới?", "Điều đó ảnh hưởng ra sao đến hai mạch mới tại chạc tái bản?"]}, {"code": "W2_COMPARE", "title": "Nhiệm vụ 2 · So sánh hai mạch mới", "prompt": "So sánh mạch dẫn đầu và mạch chậm theo ít nhất ba tiêu chí: tính liên tục, hướng di chuyển tương đối của chạc tái bản và sự xuất hiện của đoạn Okazaki.", "concept_codes": ["BIO.DNA.REPLICATION"], "minimum_chars": 100, "scaffold": ["Không chỉ liệt kê; hãy nêu nguyên nhân của điểm khác nhau.", "Cả hai mạch mới vẫn được tổng hợp theo cùng chiều hóa học 5′→3′."]}, {"code": "W3_CAUSAL", "title": "Nhiệm vụ 3 · Chuỗi nguyên nhân – kết quả", "prompt": "Tạo một lời giải thích ngắn theo chuỗi nguyên nhân – kết quả từ cấu trúc hai mạch DNA đến việc hình thành và nối các đoạn Okazaki.", "concept_codes": ["BIO.DNA.REPLICATION"], "minimum_chars": 120, "scaffold": ["Bắt đầu từ hai mạch DNA ngược chiều.", "Nối tiếp bằng giới hạn chiều tổng hợp của DNA polymerase.", "Kết thúc bằng tổng hợp gián đoạn và vai trò nối các đoạn mới tạo thành."]}], "self_check_prompt": "Sau khi hoàn thành, bạn tự tin đến mức nào rằng mình có thể tự giải thích cơ chế này mà không nhìn đáp án?"}, "en": {"title": "Work deeply with DNA replication", "intro": "Work is where you process the biology yourself. Use your Organize map, the textbook, and POWER Tutor to explain in your own words; the Tutor should scaffold and give feedback, not complete the task for you.", "tasks": [{"code": "W1_DIRECTION", "title": "Task 1 · Direction of DNA synthesis", "prompt": "Explain why DNA polymerase synthesizing new DNA only 5′→3′ produces two different synthesis patterns at a replication fork.", "concept_codes": ["BIO.DNA.REPLICATION"], "minimum_chars": 90, "scaffold": ["How are the two DNA templates oriented relative to each other?", "Which end of the new strand can DNA polymerase extend?", "How does that constraint affect the two new strands at the fork?"]}, {"code": "W2_COMPARE", "title": "Task 2 · Compare the two new strands", "prompt": "Compare the leading and lagging strands using at least three criteria: continuity, movement relative to the replication fork, and the presence of Okazaki fragments.", "concept_codes": ["BIO.DNA.REPLICATION"], "minimum_chars": 100, "scaffold": ["Do not only list differences; explain what causes them.", "Both new strands are still synthesized chemically in the 5′→3′ direction."]}, {"code": "W3_CAUSAL", "title": "Task 3 · Cause-and-effect chain", "prompt": "Write a short cause-and-effect explanation from the antiparallel DNA structure to the formation and joining of Okazaki fragments.", "concept_codes": ["BIO.DNA.REPLICATION"], "minimum_chars": 120, "scaffold": ["Start with the antiparallel DNA strands.", "Then use the directional constraint of DNA polymerase.", "End with discontinuous synthesis and joining the newly formed fragments."]}], "self_check_prompt": "After completing the tasks, how confident are you that you could explain the mechanism without looking at an answer?"}}'::jsonb, '{"primary_concept_code": "BIO.DNA.REPLICATION", "minimum_anchor_concepts": 3, "minimum_links": 3}'::jsonb, now()
FROM curriculum_units WHERE code='B12_DNA_REPLICATION'
ON CONFLICT (curriculum_unit_id) DO UPDATE
SET version=EXCLUDED.version, prepare_json=EXCLUDED.prepare_json, work_json=EXCLUDED.work_json,
    policy_json=EXCLUDED.policy_json, updated_at=now();

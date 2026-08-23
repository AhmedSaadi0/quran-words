-- ============================================
-- أمثلة على الاستعلامات لقاعدة بيانات القرآن الكريم
-- Quran Words Database Query Examples
-- ============================================

-- 1. البحث عن كلمة محددة
-- Search for a specific word

-- البحث عن كلمة "الله"
SELECT w.text, w.translation, a.surah, a.ayah
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN ayat a ON wa.ayah_id = a.id
WHERE w.text_clean LIKE '%ٱلله%'
ORDER BY a.surah, a.ayah
LIMIT 20;

-- 2. عرض سورة معينة مع التحليل الصرفي
-- Display a surah with morphological analysis

-- عرض سورة الفاتحة: الكلمة + النوع + الجذر + الصيغة + الإعراب
SELECT a.ayah, wa.position, w.text, w.translation,
       wm.pos, r.root, wm.form, wm.aspect, wm.voice,
       wm.gender, wm.number, wm.grammatical_case
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN ayat a ON wa.ayah_id = a.id
LEFT JOIN word_morphology wm ON wm.word_ayah_id = wa.id
LEFT JOIN roots r ON r.id = wm.root_id
WHERE a.surah = 1
ORDER BY a.ayah, wa.position;

-- 3. البحث بالجذر
-- Search by root

-- كل الكلمات التي جذرها "كتب" مع مواقعها
SELECT DISTINCT w.text, w.translation, r.root
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN word_morphology wm ON wm.word_ayah_id = wa.id
JOIN roots r ON r.id = wm.root_id
WHERE r.root = 'كتب';

-- 4. المعنى العربي للجذر
-- Arabic meaning of a root from classical lexicons

SELECT r.root, rm.book_name, substr(rm.definition, 1, 120) as meaning
FROM roots r
JOIN root_meanings rm ON rm.root_id = r.id
WHERE r.root = 'رحم'
LIMIT 10;

-- 5. إحصائيات عامة
-- General statistics

SELECT 
    (SELECT COUNT(*) FROM surahs) as surah_count,
    (SELECT COUNT(*) FROM ayat) as ayah_count,
    (SELECT COUNT(*) FROM words) as word_count,
    (SELECT COUNT(*) FROM roots) as root_count,
    (SELECT COUNT(*) FROM word_morphology) as morphology_count;

-- 6. أكثر الكلمات تكراراً
-- Most frequent words

SELECT w.text, w.translation, COUNT(*) as frequency
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
GROUP BY w.text
ORDER BY frequency DESC
LIMIT 20;

-- 7. البحث الصرفي: أفعال ماضية مجهولة (مبني للمجهول)
-- Morphological search: passive perfect verbs

SELECT DISTINCT w.text, w.translation, r.root, wm.form
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN word_morphology wm ON wm.word_ayah_id = wa.id
JOIN roots r ON r.id = wm.root_id
WHERE wm.aspect = 'PERF' AND wm.voice = 'PASS'
LIMIT 30;

-- 8. البحث الصرفي: صيغ المبالغة وأسماء الفاعلين
-- Active participles (اسم فاعل)

SELECT w.text, w.translation, r.root
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN word_morphology wm ON wm.word_ayah_id = wa.id
JOIN roots r ON r.id = wm.root_id
WHERE wm.derivation = 'PCPL' AND wm.pos = 'N'
LIMIT 30;

-- 9. كلمات مكية ومدنية
-- Meccan and Medinan words

SELECT w.text, w.translation
FROM words w
WHERE w.id IN (
    SELECT DISTINCT wa.word_id
    FROM word_ayah wa
    JOIN ayat a ON wa.ayah_id = a.id
    JOIN surahs s ON a.surah = s.id
    WHERE s.revelation_type = 'مكية'
)
AND w.id NOT IN (
    SELECT DISTINCT wa.word_id
    FROM word_ayah wa
    JOIN ayat a ON wa.ayah_id = a.id
    JOIN surahs s ON a.surah = s.id
    WHERE s.revelation_type = 'مدنية'
)
LIMIT 20;

-- 10. أكثر الجذور وروداً
-- Most frequent roots

SELECT r.root, COUNT(*) as frequency
FROM word_ayah wa
JOIN word_morphology wm ON wm.word_ayah_id = wa.id
JOIN roots r ON r.id = wm.root_id
GROUP BY r.root
ORDER BY frequency DESC
LIMIT 20;

-- 11. توزيع أنواع الكلمات (أجزاء الكلام)
-- Part-of-speech distribution

SELECT pos, COUNT(*) as count
FROM word_morphology
GROUP BY pos
ORDER BY count DESC;

-- 12. أفعال بوزن (فاعَل) من الجذر "عمل"
-- Verbs of form III from root "عمل"

SELECT DISTINCT w.text, w.translation, wm.form, wm.aspect
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN word_morphology wm ON wm.word_ayah_id = wa.id
JOIN roots r ON r.id = wm.root_id
WHERE r.root = 'عمل'
ORDER BY wm.form;
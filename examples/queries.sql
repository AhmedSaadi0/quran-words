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

-- 2. عرض سورة معينة
-- Display a specific surah

-- عرض سورة الفاتحة كاملة
SELECT a.ayah, wa.position, w.text, w.translation
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN ayat a ON wa.ayah_id = a.id
WHERE a.surah = 1
ORDER BY a.ayah, wa.position;

-- 3. البحث بالجذر
-- Search by root

-- البحث عن كلمات بجذر "ك ت ب" (كتابة)
SELECT w.text, w.translation
FROM words w
JOIN roots r ON w.root_id = r.id
WHERE r.root = 'كتب';

-- 4. إحصائيات عامة
-- General statistics

-- عدد السور والآيات والكلمات
SELECT 
    (SELECT COUNT(*) FROM surahs) as surah_count,
    (SELECT COUNT(*) FROM ayat) as ayah_count,
    (SELECT COUNT(*) FROM words) as word_count;

-- 5. أكثر الكلمات تكراراً
-- Most frequent words

SELECT w.text, w.translation, COUNT(*) as frequency
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
GROUP BY w.text
ORDER BY frequency DESC
LIMIT 20;

-- 6. كلمات في سورة محددة
-- Words in a specific surah

-- كلمات سورة الرحمن
SELECT DISTINCT w.text, w.translation
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN ayat a ON wa.ayah_id = a.id
WHERE a.surah = 55;

-- 7. البحث عن آية بالنص
-- Search for a verse by text

-- البحث عن آية تحتوي على "بسم الله"
SELECT a.surah, a.ayah, a.text_uthmani
FROM ayat a
WHERE a.text_uthmani LIKE '%بِسْمِ%ٱللَّهِ%';

-- 8. إحصائيات السور
-- Surah statistics

SELECT s.id, s.name_ar, s.name_en, s.ayah_count,
       COUNT(DISTINCT w.id) as unique_words
FROM surahs s
JOIN ayat a ON s.id = a.surah
JOIN word_ayah wa ON a.id = wa.ayah_id
JOIN words w ON wa.word_id = w.id
GROUP BY s.id
ORDER BY s.id;

-- 9. كلمات مكية ومدنية
-- Meccan and Medinan words

-- كلمات تظهر في سور مكية فقط
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

-- 10. تحليل طول الكلمات
-- Word length analysis

SELECT 
    LENGTH(w.text_clean) as word_length,
    COUNT(*) as frequency
FROM words w
GROUP BY word_length
ORDER BY word_length;

-- 11. كلمات تحتوي على حرف معين
-- Words containing a specific letter

-- كلمات تحتوي على حرف "ق"
SELECT DISTINCT w.text, w.translation
FROM words w
WHERE w.text LIKE '%ق%'
LIMIT 20;

-- 12. آيات طويلة وقصيرة
-- Long and short verses

-- أطول 10 آيات
SELECT a.surah, a.ayah, a.text_uthmani, a.word_count
FROM ayat a
ORDER BY a.word_count DESC
LIMIT 10;

-- أقصر 10 آيات
SELECT a.surah, a.ayah, a.text_uthmani, a.word_count
FROM ayat a
ORDER BY a.word_count ASC
LIMIT 10;

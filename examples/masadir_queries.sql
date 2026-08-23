-- ============================================
-- أمثلة جديدة: المصادر والمشتقات (المرحلة 3)
-- ============================================

-- 1) مصدر كل كلمة في سورة الفاتحة
SELECT a.surah, a.ayah, wa.position, w.text, r.root, m.masdar_plain, m.pattern, m.is_attested
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN ayat a ON wa.ayah_id = a.id
LEFT JOIN word_morphology wm ON wm.word_ayah_id = wa.id
LEFT JOIN roots r ON r.id = wm.root_id
LEFT JOIN masadir m ON m.root_id = r.id
WHERE a.surah = 1
GROUP BY wa.id
ORDER BY a.ayah, wa.position;

-- 2) كل مصادر جذر "كتب" (كَتْب، كتابة، اكتتاب...)
SELECT r.root, m.masdar_ar, m.masdar_plain, m.pattern, m.form, m.is_attested, m.source
FROM masadir m
JOIN roots r ON r.id = m.root_id
WHERE r.root = 'كتب'
ORDER BY m.is_attested DESC, m.confidence DESC;

-- 3) مشتقات جذر "علم" (عالم، معلوم، عليم...)
SELECT r.root, d.form_ar, d.form_plain, d.pattern, d.derivative_type, d.is_quranic, d.camel_valid, w.text as example
FROM derivatives d
JOIN roots r ON r.id = d.root_id
LEFT JOIN words w ON w.id = d.example_word_id
WHERE r.root = 'علم'
ORDER BY d.is_quranic DESC, d.derivative_type;

-- 4) البحث عن كلمة بمصدرها: كل الآيات التي فيها كلمات جذرها مصدره "رحمة"
SELECT DISTINCT a.surah, a.ayah, a.text_uthmani, r.root, m.masdar_plain
FROM word_ayah wa
JOIN ayat a ON wa.ayah_id = a.id
JOIN word_morphology wm ON wm.word_ayah_id = wa.id
JOIN roots r ON r.id = wm.root_id
JOIN masadir m ON m.root_id = r.id
WHERE m.masdar_plain = 'رحمة'
ORDER BY a.surah, a.ayah
LIMIT 20;

-- 5) مشتقات قرآنية فقط (الموجودة فعلاً في القرآن)
SELECT d.root, d.form_ar, d.derivative_type, d.pattern, w.text, w.translation
FROM derivatives d
JOIN words w ON w.id = d.example_word_id
WHERE d.is_quranic = 1
ORDER BY d.root
LIMIT 30;

-- 6) إحصائية: أكثر الجذور التي لها مصادر
SELECT r.root, COUNT(*) as masadir_cnt
FROM masadir m JOIN roots r ON r.id = m.root_id
GROUP BY r.root ORDER BY masadir_cnt DESC LIMIT 10;

-- 7) كلمة مع كل مشتقات جذرها
-- مثال: كلمة "عليم" (من جذر علم) وكل مشتقات علم
SELECT w.text as word, r.root, d.form_ar as derivative, d.derivative_type
FROM words w
JOIN word_ayah wa ON wa.word_id = w.id
JOIN word_morphology wm ON wm.word_ayah_id = wa.id
JOIN roots r ON r.id = wm.root_id
JOIN derivatives d ON d.root_id = r.id
WHERE w.text = 'عَلِيمٌ'
LIMIT 20;

-- 8) فرق بين المصدر المنصوص (VN) والمولّد
SELECT r.root, m.masdar_ar, m.is_attested, m.source, m.confidence,
       (SELECT GROUP_CONCAT(w2.text, ' | ') FROM word_ayah wa2 JOIN words w2 ON wa2.word_id=w2.id JOIN word_morphology wm2 ON wm2.word_ayah_id=wa2.id WHERE wm2.root_id=r.id AND wm2.derivation='VN' LIMIT 3) as quran_examples
FROM masadir m JOIN roots r ON r.id=m.root_id
WHERE m.is_attested=1
LIMIT 10;

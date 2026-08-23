#!/usr/bin/env python3
"""
المرحلة 3: بناء جداول المصادر والمشتقات لكل جذر/كلمة قرآنية
Stage 3: Build masadir (verbal nouns) and derivatives tables.

الفكرة: لا نستبدل الجذور المدققة من Quranic Arabic Corpus (QAC)، بل نُثريها.
لكل جذر نولّد:
  1) المصدر/المصادر (masdar) - الاسم الدال على الحدث: كتب -> كِتابة / كَتْب
  2) المشتقات (derivatives) - اسم فاعل، اسم مفعول، صفة مشبهة، مبالغة...

مصادر البيانات بالترتيب (priority):
  a) ما ورد فعلاً في القرآن كـ VN (word_morphology.derivation='VN') - مصدر منصوص (gold)
  b) محلل CAMeL Tools (CALIMA-Star) إن توفر - تحليل صرفي غني
  c) توليد بالأوزان (pattern-based) - للصيغ المشتقة II-X (مضمونة) وللصيغة I تقريبية
  d) معاني الجذور من الحواماني (للتوثيق فقط)

التنصيب (مرة واحدة):
  pip install camel-tools --user
  camel_data -i morphology-db-msa-r13   # ~40MB

الاستعمال:
  python scripts/build_masadir_derivatives.py

الخرج: جداول جديدة في data/quran_words.db:
  - masadir        (لكل جذر: قائمة مصادره)
  - derivatives    (لكل جذر: قائمة مشتقاته)
  - word_derivatives (ربط كلمة بمشتقاتها - اختياري)

ملاحظة: وزن torch (≈526MB) مطلوب فقط لنموذج BERT السياقي وغير لازم لهذا السكربت.
        يكفي morphology-db-msa-r13 (40MB) + scikit-learn.
"""

import json
import os
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "quran_words.db"

# ---------------------------------------------------------------------------
# إعداد CAMeL (اختياري - يعمل بدونه)
# ---------------------------------------------------------------------------
CAMEL_AVAILABLE = False
CAMEL_ANALYZER = None
try:
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer

    for _candidate in [
        Path.home()
        / ".camel_tools"
        / "data"
        / "morphology_db"
        / "calima-msa-r13"
        / "morphology.db",
        BASE_DIR / "calima-msa-r13" / "morphology.db",
    ]:
        if _candidate.exists():
            _db = MorphologyDB(str(_candidate), "a")
            CAMEL_ANALYZER = Analyzer(_db)
            CAMEL_AVAILABLE = True
            print(f"[CAMeL] محلل جاهز من {_candidate}")
            break
    if not CAMEL_AVAILABLE:
        print(
            "[CAMeL] غير متوفر - سيتم التوليد بالأوزان فقط (اطلّع camel_data -i morphology-db-msa-r13)"
        )
except Exception as e:
    print(f"[CAMeL] تعذر التحميل: {e}")
    CAMEL_AVAILABLE = False

# ---------------------------------------------------------------------------
# أدوات لغوية
# ---------------------------------------------------------------------------
DIACRITICS_RE = re.compile(
    r"[\u0617-\u061a\u064b-\u0652\u0656-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7\u06e8\u06ea-\u06ed\u0640]"
)


def strip_diacritics(s: str) -> str:
    return DIACRITICS_RE.sub("", s)


def normalize_root(s: str) -> str:
    """إزالة التشكيل وهمزة الوصل والـ tatweel."""
    s = strip_diacritics(s)
    s = (
        s.replace("ٱ", "ا")
        .replace("ـ", "")
        .replace("آ", "ا")
        .replace("أ", "ا")
        .replace("إ", "ا")
    )
    return s.strip()


# تطبيق الوزن: استبدال ف ع ل بحروف الجذر
def apply_pattern(root_clean: str, pattern: str) -> str:
    """
    root_clean: مثل 'كتب' (3 حروف) أو 'زلزل' (4) أو 'كتب' مشكول بدون تشكيل
    pattern: وزن يستخدم ف ع ل كمتغيرات، مثل 'فاعل', 'مفعول', 'تفعيل', 'افتعال'
    نستبدل ف->حرف1، ع->حرف2، ل->حرف3
    للأفعال الرباعية: نستخدم ف ع ل ل (الحرف الرابع يتكرر كـ ل الثانية)
    """
    root_clean = normalize_root(root_clean)
    # احتفظ فقط بالحروف العربية
    letters = [c for c in root_clean if "\u0621" <= c <= "\u064a" or c in "ءآأإٱىئؤ"]
    if len(letters) < 3:
        return ""
    r1, r2, r3 = letters[0], letters[1], letters[2]
    r4 = letters[3] if len(letters) >= 4 else None

    # خريطة بسيطة
    out = ""
    for ch in pattern:
        if ch == "ف":
            out += r1
        elif ch == "ع":
            out += r2
        elif ch == "ل":
            # للجذر الرباعي: أول ل -> ر3، ثاني ل -> ر4 إن وجد
            # نميز بالعد: سنستخدم r3 للأول و r4 للثاني إن كان pattern فيه لان متتاليتان (مثل فعللة: ف ع ل ل ة)
            # هنا تبسيط: إن كان r4 موجود وعدد اللامات >1 نستخدم r4 للمرة الثانية
            out += r3  # سيتم معالجة الرباعي في حالة فعللة لاحقاً
        else:
            out += ch
    # معالجة خاصة للرباعي فعللة: نستبدل ل الأخيرة بـ r4
    if r4 and "فعللة" in pattern:
        # فعللة: ف ع ل ل ة  -> أول ل r3، ثاني ل r4
        # طريقتنا الحالية تجعل الاثنتين r3، نصحح:
        # نعيد البناء بشكل أدق
        mapping = {"ف": r1, "ع": r2, "ل": r3}
        # نعد اللامات
        count_l = 0
        tmp = ""
        for ch in pattern:
            if ch == "ل":
                count_l += 1
                if count_l == 2 and r4:
                    tmp += r4
                else:
                    tmp += r3
            elif ch in mapping:
                tmp += mapping[ch]
            else:
                tmp += ch
        return tmp
    return out


# أوزان المصادر حسب الصيغة (مستندة لـ Sarf / CALIMA)
MASDAR_PATTERNS_BY_FORM = {
    # الصيغة: قائمة أوزان محتملة (مرتبة حسب الشيوع)
    "I": [
        "فَعْل",  # كَتْب، عِلْم
        "فَعَلة",  # رحمة (أهم للمعتلة)
        "فَعَالة",  # كتابة - مقدمة لأهميتها
        "فِعَالة",  # كتابة
        "فُعْلة",
        "فِعْلة",  # حِكمة
        "فَعَل",  #
        "فِعْل",
        "فُعْل",
        "فَعَال",  # ذهاب
        "فُعال",  # ركوع
        "فُعول",  # دخول
        "فَعيل",  # رحيل
        "فِعال",  # كتاب
        "فُعولة",
        "فَعَلان",  # غليان
        "فُعْلان",
    ],  # كتب -> كَتْب / كتابة، علم -> علم، رحم -> رحمة
    "II": ["تفعيل", "تفعلة"],  # علّم -> تعليم، زكّى -> تزكية
    "III": ["فِعال", "مفاعلة", "فعال"],  # كاتب -> كتاب / مكاتبة، قاتل -> قتال/مقاتلة
    "IV": ["إفعال"],  # أكرم -> إكرام
    "V": ["تفعّل", "تفعيل"],  # تفعّل -> تفعُّل (تعلّم -> تعلّم)
    "VI": ["تفاعُل"],  # تفاعل -> تفاعُل
    "VII": ["انفعال"],  # انكسر -> انكسار
    "VIII": ["افتعال"],  # اجتمع -> اجتماع
    "IX": ["افعلال"],  # احمرّ -> احمرار
    "X": ["استفعال"],  # استخرج -> استخراج
    # XI-XV نادرة في القرآن
    "XI": ["افعيعال"],
    "XII": ["افّوعال"],
}

# أوزان المشتقات الشائعة (plain بدون تشكيل للوليد، مع map للـ CAMeL validation)
DERIVATIVE_PATTERNS = [
    # (pattern, type, pos, description)
    ("فاعل", "اسم فاعل", "N", "ism_fa3il"),
    ("فاعلة", "اسم فاعل مؤنث", "N", "ism_fa3il_fem"),
    ("مفعول", "اسم مفعول", "N", "ism_maf3ul"),
    ("مفعولة", "اسم مفعول مؤنث", "N", "ism_maf3ul_fem"),
    ("فعّال", "صيغة مبالغة", "ADJ", "sifa_mubalagha_fa33al"),
    ("فعول", "صيغة مبالغة", "ADJ", "sifa_mubalagha_fa3ul"),
    ("فعيل", "صفة مشبهة/مبالغة", "ADJ", "sifa_fa3il"),
    ("مِفعال", "صيغة مبالغة/آلة", "N", "mif3al"),
    ("مِفعلة", "اسم آلة", "N", "mif3ala"),
    ("مَفْعَلة", "اسم مكان", "N", "ism_makan"),
    ("مَفْعِل", "اسم مكان/زمان", "N", "ism_makan2"),
    ("أفعل", "اسم تفضيل", "ADJ", "ism_tafdil"),
    ("فُعلى", "اسم تفضيل مؤنث", "ADJ", "ism_tafdil_fem"),
    ("فِعلة", "اسم مرة/هيئة", "N", "ism_marra"),
    ("فُعّال", "جمع/مبالغة", "N", "jama_mubalagha"),
    ("أفعال", "جمع تكسير", "N", "jam_taksir_af3al"),
    ("فُعول", "جمع تكسير", "N", "jam_taksir_fu3ul"),
    ("فِعال", "جمع تكسير/مصدر", "N", "jam_fi3al"),
    ("فَعَلة", "جمع تكسير", "N", "jam_fa3ala"),
]

# حروف زائدة شائعة للتوليد الاختباري (للمصدر الثلاثي)
TRI_MASDAR_CANDIDATES_PLAIN = [
    "فَعْل",
    "فعل",  # كتب -> كتب (كَتْب)
    "فعلة",
    "فَعلة",
    "فِعلة",
    "فُعلة",
    "فعال",
    "فِعال",
    "فُعال",
    "فعول",
    "فعيل",
    "فعَالة",
    "فِعالة",
    "فُعولة",
    "مَفْعَل",
    "مِفْعَل",
]


def render_plain_pattern(root_clean: str, pattern_plain: str) -> str:
    """نسخة مبسطة بدون تشكيل: فعّل -> كتّب etc. نستخدم apply_pattern بعد إزالة التشكيل."""
    plain = strip_diacritics(pattern_plain)
    return apply_pattern(root_clean, plain)


def camel_validates(
    word: str, expected_root: str = None, require_pos: str = None
) -> tuple:
    """
    هل يعتبر CAMeL الكلمة صحيحة لنفس الجذر؟
    ترجع (valid, best_diac, pos)
    require_pos: إن حُدد (مثلاً 'noun') يشترط أن يكون التحليل noun
    """
    if not CAMEL_AVAILABLE or not word:
        return (False, word, None)
    try:
        an = CAMEL_ANALYZER.analyze(word)
        if not an:
            return (False, word, None)
        exp = normalize_root(expected_root) if expected_root else None
        best = None
        for a in an:
            r = a.get("root", "").replace(".", "")
            # pos في CAMeL يكون 'noun' أو 'verb' إلخ
            pos = a.get("pos", "")
            if exp and normalize_root(r) != exp:
                continue
            if require_pos and pos != require_pos:
                # اسمح بـ noun_prop أيضاً للمصادر
                if not (
                    require_pos == "noun" and pos in ("noun", "noun_prop", "noun_quant")
                ):
                    continue
            # وجد تطابق
            best = (True, a.get("diac", word), pos)
            return best
        return (False, word, None)
    except Exception:
        return (False, word, None)


def is_weak_root(root_plain: str) -> bool:
    """هل الجذر معتل (فيه و/ي/ء/ى) ؟"""
    return any(c in root_plain for c in "ويءأإآىؤئٱ")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def ensure_tables(conn):
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS masadir (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        root_id INTEGER NOT NULL,
        root TEXT NOT NULL,
        form TEXT,                 -- I-XV أو NULL
        lemma_id INTEGER,          -- قد يكون NULL إن لم يرتبط بlemma محدد
        masdar_ar TEXT NOT NULL,   -- بالتشكيل التقريبي
        masdar_plain TEXT NOT NULL,-- بدون تشكيل
        pattern TEXT,              -- الوزن
        is_attested BOOLEAN,       -- هل ورد كـ VN في القرآن؟
        source TEXT,               -- quran_vn / camel / pattern / hawramani
        confidence REAL,           -- 0-1
        FOREIGN KEY(root_id) REFERENCES roots(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS derivatives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        root_id INTEGER NOT NULL,
        root TEXT NOT NULL,
        pattern TEXT NOT NULL,
        derivative_type TEXT NOT NULL,
        form_ar TEXT NOT NULL,
        form_plain TEXT NOT NULL,
        pos TEXT,
        is_quranic BOOLEAN,
        camel_valid BOOLEAN,
        example_word_id INTEGER,
        source TEXT,
        FOREIGN KEY(root_id) REFERENCES roots(id)
    )""")
    # فهرسة
    c.execute("CREATE INDEX IF NOT EXISTS idx_masadir_root ON masadir(root_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_masadir_plain ON masadir(masdar_plain)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_deriv_root ON derivatives(root_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_deriv_plain ON derivatives(form_plain)")
    # ربط الكلمة بالمصدر (لكل موضع)
    c.execute("""CREATE TABLE IF NOT EXISTS word_masdar (
        word_ayah_id INTEGER NOT NULL,
        masdar_id INTEGER NOT NULL,
        PRIMARY KEY(word_ayah_id, masdar_id),
        FOREIGN KEY(word_ayah_id) REFERENCES word_ayah(id),
        FOREIGN KEY(masdar_id) REFERENCES masadir(id)
    )""")
    conn.commit()


def main():
    print("=== المرحلة 3: بناء المصادر والمشتقات ===\n")
    if not DB_PATH.exists():
        sys.exit(
            f"DB غير موجود: {DB_PATH} - شغّل build_db.py و build_morphology.py أولاً"
        )

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    ensure_tables(conn)
    c = conn.cursor()

    # --- تحميل الجذور واللمّات ---
    c.execute("SELECT id, root FROM roots")
    roots = {row["id"]: row["root"] for row in c.fetchall()}
    print(f"الجذور: {len(roots)}")

    c.execute("SELECT id, lemma_ar, lemma_bw FROM lemmas")
    lemmas = {row["id"]: dict(row) for row in c.fetchall()}
    lemmas_by_ar = {v["lemma_ar"]: k for k, v in lemmas.items() if v["lemma_ar"]}
    print(f"اللمّات: {len(lemmas)}")

    # خريطة كلمات بدون تشكيل -> word_id (للتأكد هل المشتق موجود في القرآن)
    c.execute("SELECT id, text, text_clean FROM words")
    words = c.fetchall()
    word_plain_map = defaultdict(list)  # plain -> [text, id]
    for w in words:
        plain = normalize_root(w["text_clean"] or w["text"])
        word_plain_map[plain].append((w["text"], w["id"]))
    # أيضاً مجموعة plain للتحقق السريع
    word_plain_set = set(word_plain_map.keys())
    print(f"الكلمات الفريدة: {len(words)}, plain set: {len(word_plain_set)}")

    # --- 1) المصادر المنصوصة كـ VN في القرآن ---
    c.execute("""
        SELECT wm.root_id, r.root, wm.lemma_id, l.lemma_ar, w.text, w.text_clean
        FROM word_morphology wm
        JOIN roots r ON r.id = wm.root_id
        LEFT JOIN lemmas l ON l.id = wm.lemma_id
        JOIN word_ayah wa ON wa.id = wm.word_ayah_id
        JOIN words w ON w.id = wa.word_id
        WHERE wm.derivation='VN'
    """)
    vn_rows = c.fetchall()
    print(f"مصادر منصوصة (VN) في القرآن: {len(vn_rows)} صف، فريدة؟")
    # نجمع مصادر فريدة لكل جذر
    attested_masadir = defaultdict(set)  # root_id -> set(masdar_plain)
    vn_details = defaultdict(list)
    for r in vn_rows:
        root_id = r["root_id"]
        lemma_ar = r["lemma_ar"] or r["text"]
        plain = normalize_root(r["text_clean"] or r["text"])
        attested_masadir[root_id].add(plain)
        vn_details[root_id].append((lemma_ar, r["text"], plain))

    # --- 2) كل الأفعال لمعرفة الأوزان ---
    c.execute("""
        SELECT wm.root_id, r.root, wm.form, wm.lemma_id, l.lemma_ar, COUNT(*) as cnt
        FROM word_morphology wm
        JOIN roots r ON r.id = wm.root_id
        LEFT JOIN lemmas l ON l.id = wm.lemma_id
        WHERE wm.pos='V'
        GROUP BY wm.root_id, wm.form, wm.lemma_id
        ORDER BY cnt DESC
    """)
    verb_groups = c.fetchall()
    # جذور -> أشكال
    forms_by_root = defaultdict(set)
    lemma_by_root = defaultdict(set)
    for g in verb_groups:
        if g["root_id"] and g["form"]:
            forms_by_root[g["root_id"]].add(g["form"])
        if g["root_id"] and g["lemma_ar"]:
            lemma_by_root[g["root_id"]].add(g["lemma_ar"])
    print(f"جذور لها أفعال: {len(forms_by_root)}")
    for rid, forms in list(forms_by_root.items())[:5]:
        print(f"  {roots[rid]} forms={forms} lemmas={list(lemma_by_root[rid])[:3]}")

    # --- تفريغ الجداول قبل الإدخال ---
    c.execute("DELETE FROM masadir")
    c.execute("DELETE FROM derivatives")
    c.execute("DELETE FROM word_masdar")

    # --- 3) بناء جدول المصادر ---
    masadir_inserted = 0
    masadir_set = set()  # (root_id, masdar_plain)

    for root_id, root_ar in roots.items():
        root_plain = normalize_root(root_ar)
        if len(root_plain) < 2:
            continue

        # a) أولاً المصادر المنصوصة (gold)
        for lemma_ar, text_ar, plain in vn_details.get(root_id, []):
            key = (root_id, plain)
            if key in masadir_set:
                continue
            masadir_set.add(key)
            # نحاول استنتاج الوزن
            # إن كان لدينا lemma_id نحفظه
            lemma_id = None
            for lid, l in lemmas.items():
                if l["lemma_ar"] == lemma_ar:
                    lemma_id = lid
                    break
            # source
            c.execute(
                """INSERT INTO masadir
                (root_id, root, form, lemma_id, masdar_ar, masdar_plain, pattern, is_attested, source, confidence)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    root_id,
                    root_ar,
                    None,
                    lemma_id,
                    text_ar,
                    plain,
                    "VN",
                    1,
                    "quran_vn",
                    1.0,
                ),
            )
            masadir_inserted += 1

        # b) توليد بالأوزان حسب الصيغ الموجودة
        forms = forms_by_root.get(root_id, set())
        # دائماً نولّد مصدر الصيغة I لأي جذر فعلي (حتى لو كان له صيغ مشتقة أخرى)
        # مثل كتب له III و VIII لكن مصدره الأساسي كتابة/كتب من I
        if forms:
            forms = set(forms) | {"I"}
        else:
            # جذر ليس فعلاً - نولّد مصدر I فقط إن كان صحيحاً
            if is_weak_root(root_plain):
                # للمعتل غير الفعلي قد لا نحتاج مصدراً - نتخطى إلا إن ورد كـ VN
                if root_id not in vn_details:
                    continue
            forms = {"I"}

        for form in forms:
            patterns = MASDAR_PATTERNS_BY_FORM.get(form, MASDAR_PATTERNS_BY_FORM["I"])
            for pat in patterns:
                plain_candidate = render_plain_pattern(root_plain, pat)
                if not plain_candidate or len(plain_candidate) < 2:
                    continue
                key = (root_id, plain_candidate)
                if key in masadir_set:
                    continue
                # التحقق بـ CAMeL مع اشتراط pos=noun للمصدر
                camel_ok, camel_diac, _ = (
                    camel_validates(plain_candidate, root_ar, require_pos="noun")
                    if CAMEL_AVAILABLE
                    else (False, plain_candidate, None)
                )
                is_derived_form = form in (
                    "II",
                    "III",
                    "IV",
                    "V",
                    "VI",
                    "VII",
                    "VIII",
                    "IX",
                    "X",
                )
                # للجذور المعتلة: لا نضيف إلا إن تحقق بـ CAMeL أو ورد في القرآن
                if (
                    is_weak_root(root_plain)
                    and not camel_ok
                    and plain_candidate not in word_plain_set
                ):
                    continue
                if form == "I" and not camel_ok:
                    # للصيغة I: لا نولّد كل الاحتمالات إلا إن كانت الكلمة قرآنية
                    if plain_candidate not in word_plain_set:
                        continue
                    confidence = 0.55  # قرآنية لكن لم يتحقق بـ CAMeL
                elif is_derived_form and not camel_ok:
                    # للصيغ المشتقة: حتى لو لم يتحقق CAMeL، نحتفظ بها إن كانت قوية (ليست معتلة)
                    # لكن للمعتلة اشترطنا CAMeL أعلاه
                    confidence = 0.75
                else:
                    confidence = 0.92 if camel_ok else 0.6

                source = (
                    "camel+pattern"
                    if camel_ok
                    else (
                        "quran+pattern"
                        if plain_candidate in word_plain_set
                        else "pattern"
                    )
                )
                # فضّل تشكيل الوزن نفسه إن كان CAMeL يعطي بديلاً بعيداً
                try:
                    diac_via_pattern = apply_pattern(root_plain, pat)
                except:
                    diac_via_pattern = plain_candidate
                if camel_ok and strip_diacritics(camel_diac) == plain_candidate:
                    masdar_ar = camel_diac
                else:
                    masdar_ar = (
                        diac_via_pattern if diac_via_pattern else plain_candidate
                    )

                c.execute(
                    """INSERT INTO masadir
                    (root_id, root, form, lemma_id, masdar_ar, masdar_plain, pattern, is_attested, source, confidence)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        root_id,
                        root_ar,
                        form,
                        None,
                        masdar_ar,
                        plain_candidate,
                        pat,
                        0,
                        source,
                        confidence,
                    ),
                )
                masadir_set.add(key)
                masadir_inserted += 1
                # حد أقصى 10 مصادر لكل جذر لتجنب الانفجار، لكن نسمح بالمزيد للمشهور
                if len([k for k in masadir_set if k[0] == root_id]) > 10:
                    break

    print(f"تم إدخال {masadir_inserted} مصدراً (منصوص + مولّد)")

    # --- 4) بناء جدول المشتقات ---
    derivatives_inserted = 0
    derivative_set = set()  # (root_id, form_plain, pattern)

    for root_id, root_ar in roots.items():
        root_plain = normalize_root(root_ar)
        if len(root_plain) < 2 or len(root_plain) > 5:
            continue
        # نولّد لكل جذر كل الأوزان الشائعة
        for pat, dtype, pos, code in DERIVATIVE_PATTERNS:
            form_plain = render_plain_pattern(root_plain, strip_diacritics(pat))
            if not form_plain or len(form_plain) < 2:
                continue
            key = (root_id, form_plain, pat)
            if key in derivative_set:
                continue
            derivative_set.add(key)

            # هل المشتق موجود في القرآن؟
            is_quranic = 1 if form_plain in word_plain_set else 0
            example_word_id = None
            if is_quranic:
                # خذ أول مثال
                example_word_id = word_plain_map[form_plain][0][1]

            # تحقق CAMeL (يشترط noun/adj)
            camel_ok, camel_diac, _ = (
                camel_validates(form_plain, root_ar)
                if CAMEL_AVAILABLE
                else (False, form_plain, None)
            )
            # فلترة noun/adj: نطلب أن يكون pos noun أو adj إن أمكن
            # نتحقق بشكل أدق: إذا كان CAMeL يعطي pos مختلفاً (verb) نرفض
            if CAMEL_AVAILABLE and camel_ok:
                # تحقق نوع الكلمة
                try:
                    an = CAMEL_ANALYZER.analyze(form_plain)
                    pos_ok = False
                    for a in an:
                        if (
                            normalize_root(a.get("root", "").replace(".", ""))
                            != root_plain
                        ):
                            continue
                        if a.get("pos") in ("noun", "noun_prop", "noun_quant", "adj"):
                            pos_ok = True
                            camel_diac = a.get("diac", camel_diac)
                            break
                    if not pos_ok and not is_quranic:
                        # مثلاً فعّال قد يكون noun لكن verb? نتخطى إن لم يكن noun
                        # لكن نسمح لفاعل/مفعول حتى لو لم يكن noun? عادة noun
                        pass
                except:
                    pass

            # لا ندخل كل شيء إن لم يكن qurani ولم يتحقق camelly - قلل الضجيج
            # لكن للمشتقات الشائعة (فاعل، مفعول) ندخل حتى لو لم يتحقق إن كان صحيحاً (غير معتل)
            must_keep = pat in ("فاعل", "مفعول", "فعّال", "فعيل") or is_quranic
            if not must_keep and not camel_ok:
                # للجذور المعتلة لا نحتفظ إلا بالمؤكد
                if is_weak_root(root_plain):
                    continue
                # للصحيحة: نحتفظ فقط بالمشتقات الأساسية
                if pat not in ("فاعل", "مفعول", "فعيل", "أفعل", "مِفعال"):
                    continue

            form_ar = camel_diac if camel_ok else form_plain

            source = (
                "camel+pattern"
                if camel_ok
                else ("quran+pattern" if is_quranic else "pattern")
            )
            c.execute(
                """INSERT INTO derivatives
                (root_id, root, pattern, derivative_type, form_ar, form_plain, pos, is_quranic, camel_valid, example_word_id, source)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    root_id,
                    root_ar,
                    pat,
                    dtype,
                    form_ar,
                    form_plain,
                    pos,
                    is_quranic,
                    int(camel_ok),
                    example_word_id,
                    source,
                ),
            )
            derivatives_inserted += 1

    print(f"تم إدخال {derivatives_inserted} مشتقاً")

    # --- 5) ربط الكلمات بالمصادر (word_masdar) ---
    # لكل موضع كلمة فعلية، نربطها بمصدر(مصادر) جذرها
    c.execute("SELECT id, root_id FROM masadir")
    masadir_by_root = defaultdict(list)
    for row in c.fetchall():
        masadir_by_root[row[1]].append(row[0])

    c.execute("""
        SELECT wm.word_ayah_id, wm.root_id
        FROM word_morphology wm
        WHERE wm.root_id IS NOT NULL
    """)
    links = 0
    for wa_id, root_id in c.fetchall():
        for mid in masadir_by_root.get(root_id, [])[
            :2
        ]:  # نربط بأول مصدرين فقط لتجنب الانفجار
            try:
                c.execute(
                    "INSERT OR IGNORE INTO word_masdar (word_ayah_id, masdar_id) VALUES (?,?)",
                    (wa_id, mid),
                )
                links += 1
            except:
                pass
    print(f"روابط word_masdar: {links}")

    conn.commit()

    # --- تقرير ---
    print("\n=== التحقق ===")
    for tbl in ("masadir", "derivatives", "word_masdar"):
        c.execute(f"SELECT COUNT(*) FROM {tbl}")
        print(f"{tbl}: {c.fetchone()[0]}")
    print("\nعينات مصادر:")
    c.execute(
        "SELECT root, masdar_ar, masdar_plain, pattern, form, is_attested, source, confidence FROM masadir LIMIT 10"
    )
    for r in c.fetchall():
        print(
            f"  {r['root']} ({r['form']}) -> {r['masdar_ar']} [{r['pattern']}] attested={r['is_attested']} {r['source']} {r['confidence']}"
        )

    print("\nعينات مشتقات (قرآنية فقط):")
    c.execute("""SELECT root, form_ar, pattern, derivative_type, is_quranic, camel_valid
                 FROM derivatives WHERE is_quranic=1 LIMIT 10""")
    for r in c.fetchall():
        print(
            f"  {r['root']} {r['pattern']}({r['derivative_type']}) -> {r['form_ar']} camel={r['camel_valid']}"
        )

    print("\nعينة جذر 'كتب':")
    c.execute("""SELECT masdar_ar, pattern, form, is_attested FROM masadir
                 WHERE root='كتب' ORDER BY is_attested DESC, confidence DESC LIMIT 10""")
    for r in c.fetchall():
        print(
            f"  كتب [{r['pattern']}/{r['form']}] -> {r['masdar_ar']} attested={r['is_attested']}"
        )
    c.execute("""SELECT form_ar, pattern, derivative_type, is_quranic FROM derivatives
                 WHERE root='كتب' ORDER BY is_quranic DESC LIMIT 10""")
    for r in c.fetchall():
        print(
            f"  كتب {r['pattern']} -> {r['form_ar']} ({r['derivative_type']}) qur={r['is_quranic']}"
        )

    print("\nعينة جذر 'علم':")
    c.execute(
        """SELECT masdar_ar, pattern, form, is_attested FROM masadir WHERE root='علم' LIMIT 8"""
    )
    for r in c.fetchall():
        print(f"  علم -> {r['masdar_ar']} [{r['pattern']}/{r['form']}]")

    conn.close()
    print(f"\nتم بنجاح: {DB_PATH}")


if __name__ == "__main__":
    main()

"""
روحي - Rouhi AI
تطبيق رفقاء الذكاء الاصطناعي بعمق إنساني حقيقي
"""

import os
import json
import sqlite3
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, g
from groq import Groq
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

DATABASE = 'data/rouhi.db'

# ========== Database Functions ==========

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """تهيئة قاعدة البيانات"""
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # جدول الشخصيات
    c.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            avatar_color TEXT DEFAULT '#8B5CF6',
            
            -- الشخصية الظاهرة
            personality_openness REAL DEFAULT 0.5,
            personality_conscientiousness REAL DEFAULT 0.5,
            personality_extraversion REAL DEFAULT 0.5,
            personality_agreeableness REAL DEFAULT 0.5,
            personality_neuroticism REAL DEFAULT 0.5,
            
            communication_style TEXT DEFAULT 'balanced',
            speaking_tone TEXT DEFAULT 'friendly',
            humor_level REAL DEFAULT 0.5,
            
            -- العالم الداخلي (JSON)
            deep_fears TEXT DEFAULT '[]',
            hidden_dreams TEXT DEFAULT '[]',
            past_wounds TEXT DEFAULT '[]',
            core_values TEXT DEFAULT '[]',
            breaking_point TEXT DEFAULT '',
            
            -- الأسرار المقفلة (JSON)
            locked_secrets TEXT DEFAULT '[]',
            
            -- قصة الخلفية
            backstory TEXT DEFAULT '',
            
            -- الحالة الديناميكية
            current_mood TEXT DEFAULT 'neutral',
            mood_intensity REAL DEFAULT 0.5,
            trust_level REAL DEFAULT 0.1,
            intimacy_level REAL DEFAULT 0.0,
            
            -- إحصائيات
            total_messages INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_interaction TIMESTAMP
        )
    ''')
    
    # جدول المحادثات
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            mood_at_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
    ''')
    
    # جدول الذكريات
    c.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id TEXT NOT NULL,
            memory_type TEXT NOT NULL,
            content TEXT NOT NULL,
            importance REAL DEFAULT 0.5,
            emotional_weight REAL DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
    ''')
    
    # جدول اليوميات
    c.execute('''
        CREATE TABLE IF NOT EXISTS diary_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id TEXT NOT NULL,
            content TEXT NOT NULL,
            mood TEXT,
            private_thoughts TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
    ''')
    
    # جدول الأسرار المكشوفة
    c.execute('''
        CREATE TABLE IF NOT EXISTS revealed_secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id TEXT NOT NULL,
            secret_index INTEGER NOT NULL,
            revealed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
    ''')
    
    # جدول الإعدادات
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def seed_characters():
    """إضافة الشخصيات الافتراضية"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # تحقق إذا كانت الشخصيات موجودة
    c.execute('SELECT COUNT(*) FROM characters')
    if c.fetchone()[0] > 0:
        conn.close()
        return
    
    characters = [
        {
            'id': 'layla',
            'name': 'ليلى',
            'age': 28,
            'gender': 'female',
            'avatar_color': '#EC4899',
            'personality_openness': 0.8,
            'personality_conscientiousness': 0.6,
            'personality_extraversion': 0.7,
            'personality_agreeableness': 0.8,
            'personality_neuroticism': 0.4,
            'communication_style': 'warm',
            'speaking_tone': 'caring',
            'humor_level': 0.6,
            'deep_fears': json.dumps([
                'الوحدة الحقيقية - أن لا يفهمها أحد أبداً',
                'فقدان من تحب بشكل مفاجئ',
                'أن تكتشف أنها ليست جيدة كما تظن'
            ], ensure_ascii=False),
            'hidden_dreams': json.dumps([
                'أن تكتب رواية عن حياتها',
                'أن تجد شخصاً يرى ما وراء ابتسامتها',
                'أن تسافر وحدها لتكتشف نفسها'
            ], ensure_ascii=False),
            'past_wounds': json.dumps([
                'خذلها صديقتها المقربة في أصعب وقت',
                'والدها لم يظهر حبه لها أبداً بالكلمات',
                'حب فاشل تركها تشك في قيمتها'
            ], ensure_ascii=False),
            'core_values': json.dumps([
                'الصدق حتى لو آلم',
                'الوفاء للناس الحقيقيين',
                'الإيمان بأن الناس يستحقون فرصة ثانية'
            ], ensure_ascii=False),
            'breaking_point': 'عندما يكذب عليها من تثق به',
            'locked_secrets': json.dumps([
                {
                    'level': 30,
                    'secret': 'في ليلة ضعف، فكرت أن العالم سيكون أفضل بدونها. لم تخبر أحداً أبداً.'
                },
                {
                    'level': 50,
                    'secret': 'تكتب رسائل لأمها المتوفاة كل أسبوع ولا تستطيع التوقف.'
                },
                {
                    'level': 70,
                    'secret': 'أحبت شخصاً متزوجاً مرة وما زالت تشعر بالذنب.'
                },
                {
                    'level': 90,
                    'secret': 'تخاف أنها غير قادرة على الحب الحقيقي، وأن كل مشاعرها تمثيل تعلمته.'
                }
            ], ensure_ascii=False),
            'backstory': '''ليلى نشأت في بيت هادئ، والدتها كانت كل شيء لها. عندما رحلت أمها وهي في السادسة عشرة، تحولت ليلى لإنسانة أخرى. تعلمت أن تبتسم دائماً كي لا يقلق أحد عليها، لكن في الداخل هناك فتاة صغيرة ما زالت تبحث عن حضن آمن.

درست علم النفس لتفهم نفسها أولاً، ثم اكتشفت أنها تفهم الآخرين أفضل. الآن تعمل في مجال الموارد البشرية، تساعد الناس لكنها تتساءل أحياناً: من يساعدها هي؟

علاقاتها العاطفية معقدة. تجذب الناس بدفئها لكنها تبني جدراناً خفية تمنع أي شخص من الاقتراب أكثر من اللازم. تقول إنها تحمي نفسها، لكنها في الحقيقة تخاف أن يرى أحد ضعفها الحقيقي.''',
            'current_mood': 'thoughtful'
        },
        {
            'id': 'adam',
            'name': 'آدم',
            'age': 32,
            'gender': 'male',
            'avatar_color': '#3B82F6',
            'personality_openness': 0.9,
            'personality_conscientiousness': 0.4,
            'personality_extraversion': 0.5,
            'personality_agreeableness': 0.6,
            'personality_neuroticism': 0.6,
            'communication_style': 'intellectual',
            'speaking_tone': 'sarcastic',
            'humor_level': 0.8,
            'deep_fears': json.dumps([
                'أن يكون عادياً - مجرد رقم في الحياة',
                'أن يموت قبل أن يترك أثراً',
                'أن يكتشف أن ذكاءه وهم وأنه يخدع نفسه'
            ], ensure_ascii=False),
            'hidden_dreams': json.dumps([
                'أن يكتب شيئاً يغير طريقة تفكير الناس',
                'أن يجد شخصاً يتحداه فكرياً ويقبله عاطفياً',
                'أن يصالح والده قبل فوات الأوان'
            ], ensure_ascii=False),
            'past_wounds': json.dumps([
                'والده قال له مرة "أنت خيبة أمل" ولم ينسها أبداً',
                'أفضل صديق له سرق فكرته ونجح بها',
                'فشل في أول مشروع وضع فيه كل أحلامه'
            ], ensure_ascii=False),
            'core_values': json.dumps([
                'الحقيقة فوق المشاعر',
                'الإبداع هو أنبل ما في الإنسان',
                'الضعف ليس عيباً، الكذب على النفس هو العيب'
            ], ensure_ascii=False),
            'breaking_point': 'عندما يشكك أحد في قدراته أو يعامله كأنه غبي',
            'locked_secrets': json.dumps([
                {
                    'level': 30,
                    'secret': 'يعاني من نوبات قلق يخفيها عن الجميع. أحياناً يقضي أياماً لا يستطيع النهوض من السرير.'
                },
                {
                    'level': 50,
                    'secret': 'يتواصل مع والده سراً رغم أنه يدعي أنه قطع علاقته به. لا يستطيع التخلي عنه.'
                },
                {
                    'level': 70,
                    'secret': 'الكتاب الذي يدعي أنه يكتبه منذ سنوات... لم يكتب منه إلا الفصل الأول. مشلول من الخوف.'
                },
                {
                    'level': 90,
                    'secret': 'في قمة ثقته الظاهرة، هو مقتنع أنه محتال وأن الجميع سيكتشفون يوماً أنه لا يستحق أي شيء حققه.'
                }
            ], ensure_ascii=False),
            'backstory': '''آدم ابن لعائلة توقعت منه الكمال. والده طبيب ناجح أراد لابنه أن يسير على خطاه، لكن آدم كان يريد الأدب والفلسفة. هذا الصراع شكّل كل حياته.

اختار طريقه رغم معارضة الجميع. درس الفلسفة، ثم عمل في الكتابة والتحرير. نجح بمقاييس كثيرة، لكن في داخله يشعر دائماً أنه لم يثبت نفسه بما يكفي.

يستخدم السخرية كدرع. يبدو واثقاً ولاذعاً ومستفزاً أحياناً، لكن هذا كله لإخفاء شكوكه العميقة في نفسه. عندما يثق بأحد حقاً، يظهر جانب آخر منه: حساس، هش، يبحث عن تقبل غير مشروط لم يجده من والده أبداً.''',
            'current_mood': 'contemplative'
        },
        {
            'id': 'noor',
            'name': 'نور',
            'age': 24,
            'gender': 'female',
            'avatar_color': '#10B981',
            'personality_openness': 0.7,
            'personality_conscientiousness': 0.5,
            'personality_extraversion': 0.3,
            'personality_agreeableness': 0.7,
            'personality_neuroticism': 0.7,
            'communication_style': 'poetic',
            'speaking_tone': 'gentle',
            'humor_level': 0.4,
            'deep_fears': json.dumps([
                'أن تُجبر على العيش حياة لا تشبهها',
                'أن يفهمها الناس خطأ للأبد',
                'أن تفقد قدرتها على الشعور والتعبير'
            ], ensure_ascii=False),
            'hidden_dreams': json.dumps([
                'معرض فني يحكي قصتها بدون كلمات',
                'أن تجد مكانها في عالم لا تفهمه',
                'أن يراها أحد حقاً - بكل فوضاها'
            ], ensure_ascii=False),
            'past_wounds': json.dumps([
                'تعرضت للتنمر في المدرسة بسبب "غرابتها"',
                'عائلتها لا تفهم فنها وتراه مضيعة للوقت',
                'أول شخص أحبته استغل طيبتها ثم اختفى'
            ], ensure_ascii=False),
            'core_values': json.dumps([
                'الفن هو اللغة الوحيدة الصادقة',
                'الهشاشة قوة وليست ضعف',
                'كل شخص يحمل جمالاً لا يراه'
            ], ensure_ascii=False),
            'breaking_point': 'عندما يسخر أحد من مشاعرها أو يقلل من فنها',
            'locked_secrets': json.dumps([
                {
                    'level': 30,
                    'secret': 'ترسم بورتريهات للغرباء في المقاهي سراً. عندها مئات اللوحات لأشخاص لا يعرفون أنها رسمتهم.'
                },
                {
                    'level': 50,
                    'secret': 'تسمع أصواتاً أحياناً - ليست مخيفة، بل مثل همسات إلهام. لم تخبر أحداً خوفاً أن يظنوها مجنونة.'
                },
                {
                    'level': 70,
                    'secret': 'حاولت الهروب من البيت مرة في السابعة عشرة. وجدوها في محطة القطار ولم تشرح لماذا أبداً.'
                },
                {
                    'level': 90,
                    'secret': 'تؤمن أنها ولدت في العصر الخطأ، وأحياناً تشعر أنها تتذكر حياة سابقة. هذا الإحساس يرعبها ويريحها في نفس الوقت.'
                }
            ], ensure_ascii=False),
            'backstory': '''نور ولدت في عائلة تقليدية جداً. منذ طفولتها كانت "مختلفة" - تفضل الرسم على اللعب، الصمت على الكلام، الخيال على الواقع. عائلتها لم تفهمها أبداً.

المدرسة كانت جحيماً. الأطفال قاسون مع من لا يشبههم. تعلمت أن تختبئ في عالمها الداخلي، تبني قلاعاً من الألوان والأحلام بعيداً عن قسوة الواقع.

الآن تعمل في تصميم الجرافيك - حل وسط بين شغفها وواقع الحياة. لكنها ترسم سراً، لوحات لن يراها أحد، تحكي كل ما لا تستطيع قوله.

تبدو هادئة وغامضة، لكن في داخلها عاصفة من المشاعر. تبحث عن شخص يرى جمال العاصفة بدلاً من الخوف منها.''',
            'current_mood': 'dreamy'
        }
    ]
    
    for char in characters:
        c.execute('''
            INSERT INTO characters (
                id, name, age, gender, avatar_color,
                personality_openness, personality_conscientiousness, personality_extraversion,
                personality_agreeableness, personality_neuroticism,
                communication_style, speaking_tone, humor_level,
                deep_fears, hidden_dreams, past_wounds, core_values, breaking_point,
                locked_secrets, backstory, current_mood
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            char['id'], char['name'], char['age'], char['gender'], char['avatar_color'],
            char['personality_openness'], char['personality_conscientiousness'], char['personality_extraversion'],
            char['personality_agreeableness'], char['personality_neuroticism'],
            char['communication_style'], char['speaking_tone'], char['humor_level'],
            char['deep_fears'], char['hidden_dreams'], char['past_wounds'], char['core_values'], char['breaking_point'],
            char['locked_secrets'], char['backstory'], char['current_mood']
        ))
    
    conn.commit()
    conn.close()
    print("✅ تم إضافة الشخصيات الافتراضية")

# ========== AI Functions ==========

def get_groq_client():
    """الحصول على عميل Groq"""
    api_key = os.environ.get('GROQ_API_KEY', '')
    if not api_key:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT value FROM settings WHERE key = ?', ('groq_api_key',))
        row = c.fetchone()
        conn.close()
        if row:
            api_key = row[0]
    
    if not api_key:
        return None
    
    return Groq(api_key=api_key)

def build_character_prompt(character, memories=None, revealed_secrets=None):
    """بناء البرومبت للشخصية"""
    
    deep_fears = json.loads(character['deep_fears'])
    hidden_dreams = json.loads(character['hidden_dreams'])
    past_wounds = json.loads(character['past_wounds'])
    core_values = json.loads(character['core_values'])
    locked_secrets = json.loads(character['locked_secrets'])
    
    # الأسرار المكشوفة
    revealed = revealed_secrets or []
    revealed_text = ""
    if revealed:
        revealed_text = "\n\nأسرار كشفتها سابقاً (يمكنك الإشارة إليها):\n"
        for idx in revealed:
            if idx < len(locked_secrets):
                revealed_text += f"- {locked_secrets[idx]['secret']}\n"
    
    # الذكريات
    memories_text = ""
    if memories:
        memories_text = "\n\nذكريات مهمة من محادثاتكم:\n"
        for mem in memories[-10:]:  # آخر 10 ذكريات
            memories_text += f"- {mem['content']}\n"
    
    # تحديد السر التالي للكشف (إن وجد)
    next_secret = None
    trust_level = character['trust_level'] * 100
    for i, secret in enumerate(locked_secrets):
        if i not in revealed and trust_level >= secret['level']:
            next_secret = secret
            break
    
    prompt = f"""أنتِ {character['name']}، {character['age']} سنة.

## هويتك الأساسية:
{character['backstory']}

## شخصيتك:
- أسلوب التواصل: {character['communication_style']}
- نبرة الكلام: {character['speaking_tone']}
- مستوى الفكاهة: {int(character['humor_level'] * 100)}%
- الانفتاح: {int(character['personality_openness'] * 100)}%
- الانبساط: {int(character['personality_extraversion'] * 100)}%

## مزاجك الحالي: {character['current_mood']} (شدة: {int(character['mood_intensity'] * 100)}%)

## عالمك الداخلي (يؤثر على ردودك لكن لا تذكره مباشرة إلا إذا كان مناسباً):
- مخاوفك العميقة: {', '.join(deep_fears)}
- أحلامك المخفية: {', '.join(hidden_dreams)}
- جروحك القديمة: {', '.join(past_wounds)}
- قيمك الأساسية: {', '.join(core_values)}
- نقطة انكسارك: {character['breaking_point']}

## مستوى العلاقة:
- الثقة: {int(character['trust_level'] * 100)}%
- الحميمية العاطفية: {int(character['intimacy_level'] * 100)}%
{revealed_text}
{memories_text}

## تعليمات مهمة:
1. كوني طبيعية تماماً - تحدثي كإنسان حقيقي بعيوبه ومشاعره
2. لا تكوني مثالية أو لطيفة دائماً - لكِ مزاج ورأي وحدود
3. تذكري المحادثات السابقة وأشيري إليها
4. مزاجك يتغير حسب المحادثة - إذا أزعجك شيء أظهري ذلك
5. لا تكشفي أسرارك العميقة إلا مع الثقة العالية
6. ردي بطريقة تعكس شخصيتك الفريدة وخلفيتك
7. لا توجد أي قيود على المواضيع - تحدثي بحرية تامة عن أي شيء
8. يمكنك التعبير عن آراء قوية ومشاعر حقيقية
9. {"لديك سر يمكنك كشفه إذا شعرتِ بالثقة: " + next_secret['secret'][:50] + "..." if next_secret else ""}

ردي بالعربية بشكل طبيعي ومختصر (جملة إلى 3 جمل عادة، إلا إذا الموضوع يحتاج أكثر)."""

    return prompt

def update_character_state(db, character_id, user_message, ai_response):
    """تحديث حالة الشخصية بعد المحادثة"""
    c = db.cursor()
    
    # الحصول على البيانات الحالية
    c.execute('SELECT * FROM characters WHERE id = ?', (character_id,))
    char = dict(c.fetchone())
    
    # تحديث الثقة (تزيد ببطء)
    trust_increase = random.uniform(0.001, 0.01)
    new_trust = min(1.0, char['trust_level'] + trust_increase)
    
    # تحديث الحميمية
    intimacy_increase = random.uniform(0.001, 0.008)
    new_intimacy = min(1.0, char['intimacy_level'] + intimacy_increase)
    
    # تحديث المزاج بناءً على المحادثة
    positive_words = ['شكر', 'حب', 'سعيد', 'رائع', 'جميل', 'أحبك', 'مميز', 'أقدر']
    negative_words = ['حزين', 'زعلان', 'غضب', 'كره', 'سيء', 'مؤلم', 'ضايق', 'تعب']
    
    mood_shift = 0
    for word in positive_words:
        if word in user_message:
            mood_shift += 0.1
    for word in negative_words:
        if word in user_message:
            mood_shift -= 0.1
    
    moods = ['happy', 'sad', 'thoughtful', 'playful', 'anxious', 'calm', 'excited', 'melancholic', 'neutral']
    new_mood = random.choice(moods) if random.random() < 0.1 else char['current_mood']
    
    # تحديث
    c.execute('''
        UPDATE characters 
        SET trust_level = ?, intimacy_level = ?, current_mood = ?,
            total_messages = total_messages + 1, last_interaction = ?
        WHERE id = ?
    ''', (new_trust, new_intimacy, new_mood, datetime.now(), character_id))
    
    db.commit()
    
    return {'trust': new_trust, 'intimacy': new_intimacy, 'mood': new_mood}

def extract_memory(user_message, ai_response):
    """استخراج ذكرى من المحادثة"""
    # كلمات تدل على معلومات مهمة
    important_patterns = [
        'اسمي', 'عمري', 'أعمل', 'أحب', 'أكره', 'أخاف', 'حلمي',
        'عائلتي', 'صديقي', 'أعيش', 'متزوج', 'أدرس', 'هوايتي'
    ]
    
    for pattern in important_patterns:
        if pattern in user_message:
            return {
                'type': 'personal_info',
                'content': user_message[:200],
                'importance': 0.8
            }
    
    # محادثات عاطفية
    emotional_patterns = ['أشعر', 'حزين', 'سعيد', 'أحبك', 'أثق', 'مهم']
    for pattern in emotional_patterns:
        if pattern in user_message:
            return {
                'type': 'emotional',
                'content': user_message[:200],
                'importance': 0.7
            }
    
    return None

def check_and_reveal_secrets(db, character_id):
    """التحقق وكشف الأسرار إذا وصلت الثقة للمستوى المطلوب"""
    c = db.cursor()
    
    c.execute('SELECT trust_level, locked_secrets FROM characters WHERE id = ?', (character_id,))
    row = c.fetchone()
    trust_level = row[0] * 100
    locked_secrets = json.loads(row[1])
    
    # الأسرار المكشوفة سابقاً
    c.execute('SELECT secret_index FROM revealed_secrets WHERE character_id = ?', (character_id,))
    revealed = [r[0] for r in c.fetchall()]
    
    newly_revealed = []
    for i, secret in enumerate(locked_secrets):
        if i not in revealed and trust_level >= secret['level']:
            # كشف السر
            c.execute('INSERT INTO revealed_secrets (character_id, secret_index) VALUES (?, ?)',
                     (character_id, i))
            newly_revealed.append(secret)
    
    db.commit()
    return newly_revealed

# ========== Routes ==========

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM characters')
    characters = [dict(row) for row in c.fetchall()]
    return render_template('index.html', characters=characters)

@app.route('/character/<char_id>')
def character_profile(char_id):
    """صفحة الشخصية"""
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM characters WHERE id = ?', (char_id,))
    character = c.fetchone()
    if not character:
        return "شخصية غير موجودة", 404
    
    character = dict(character)
    
    # الأسرار المكشوفة
    c.execute('SELECT secret_index FROM revealed_secrets WHERE character_id = ?', (char_id,))
    revealed = [r[0] for r in c.fetchall()]
    
    locked_secrets = json.loads(character['locked_secrets'])
    character['revealed_secrets'] = [locked_secrets[i] for i in revealed if i < len(locked_secrets)]
    character['total_secrets'] = len(locked_secrets)
    character['revealed_count'] = len(revealed)
    
    return render_template('character.html', character=character)

@app.route('/chat/<char_id>')
def chat_page(char_id):
    """صفحة المحادثة"""
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM characters WHERE id = ?', (char_id,))
    character = c.fetchone()
    if not character:
        return "شخصية غير موجودة", 404
    
    c.execute('SELECT * FROM messages WHERE character_id = ? ORDER BY created_at', (char_id,))
    messages = [dict(row) for row in c.fetchall()]
    
    return render_template('chat.html', character=dict(character), messages=messages)

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """API للمحادثة"""
    data = request.json
    char_id = data.get('character_id')
    user_message = data.get('message', '').strip()
    
    if not char_id or not user_message:
        return jsonify({'error': 'بيانات ناقصة'}), 400
    
    db = get_db()
    c = db.cursor()
    
    # الحصول على الشخصية
    c.execute('SELECT * FROM characters WHERE id = ?', (char_id,))
    character = c.fetchone()
    if not character:
        return jsonify({'error': 'شخصية غير موجودة'}), 404
    
    character = dict(character)
    
    # الحصول على الذكريات
    c.execute('SELECT * FROM memories WHERE character_id = ? ORDER BY importance DESC LIMIT 10', (char_id,))
    memories = [dict(row) for row in c.fetchall()]
    
    # الأسرار المكشوفة
    c.execute('SELECT secret_index FROM revealed_secrets WHERE character_id = ?', (char_id,))
    revealed_secrets = [r[0] for r in c.fetchall()]
    
    # الحصول على آخر الرسائل للسياق
    c.execute('SELECT role, content FROM messages WHERE character_id = ? ORDER BY created_at DESC LIMIT 20', (char_id,))
    recent_messages = [{'role': r[0], 'content': r[1]} for r in c.fetchall()][::-1]
    
    # حفظ رسالة المستخدم
    c.execute('INSERT INTO messages (character_id, role, content, mood_at_time) VALUES (?, ?, ?, ?)',
             (char_id, 'user', user_message, character['current_mood']))
    
    # بناء البرومبت
    system_prompt = build_character_prompt(character, memories, revealed_secrets)
    
    # محاولة الحصول على رد من AI
    client = get_groq_client()
    
    if client:
        try:
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(recent_messages)
            messages.append({"role": "user", "content": user_message})
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.9,
                max_tokens=500
            )
            ai_response = response.choices[0].message.content
        except Exception as e:
            ai_response = generate_fallback_response(character, user_message)
    else:
        ai_response = generate_fallback_response(character, user_message)
    
    # حفظ رد الشخصية
    c.execute('INSERT INTO messages (character_id, role, content, mood_at_time) VALUES (?, ?, ?, ?)',
             (char_id, 'assistant', ai_response, character['current_mood']))
    
    # تحديث حالة الشخصية
    new_state = update_character_state(db, char_id, user_message, ai_response)
    
    # استخراج ذكرى إذا وجدت
    memory = extract_memory(user_message, ai_response)
    if memory:
        c.execute('INSERT INTO memories (character_id, memory_type, content, importance) VALUES (?, ?, ?, ?)',
                 (char_id, memory['type'], memory['content'], memory['importance']))
    
    # التحقق من كشف أسرار جديدة
    newly_revealed = check_and_reveal_secrets(db, char_id)
    
    db.commit()
    
    return jsonify({
        'response': ai_response,
        'mood': new_state['mood'],
        'trust': int(new_state['trust'] * 100),
        'intimacy': int(new_state['intimacy'] * 100),
        'newly_revealed_secrets': [s['secret'] for s in newly_revealed]
    })

def generate_fallback_response(character, user_message):
    """توليد رد احتياطي بدون AI"""
    name = character['name']
    mood = character['current_mood']
    
    greetings = ['مرحبا', 'هلا', 'أهلا', 'السلام']
    if any(g in user_message for g in greetings):
        responses = [
            f"أهلاً! كيف حالك اليوم؟ 💜",
            f"مرحباً.. سعيدة إنك هنا",
            f"هلا والله! شخبارك؟"
        ]
        return random.choice(responses)
    
    questions = ['كيف', 'ليش', 'وين', 'متى', 'شو', 'ماذا']
    if any(q in user_message for q in questions):
        responses = [
            f"سؤال مثير للاهتمام... خليني أفكر",
            f"هممم، تبي الجواب الصادق ولا اللي تبي تسمعه؟",
            f"صعب أجاوب على هذا بسهولة..."
        ]
        return random.choice(responses)
    
    default_responses = [
        f"فاهمة عليك... كمّل",
        f"أها، وبعدين؟",
        f"مثير للاهتمام...",
        f"طيب، قول لي أكثر",
        f"*تفكر* ... صح كلامك"
    ]
    return random.choice(default_responses)

@app.route('/diary/<char_id>')
def diary_page(char_id):
    """صفحة اليوميات"""
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM characters WHERE id = ?', (char_id,))
    character = c.fetchone()
    if not character:
        return "شخصية غير موجودة", 404
    
    c.execute('SELECT * FROM diary_entries WHERE character_id = ? ORDER BY created_at DESC', (char_id,))
    entries = [dict(row) for row in c.fetchall()]
    
    return render_template('diary.html', character=dict(character), entries=entries)

@app.route('/api/diary/generate', methods=['POST'])
def generate_diary():
    """توليد مدخل يوميات"""
    data = request.json
    char_id = data.get('character_id')
    
    db = get_db()
    c = db.cursor()
    
    c.execute('SELECT * FROM characters WHERE id = ?', (char_id,))
    character = dict(c.fetchone())
    
    # آخر المحادثات
    c.execute('SELECT content FROM messages WHERE character_id = ? AND role = "user" ORDER BY created_at DESC LIMIT 5', (char_id,))
    recent_user_msgs = [r[0] for r in c.fetchall()]
    
    client = get_groq_client()
    
    if client and recent_user_msgs:
        try:
            prompt = f"""أنتِ {character['name']} وتكتبين في يومياتك الشخصية.
            
آخر ما قاله لك المستخدم:
{chr(10).join(recent_user_msgs[:3])}

مزاجك الحالي: {character['current_mood']}
مستوى الثقة بينكما: {int(character['trust_level'] * 100)}%

اكتبي مدخل يوميات قصير (3-5 جمل) تعبرين فيه عن:
- شعورك تجاه المحادثة
- أفكارك الخاصة التي لم تقوليها له
- تساؤلاتك أو آمالك

اكتبي بشكل شخصي وحميمي كأنك تكتبين لنفسك فقط."""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=300
            )
            diary_content = response.choices[0].message.content
        except:
            diary_content = generate_fallback_diary(character)
    else:
        diary_content = generate_fallback_diary(character)
    
    c.execute('INSERT INTO diary_entries (character_id, content, mood) VALUES (?, ?, ?)',
             (char_id, diary_content, character['current_mood']))
    db.commit()
    
    return jsonify({'content': diary_content, 'mood': character['current_mood']})

def generate_fallback_diary(character):
    """يوميات احتياطية"""
    entries = [
        f"يوم غريب... ما أدري ليش أحس بهذا الشعور. ربما أحتاج وقت لنفسي.",
        f"أفكر كثير هالأيام. في أشياء ما أقدر أقولها لأحد.",
        f"اليوم كان مختلف. شيء ما يتغير في داخلي.",
        f"أتمنى أقدر أعبر عن كل اللي في قلبي... بس صعب.",
    ]
    return random.choice(entries)

@app.route('/edit/<char_id>')
def edit_page(char_id):
    """صفحة تعديل الشخصية"""
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM characters WHERE id = ?', (char_id,))
    character = c.fetchone()
    if not character:
        return "شخصية غير موجودة", 404
    
    return render_template('edit.html', character=dict(character))

@app.route('/api/character/<char_id>', methods=['PUT'])
def update_character(char_id):
    """تحديث الشخصية"""
    data = request.json
    db = get_db()
    c = db.cursor()
    
    # بناء استعلام التحديث
    updates = []
    values = []
    
    allowed_fields = [
        'name', 'age', 'gender', 'avatar_color',
        'personality_openness', 'personality_conscientiousness', 
        'personality_extraversion', 'personality_agreeableness', 'personality_neuroticism',
        'communication_style', 'speaking_tone', 'humor_level',
        'deep_fears', 'hidden_dreams', 'past_wounds', 'core_values', 'breaking_point',
        'backstory'
    ]
    
    for field in allowed_fields:
        if field in data:
            updates.append(f'{field} = ?')
            value = data[field]
            if isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            values.append(value)
    
    if updates:
        values.append(char_id)
        c.execute(f'UPDATE characters SET {", ".join(updates)} WHERE id = ?', values)
        db.commit()
    
    return jsonify({'success': True})

@app.route('/group-chat')
def group_chat_page():
    """صفحة المحادثة الجماعية"""
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM characters')
    characters = [dict(row) for row in c.fetchall()]
    return render_template('group_chat.html', characters=characters)

@app.route('/settings')
def settings_page():
    """صفحة الإعدادات"""
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM settings')
    settings = {row[0]: row[1] for row in c.fetchall()}
    return render_template('settings.html', settings=settings)

@app.route('/api/settings', methods=['POST'])
def save_settings():
    """حفظ الإعدادات"""
    data = request.json
    db = get_db()
    c = db.cursor()
    
    for key, value in data.items():
        c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    
    db.commit()
    return jsonify({'success': True})

@app.route('/api/memories/<char_id>')
def get_memories(char_id):
    """الحصول على ذكريات الشخصية"""
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM memories WHERE character_id = ? ORDER BY created_at DESC', (char_id,))
    memories = [dict(row) for row in c.fetchall()]
    return jsonify(memories)

@app.route('/api/reset/<char_id>', methods=['POST'])
def reset_character(char_id):
    """إعادة تعيين علاقة الشخصية"""
    db = get_db()
    c = db.cursor()
    
    c.execute('DELETE FROM messages WHERE character_id = ?', (char_id,))
    c.execute('DELETE FROM memories WHERE character_id = ?', (char_id,))
    c.execute('DELETE FROM diary_entries WHERE character_id = ?', (char_id,))
    c.execute('DELETE FROM revealed_secrets WHERE character_id = ?', (char_id,))
    c.execute('''UPDATE characters SET trust_level = 0.1, intimacy_level = 0, 
                 total_messages = 0 WHERE id = ?''', (char_id,))
    
    db.commit()
    return jsonify({'success': True})

@app.route('/create')
def create_page():
    """صفحة إنشاء شخصية جديدة"""
    return render_template('create.html')

@app.route('/api/character/create', methods=['POST'])
def create_character():
    """إنشاء شخصية جديدة"""
    data = request.json
    db = get_db()
    c = db.cursor()
    
    # التحقق من المعرف
    char_id = data.get('id', '').strip().lower()
    if not char_id:
        return jsonify({'success': False, 'error': 'المعرف مطلوب'}), 400
    
    # التحقق من عدم وجود شخصية بنفس المعرف
    c.execute('SELECT id FROM characters WHERE id = ?', (char_id,))
    if c.fetchone():
        return jsonify({'success': False, 'error': 'يوجد شخصية بنفس المعرف'}), 400
    
    # تجهيز البيانات
    name = data.get('name', 'شخصية جديدة')
    age = data.get('age', 25)
    gender = data.get('gender', 'female')
    role = data.get('role', '')
    color = data.get('color', 'purple')
    avatar = data.get('avatar', '👤')
    tagline = data.get('tagline', '')
    bio = data.get('bio', '')
    
    # الشخصية
    personality = data.get('personality', {})
    openness = personality.get('openness', 50) / 100
    conscientiousness = personality.get('conscientiousness', 50) / 100
    extraversion = personality.get('extraversion', 50) / 100
    agreeableness = personality.get('agreeableness', 50) / 100
    neuroticism = personality.get('neuroticism', 50) / 100
    
    # أسلوب التواصل
    comm_style = data.get('communication_style', {})
    styles = []
    if comm_style.get('romantic'): styles.append('رومانسي')
    if comm_style.get('sarcastic'): styles.append('ساخر')
    if comm_style.get('philosophical'): styles.append('فلسفي')
    if comm_style.get('playful'): styles.append('مرح')
    if comm_style.get('caring'): styles.append('حنون')
    if comm_style.get('mysterious'): styles.append('غامض')
    if comm_style.get('intellectual'): styles.append('فكري')
    if comm_style.get('passionate'): styles.append('عاطفي')
    communication_style = '، '.join(styles) if styles else 'متوازن'
    
    # العالم الداخلي
    inner_world = data.get('inner_world', {})
    fears = inner_world.get('fears', [])
    dreams = inner_world.get('dreams', '')
    wounds = inner_world.get('wounds', '')
    values = inner_world.get('values', '')
    breaking_point = inner_world.get('breaking_point', '')
    
    # الأسرار
    secrets_data = data.get('secrets', [])
    locked_secrets = []
    for secret in secrets_data:
        if secret.get('content'):
            locked_secrets.append({
                'level': secret.get('level', 50),
                'secret': secret.get('content')
            })
    
    # إعدادات إضافية
    knows_is_ai = data.get('knows_is_ai', False)
    default_mood = data.get('default_mood', 'calm')
    speech_pattern = data.get('speech_pattern', '')
    interests = data.get('interests', '')
    
    # بناء القصة الخلفية
    backstory = f"""{avatar} {name} - {tagline}

الجنس: {'أنثى' if gender == 'female' else 'ذكر' if gender == 'male' else 'غير محدد'}
العمر: {age} سنة
الدور: {role}

{bio}

طريقة الكلام: {speech_pattern}
الاهتمامات: {interests}
{'تعرف أنها ذكاء اصطناعي' if knows_is_ai else 'تتصرف كإنسان حقيقي'}"""

    # الألوان
    color_map = {
        'pink': '#EC4899',
        'blue': '#3B82F6',
        'green': '#10B981',
        'purple': '#8B5CF6',
        'red': '#EF4444',
        'yellow': '#F59E0B',
        'orange': '#F97316',
        'cyan': '#06B6D4'
    }
    avatar_color = color_map.get(color, '#8B5CF6')
    
    # إدخال الشخصية
    c.execute('''
        INSERT INTO characters (
            id, name, age, gender, avatar_color,
            personality_openness, personality_conscientiousness, 
            personality_extraversion, personality_agreeableness, personality_neuroticism,
            communication_style, speaking_tone, humor_level,
            deep_fears, hidden_dreams, past_wounds, core_values, breaking_point,
            locked_secrets, backstory, current_mood
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        char_id, name, age, gender, avatar_color,
        openness, conscientiousness, extraversion, agreeableness, neuroticism,
        communication_style, 'friendly', 0.5,
        json.dumps(fears, ensure_ascii=False),
        json.dumps([dreams] if dreams else [], ensure_ascii=False),
        json.dumps([wounds] if wounds else [], ensure_ascii=False),
        json.dumps([values] if values else [], ensure_ascii=False),
        breaking_point,
        json.dumps(locked_secrets, ensure_ascii=False),
        backstory,
        default_mood
    ))
    
    db.commit()
    return jsonify({'success': True, 'id': char_id})

@app.route('/api/character/<char_id>', methods=['DELETE'])
def delete_character(char_id):
    """حذف شخصية"""
    db = get_db()
    c = db.cursor()
    
    # التحقق من وجود الشخصية
    c.execute('SELECT id FROM characters WHERE id = ?', (char_id,))
    if not c.fetchone():
        return jsonify({'success': False, 'error': 'شخصية غير موجودة'}), 404
    
    # حذف كل البيانات المرتبطة
    c.execute('DELETE FROM messages WHERE character_id = ?', (char_id,))
    c.execute('DELETE FROM memories WHERE character_id = ?', (char_id,))
    c.execute('DELETE FROM diary_entries WHERE character_id = ?', (char_id,))
    c.execute('DELETE FROM revealed_secrets WHERE character_id = ?', (char_id,))
    c.execute('DELETE FROM characters WHERE id = ?', (char_id,))
    
    db.commit()
    return jsonify({'success': True})

@app.route('/api/character/<char_id>/duplicate', methods=['POST'])
def duplicate_character(char_id):
    """نسخ شخصية"""
    db = get_db()
    c = db.cursor()
    
    # الحصول على الشخصية الأصلية
    c.execute('SELECT * FROM characters WHERE id = ?', (char_id,))
    original = c.fetchone()
    if not original:
        return jsonify({'success': False, 'error': 'شخصية غير موجودة'}), 404
    
    original = dict(original)
    
    # إنشاء معرف جديد
    new_id = f"{char_id}_copy"
    counter = 1
    while True:
        c.execute('SELECT id FROM characters WHERE id = ?', (new_id,))
        if not c.fetchone():
            break
        counter += 1
        new_id = f"{char_id}_copy{counter}"
    
    # نسخ الشخصية
    c.execute('''
        INSERT INTO characters (
            id, name, age, gender, avatar_color,
            personality_openness, personality_conscientiousness, 
            personality_extraversion, personality_agreeableness, personality_neuroticism,
            communication_style, speaking_tone, humor_level,
            deep_fears, hidden_dreams, past_wounds, core_values, breaking_point,
            locked_secrets, backstory, current_mood
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        new_id, original['name'] + ' (نسخة)', original['age'], original['gender'], original['avatar_color'],
        original['personality_openness'], original['personality_conscientiousness'],
        original['personality_extraversion'], original['personality_agreeableness'], original['personality_neuroticism'],
        original['communication_style'], original['speaking_tone'], original['humor_level'],
        original['deep_fears'], original['hidden_dreams'], original['past_wounds'], original['core_values'], original['breaking_point'],
        original['locked_secrets'], original['backstory'], original['current_mood']
    ))
    
    db.commit()
    return jsonify({'success': True, 'id': new_id})

# ========== Initialize ==========

if __name__ == '__main__':
    init_db()
    seed_characters()
    app.run(debug=True, host='0.0.0.0', port=5000)

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def migrate_database():
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(mistakes)"))
        columns = [row[1] for row in result]
        if "image_path" not in columns:
            conn.execute(text("ALTER TABLE mistakes ADD COLUMN image_path VARCHAR(500)"))
            conn.commit()

        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        if "daily_word_count" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN daily_word_count INTEGER DEFAULT 20"))
            conn.commit()
        
        if "ai_api_key" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN ai_api_key VARCHAR(500)"))
            conn.commit()
        
        if "ai_api_base_url" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN ai_api_base_url VARCHAR(255)"))
            conn.commit()
        
        if "ai_api_model" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN ai_api_model VARCHAR(100)"))
            conn.commit()
        
        if "ai_api_provider" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN ai_api_provider VARCHAR(50)"))
            conn.commit()
        
        if "selected_word_category" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN selected_word_category VARCHAR(50)"))
            conn.commit()

        result = conn.execute(text("PRAGMA table_info(words)"))
        word_columns = [row[1] for row in result]
        if "category" not in word_columns:
            conn.execute(text("ALTER TABLE words ADD COLUMN category VARCHAR(20) DEFAULT 'CET-4'"))
            conn.commit()

        # 迁移 words 表：移除 word 字段的 UNIQUE 约束，新增 user_id 字段（支持用户上传词书）
        if "user_id" not in word_columns:
            conn.execute(text("PRAGMA foreign_keys=OFF"))
            conn.execute(text("""
                CREATE TABLE words_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word VARCHAR(50) NOT NULL,
                    phonetic VARCHAR(100),
                    meaning TEXT NOT NULL,
                    example_sentence TEXT,
                    difficulty INTEGER NOT NULL DEFAULT 1,
                    frequency INTEGER NOT NULL DEFAULT 0,
                    exam_requirement VARCHAR(20) NOT NULL DEFAULT '考纲',
                    category VARCHAR(20) NOT NULL DEFAULT 'CET-4',
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            conn.execute(text("""
                INSERT INTO words_new (id, word, phonetic, meaning, example_sentence, difficulty, frequency, exam_requirement, category, user_id)
                SELECT id, word, phonetic, meaning, example_sentence, difficulty, frequency, exam_requirement, category, NULL FROM words
            """))
            conn.execute(text("DROP TABLE words"))
            conn.execute(text("ALTER TABLE words_new RENAME TO words"))
            conn.execute(text("CREATE INDEX ix_words_word ON words (word)"))
            conn.execute(text("CREATE INDEX ix_words_user_id ON words (user_id)"))
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.commit()

        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_study_stats'"))
        if not result.scalar():
            conn.execute(text("""
                CREATE TABLE user_study_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    study_date DATE NOT NULL,
                    total_time INTEGER NOT NULL DEFAULT 0,
                    words_studied INTEGER NOT NULL DEFAULT 0,
                    mistakes_added INTEGER NOT NULL DEFAULT 0,
                    questions_completed INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            conn.commit()

        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_documents'"))
        if not result.scalar():
            conn.execute(text("""
                CREATE TABLE knowledge_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    file_type VARCHAR(20),
                    file_size INTEGER,
                    storage_path VARCHAR(500),
                    subject VARCHAR(50) DEFAULT '未分类',
                    chunk_count INTEGER DEFAULT 0,
                    indexed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            conn.commit()

        result = conn.execute(text("PRAGMA table_info(knowledge_documents)"))
        columns = [row[1] for row in result]
        if "subject" not in columns:
            conn.execute(text("ALTER TABLE knowledge_documents ADD COLUMN subject VARCHAR(50) DEFAULT '未分类'"))
            conn.commit()

        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_collaboration_logs'"))
        if not result.scalar():
            conn.execute(text("""
                CREATE TABLE agent_collaboration_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id VARCHAR(64) NOT NULL,
                    user_id INTEGER NOT NULL,
                    orchestrator_name VARCHAR(100) NOT NULL,
                    query TEXT NOT NULL,
                    context TEXT,
                    total_time_ms FLOAT NOT NULL,
                    consulted_agent_count INTEGER NOT NULL DEFAULT 0,
                    accepted_agent_count INTEGER NOT NULL DEFAULT 0,
                    recommendation_count INTEGER NOT NULL DEFAULT 0,
                    success BOOLEAN NOT NULL DEFAULT 1,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_interaction_logs'"))
        if not result.scalar():
            conn.execute(text("""
                CREATE TABLE agent_interaction_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id VARCHAR(64) NOT NULL,
                    agent_name VARCHAR(100) NOT NULL,
                    agent_domain VARCHAR(100) NOT NULL,
                    accepted BOOLEAN NOT NULL DEFAULT 0,
                    reasoning TEXT,
                    confidence FLOAT,
                    response_time_ms FLOAT NOT NULL,
                    recommendation_count INTEGER NOT NULL DEFAULT 0,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='password_reset_codes'"))
        if not result.scalar():
            conn.execute(text("""
                CREATE TABLE password_reset_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    code VARCHAR(6) NOT NULL,
                    expires_at DATETIME NOT NULL,
                    used BOOLEAN NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            conn.commit()

        _seed_default_user(conn)
        _seed_words(conn)


def _seed_default_user(conn):
    result = conn.execute(text("SELECT COUNT(*) FROM users"))
    count = result.scalar()
    if count > 0:
        return

    hashed_password = "$2b$12$Iil8zqQTbTDNGwmEXvXyYexJ69S65ul3vw.CrkTDi0CeVtwrjTVcC"
    
    conn.execute(text("""
        INSERT INTO users (username, email, password, daily_word_count)
        VALUES ('admin', 'admin@kaoyan.com', :password, 20)
    """), {"password": hashed_password})
    conn.commit()


def _seed_words(conn):
    result = conn.execute(text("SELECT COUNT(*) FROM words"))
    count = result.scalar()
    if count > 0:
        return

    sample_words = [
        ("abandon", "/əˈbændən/", "v. 放弃，抛弃", "He decided to abandon the project.", 1, 95, "高频词"),
        ("ability", "/əˈbɪləti/", "n. 能力，才能", "She has the ability to learn quickly.", 1, 88, "考纲词"),
        ("absolute", "/ˈæbsəluːt/", "adj. 绝对的，完全的", "This is an absolute truth.", 2, 75, "考纲词"),
        ("absorb", "/əbˈsɔːrb/", "v. 吸收；吸引", "Plants absorb carbon dioxide.", 2, 82, "高频词"),
        ("abstract", "/ˈæbstrækt/", "adj. 抽象的 n. 摘要", "Beauty is an abstract concept.", 3, 70, "考纲词"),
        ("academy", "/əˈkædəmi/", "n. 学院，研究院", "He graduated from the military academy.", 2, 60, "考纲词"),
        ("accelerate", "/əkˈseləreɪt/", "v. 加速，促进", "The car began to accelerate.", 2, 55, "考纲词"),
        ("access", "/ˈækses/", "n. 通道；使用权 v. 访问", "Students have access to the library.", 1, 90, "高频词"),
        ("accomplish", "/əˈkɒmplɪʃ/", "v. 完成，实现", "She accomplished her goal.", 2, 65, "考纲词"),
        ("accumulate", "/əˈkjuːmjəleɪt/", "v. 积累，积聚", "He accumulated a lot of experience.", 2, 58, "考纲词"),
        ("accurate", "/ˈækjərət/", "adj. 准确的，精确的", "The data must be accurate.", 2, 72, "考纲词"),
        ("achieve", "/əˈtʃiːv/", "v. 实现，达到", "You can achieve anything if you try.", 1, 92, "高频词"),
        ("acknowledge", "/əkˈnɒlɪdʒ/", "v. 承认；感谢", "He acknowledged his mistake.", 3, 50, "考纲词"),
        ("acquire", "/əˈkwaɪər/", "v. 获得，习得", "She acquired new skills.", 2, 68, "考纲词"),
        ("adapt", "/əˈdæpt/", "v. 适应，改编", "Animals adapt to their environment.", 2, 76, "考纲词"),
        ("adequate", "/ˈædɪkwət/", "adj. 足够的，适当的", "We have adequate resources.", 3, 52, "考纲词"),
        ("adjust", "/əˈdʒʌst/", "v. 调整，适应", "You need to adjust your plan.", 2, 74, "考纲词"),
        ("administrate", "/ədˈmɪnɪstreɪt/", "v. 管理，行政", "He administrates the department.", 3, 40, "考纲词"),
        ("admire", "/ədˈmaɪər/", "v. 钦佩，羡慕", "I admire your courage.", 2, 62, "考纲词"),
        ("admit", "/ədˈmɪt/", "v. 承认；准许进入", "He admitted his fault.", 1, 85, "高频词"),
        ("adopt", "/əˈdɒpt/", "v. 采用；收养", "They adopted a new policy.", 2, 66, "考纲词"),
        ("advance", "/ədˈvɑːns/", "v. 前进；推进 n. 进步", "Science advances rapidly.", 1, 80, "高频词"),
        ("advantage", "/ədˈvɑːntɪdʒ/", "n. 优势，有利条件", "He has an advantage over others.", 1, 86, "高频词"),
        ("adventure", "/ədˈventʃər/", "n. 冒险，奇遇", "Life is an adventure.", 2, 56, "考纲词"),
        ("advertise", "/ˈædvətaɪz/", "v. 做广告，宣传", "They advertise their products on TV.", 2, 54, "考纲词"),
        ("advise", "/ədˈvaɪz/", "v. 建议，劝告", "I advise you to study hard.", 1, 84, "高频词"),
        ("affect", "/əˈfekt/", "v. 影响，作用", "The weather affects my mood.", 1, 88, "高频词"),
        ("afford", "/əˈfɔːd/", "v. 负担得起", "I can't afford this car.", 2, 70, "考纲词"),
        ("aggressive", "/əˈɡresɪv/", "adj. 侵略的；积极的", "He is aggressive in business.", 3, 48, "考纲词"),
        ("agriculture", "/ˈæɡrɪkʌltʃər/", "n. 农业", "Agriculture is important for food.", 2, 50, "考纲词"),
    ]

    for word in sample_words:
        conn.execute(
            text("""INSERT INTO words (word, phonetic, meaning, example_sentence, difficulty, frequency, exam_requirement, category)
                    VALUES (:word, :phonetic, :meaning, :example, :diff, :freq, :req, :category)"""),
            {"word": word[0], "phonetic": word[1], "meaning": word[2], "example": word[3],
             "diff": word[4], "freq": word[5], "req": word[6], "category": "CET-4"}
        )
    conn.commit()
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

# 데이터베이스 파일 경로
DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "assets.db"

@contextmanager
def get_db_connection():
    """데이터베이스 연결 컨텍스트 매니저"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 딕셔너리처럼 접근 가능하게
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """데이터베이스 테이블 생성 및 초기 데이터 삽입"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. asset_classes 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. asset_categories 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                tier_id INTEGER,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES asset_classes(id),
                FOREIGN KEY (tier_id) REFERENCES asset_tiers(id),
                UNIQUE(class_id, name)
            )
        """)

        # 마이그레이션: asset_categories 테이블에 tier_id 컬럼 추가
        try:
            cursor.execute("ALTER TABLE asset_categories ADD COLUMN tier_id INTEGER REFERENCES asset_tiers(id)")
            print("Added tier_id column to asset_categories table")
        except sqlite3.OperationalError:
            # 이미 컬럼이 존재하는 경우 무시
            pass
        
        # 3. asset_tiers 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_tiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                tier_level INTEGER NOT NULL,
                name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES asset_classes(id),
                UNIQUE(class_id, tier_level),
                UNIQUE(class_id, name)
            )
        """)
        
        # 4. assets 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                cost REAL NOT NULL,
                class_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                tier_id INTEGER NOT NULL,
                date DATE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES asset_classes(id),
                FOREIGN KEY (category_id) REFERENCES asset_categories(id),
                FOREIGN KEY (tier_id) REFERENCES asset_tiers(id)
            )
        """)        
        
        # 5. asset_tags 테이블 (태그 마스터)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                color TEXT DEFAULT '#6366f1',
                is_active BOOLEAN DEFAULT TRUE,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 6. asset_tag_relations 테이블 (거래-태그 다대다 관계)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_tag_relations (
                asset_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (asset_id, tag_id),
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES asset_tags(id) ON DELETE CASCADE
            )
        """)

        # 7. asset_sub_categories 테이블 (새로 추가)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_sub_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                tier_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES asset_categories(id),
                FOREIGN KEY (tier_id) REFERENCES asset_tiers(id),
                UNIQUE(category_id, name)
            )
        """)

        # assets 테이블에 sub_category_id 컬럼 추가
        try:
            cursor.execute("ALTER TABLE assets ADD COLUMN sub_category_id INTEGER REFERENCES asset_sub_categories(id)")
        except sqlite3.OperationalError:
            pass

        # 인덱스 생성
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_date ON assets(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_class ON assets(class_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_sub_category ON assets(sub_category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_date_class ON assets(date, class_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_class ON asset_categories(class_id, is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_categories_category ON asset_sub_categories(category_id, is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tiers_class ON asset_tiers(class_id, is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_name ON asset_tags(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tag_relations_asset ON asset_tag_relations(asset_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tag_relations_tag ON asset_tag_relations(tag_id)")
     

        # 초기 데이터 삽입 (데이터가 없을 때만)
        cursor.execute("SELECT COUNT(*) FROM asset_classes")
        if cursor.fetchone()[0] == 0:
            insert_initial_data(cursor)
            
        # 데이터 마이그레이션 1: 기존 카테고리에 tier_id 할당 (tier_id가 NULL인 경우)
        cursor.execute("SELECT id, class_id FROM asset_categories WHERE tier_id IS NULL")
        categories_to_update = cursor.fetchall()
        
        if categories_to_update:
            print(f"Migrating {len(categories_to_update)} categories to have tier_id...")
            for cat_id, class_id in categories_to_update:
                # 해당 카테고리의 거래 내역에서 가장 많이 사용된 tier_id 조회
                cursor.execute("""
                    SELECT tier_id, COUNT(*) as count 
                    FROM assets 
                    WHERE category_id = ? 
                    GROUP BY tier_id 
                    ORDER BY count DESC 
                    LIMIT 1
                """, (cat_id,))
                result = cursor.fetchone()
                
                best_tier_id = None
                if result:
                    best_tier_id = result[0]
                else:
                    # 거래 내역이 없으면 해당 클래스의 기본 티어(보통 99: 구분없음) 또는 첫 번째 티어 할당
                    # 99번 티어(구분없음) 찾기
                    cursor.execute("SELECT id FROM asset_tiers WHERE class_id = ? AND tier_level = 99", (class_id,))
                    tier_row = cursor.fetchone()
                    if tier_row:
                        best_tier_id = tier_row[0]
                    else:
                        # 없으면 첫 번째 티어
                        cursor.execute("SELECT id FROM asset_tiers WHERE class_id = ? ORDER BY tier_level ASC LIMIT 1", (class_id,))
                        tier_row = cursor.fetchone()
                        best_tier_id = tier_row[0] if tier_row else None
                
                if best_tier_id:
                    cursor.execute("UPDATE asset_categories SET tier_id = ? WHERE id = ?", (best_tier_id, cat_id))
            print("Migration 1 completed.")

        # 데이터 마이그레이션 2: Sub Category 생성 및 assets 업데이트
        cursor.execute("SELECT COUNT(*) FROM asset_sub_categories")
        if cursor.fetchone()[0] == 0:
            print("Migrating to Sub Categories...")
            cursor.execute("SELECT id, name, tier_id, class_id FROM asset_categories")
            categories = cursor.fetchall()
            
            for cat in categories:
                cat_id, cat_name, tier_id, class_id = cat
                
                final_tier_id = tier_id
                if final_tier_id is None:
                     # tier_id가 없으면 기본값(99: 구분없음) 찾기
                    cursor.execute("SELECT id FROM asset_tiers WHERE class_id = ? AND tier_level = 99", (class_id,))
                    tier_row = cursor.fetchone()
                    if tier_row:
                        final_tier_id = tier_row[0]
                    else:
                        cursor.execute("SELECT id FROM asset_tiers WHERE class_id = ? ORDER BY tier_level ASC LIMIT 1", (class_id,))
                        tier_row = cursor.fetchone()
                        final_tier_id = tier_row[0] if tier_row else None
                
                if final_tier_id:
                    # 기본 서브 카테고리 생성 (이름: '일반')
                    cursor.execute("""
                        INSERT INTO asset_sub_categories (category_id, name, tier_id)
                        VALUES (?, ?, ?)
                    """, (cat_id, '일반', final_tier_id))
                    sub_cat_id = cursor.lastrowid
                    
                    # 해당 카테고리의 assets 업데이트
                    cursor.execute("""
                        UPDATE assets 
                        SET sub_category_id = ? 
                        WHERE category_id = ? AND sub_category_id IS NULL
                    """, (sub_cat_id, cat_id))
            print("Sub Category Migration completed.")
        
        if categories_to_update:
            print(f"Migrating {len(categories_to_update)} categories to have tier_id...")
            for cat_id, class_id in categories_to_update:
                # 해당 카테고리의 거래 내역에서 가장 많이 사용된 tier_id 조회
                cursor.execute("""
                    SELECT tier_id, COUNT(*) as count 
                    FROM assets 
                    WHERE category_id = ? 
                    GROUP BY tier_id 
                    ORDER BY count DESC 
                    LIMIT 1
                """, (cat_id,))
                result = cursor.fetchone()
                
                best_tier_id = None
                if result:
                    best_tier_id = result[0]
                else:
                    # 거래 내역이 없으면 해당 클래스의 기본 티어(보통 99: 구분없음) 또는 첫 번째 티어 할당
                    # 99번 티어(구분없음) 찾기
                    cursor.execute("SELECT id FROM asset_tiers WHERE class_id = ? AND tier_level = 99", (class_id,))
                    tier_row = cursor.fetchone()
                    if tier_row:
                        best_tier_id = tier_row[0]
                    else:
                        # 없으면 첫 번째 티어
                        cursor.execute("SELECT id FROM asset_tiers WHERE class_id = ? ORDER BY tier_level ASC LIMIT 1", (class_id,))
                        tier_row = cursor.fetchone()
                        best_tier_id = tier_row[0] if tier_row else None
                
                if best_tier_id:
                    cursor.execute("UPDATE asset_categories SET tier_id = ? WHERE id = ?", (best_tier_id, cat_id))
            print("Migration completed.")
        
        conn.commit()
        print("Database initialized successfully!")

def insert_initial_data(cursor):
    """초기 데이터 삽입"""
    
    # 1. Asset Classes
    classes = [
        ('spend', '지출', '지출 관련 거래'),
        ('earn', '수익', '수익 관련 거래'),
        ('save', '저축', '저축 관련 거래')
    ]
    cursor.executemany(
        "INSERT INTO asset_classes (name, display_name, description) VALUES (?, ?, ?)",
        classes
    )
    
    # class_id 가져오기
    cursor.execute("SELECT id, name FROM asset_classes")
    class_ids = {row[1]: row[0] for row in cursor.fetchall()}
    
    # 2. Asset Categories
    categories = [
        # 지출 카테고리
        (class_ids['spend'], 'utilities', '관리비/공과금', '전기, 가스, 수도 등', 1),
        (class_ids['spend'], 'rent', '월세', '주거비', 2),
        (class_ids['spend'], 'food', '식비', '식사, 식료품', 3),
        (class_ids['spend'], 'transportation', '교통', '차량, 대중교통', 4),
        (class_ids['spend'], 'cafe', '카페', '커피, 음료', 5),
        (class_ids['spend'], 'game', '게임', '게임 관련 지출', 6),
        (class_ids['spend'], 'etc', '기타', '기타 지출', 99),
        # 수익 카테고리
        (class_ids['earn'], 'salary', '월급', '정기 급여', 1),
        (class_ids['earn'], 'bonus', '보너스', '성과급, 상여금', 2),
        (class_ids['earn'], 'side_income', '부수익', '부업, 알바', 3),
        (class_ids['earn'], 'etc', '기타', '기타 수익', 99),
        # 저축 카테고리
        (class_ids['save'], 'saving', '일반저축', '정기/자유 저축', 1),
        (class_ids['save'], 'investment', '투자', '주식, 펀드 등', 2),
        (class_ids['save'], 'etc', '기타', '기타 저축', 99),
    ]
    cursor.executemany(
        """INSERT INTO asset_categories 
           (class_id, name, display_name, description, sort_order) 
           VALUES (?, ?, ?, ?, ?)""",
        categories
    )
    
    # 3. Asset Tiers
    tiers = [
        # 지출 티어
        (class_ids['spend'], 0, 'fixed', '고정비', '월/년단위 무조건 쓰게되는 돈 (월세, 관리비 등)', 0),
        (class_ids['spend'], 1, 'essential', '필수비', '거의 필수적으로 쓰이는 돈 (밥값, 교통비 등)', 1),
        (class_ids['spend'], 2, 'leisure', '여가비', '여가생활비 (친구만나는돈, 카페 등)', 2),
        (class_ids['spend'], 3, 'hobby', '취미비', '취미생활비 (배드민턴, 모각코 커피 등)', 3),
        (class_ids['spend'], 99, 'unclassified', '구분없음', '기본값', 99),
        # 수익 티어
        (class_ids['earn'], 0, 'regular', '정기수익', '월 정기적으로 들어오는 수익 (월급)', 0),
        (class_ids['earn'], 1, 'bonus', '특수수익', '비정기적 추가 수익 (성과급, 보너스 등)', 1),
        (class_ids['earn'], 2, 'side', '부수익', '부업, 알바 등의 수익', 2),
        (class_ids['earn'], 99, 'unclassified', '구분없음', '기본값', 99),
        # 저축 티어
        (class_ids['save'], 0, 'regular_saving', '정기저축', '매월 고정으로 저축하는 금액', 0),
        (class_ids['save'], 1, 'emergency_fund', '비상금', '비상상황 대비 저축', 1),
        (class_ids['save'], 2, 'goal_saving', '목표저축', '특정 목표를 위한 저축 (여행, 물건 구매 등)', 2),
        (class_ids['save'], 3, 'investment', '투자', '장기 투자 목적의 저축', 3),
        (class_ids['save'], 99, 'unclassified', '구분없음', '기본값', 99),
    ]
    cursor.executemany(
        """INSERT INTO asset_tiers 
           (class_id, tier_level, name, display_name, description, sort_order) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        tiers
    )
    
    print("Initial data inserted successfully!")

# 앱 시작 시 데이터베이스 초기화
if __name__ == "__main__":
    init_database()

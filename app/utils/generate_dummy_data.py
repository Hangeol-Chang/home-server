"""
더미 데이터 생성 스크립트
2025년 9월 ~ 11월까지 3개월치 거래 데이터 생성
"""
import random
from datetime import datetime, timedelta
from database import get_db_connection, init_database

# 더미 데이터 설정
START_DATE = datetime(2025, 9, 1)
END_DATE = datetime(2025, 11, 30)

# 태그 데이터
TAGS = [
    ('데이트', '연인과의 데이트 지출', '#ff69b4'),
    ('차량', '차량 관련 지출', '#4169e1'),
    ('카페', '카페/커피 지출', '#8b4513'),
    ('외식', '외식/식당 지출', '#ff8c00'),
    ('장보기', '식료품/마트 지출', '#32cd32'),
    ('회식', '직장 회식', '#9370db'),
    ('친구', '친구와의 모임', '#20b2aa'),
    ('취미', '취미 활동', '#ff6347'),
    ('운동', '운동/헬스', '#228b22'),
    ('게임', '게임 관련', '#9932cc'),
    ('쇼핑', '쇼핑/구매', '#ff1493'),
    ('건강', '병원/약국', '#dc143c'),
    ('교육', '교육/학습', '#4682b4'),
    ('구독', '구독 서비스', '#daa520'),
]

# 지출 거래 템플릿
SPEND_TEMPLATES = [
    # 고정비 (tier_level=0)
    {
        'category': 'utilities',
        'tier_level': 0,
        'items': [
            ('전기요금', 50000, 80000, ['관리비'], None),
            ('가스요금', 30000, 60000, ['관리비'], None),
            ('수도요금', 20000, 35000, ['관리비'], None),
            ('인터넷/통신비', 40000, 60000, ['구독'], None),
        ],
        'frequency': 'monthly'  # 매월 1회
    },
    {
        'category': 'rent',
        'tier_level': 0,
        'items': [
            ('월세', 500000, 700000, [], None),
        ],
        'frequency': 'monthly'
    },
    # 필수비 (tier_level=1)
    {
        'category': 'food',
        'tier_level': 1,
        'items': [
            ('아침식사', 5000, 8000, ['외식'], None),
            ('점심식사', 8000, 12000, ['외식'], None),
            ('저녁식사', 10000, 15000, ['외식'], None),
            ('편의점', 3000, 8000, [], None),
            ('마트 장보기', 30000, 80000, ['장보기'], None),
        ],
        'frequency': 'daily'  # 매일 1-3회
    },
    {
        'category': 'transportation',
        'tier_level': 1,
        'items': [
            ('주유', 60000, 90000, ['차량'], None),
            ('지하철', 1500, 1500, [], None),
            ('버스', 1500, 1500, [], None),
            ('택시', 8000, 25000, [], None),
            ('주차비', 3000, 10000, ['차량'], None),
        ],
        'frequency': 'frequent'  # 주 3-5회
    },
    # 여가비 (tier_level=2)
    {
        'category': 'cafe',
        'tier_level': 2,
        'items': [
            ('스타벅스', 5500, 8000, ['카페'], None),
            ('이디야 커피', 3000, 5000, ['카페'], None),
            ('베이커리 카페', 8000, 15000, ['카페', '외식'], None),
            ('디저트 카페', 10000, 20000, ['카페', '데이트'], None),
        ],
        'frequency': 'frequent'
    },
    {
        'category': 'food',
        'tier_level': 2,
        'items': [
            ('맛집 외식', 30000, 60000, ['외식', '데이트'], None),
            ('술집/바', 40000, 80000, ['외식', '친구'], None),
            ('회식', 50000, 100000, ['외식', '회식'], None),
            ('치킨/야식', 20000, 30000, ['외식'], None),
        ],
        'frequency': 'weekly'  # 주 1-2회
    },
    {
        'category': 'etc',
        'tier_level': 2,
        'items': [
            ('영화', 15000, 20000, ['데이트', '취미'], None),
            ('쇼핑', 30000, 150000, ['쇼핑'], None),
            ('노래방', 20000, 30000, ['친구'], None),
        ],
        'frequency': 'occasional'  # 월 2-4회
    },
    # 취미비 (tier_level=3)
    {
        'category': 'game',
        'tier_level': 3,
        'items': [
            ('게임 결제', 10000, 50000, ['게임'], None),
            ('스팀 게임', 20000, 60000, ['게임'], None),
        ],
        'frequency': 'occasional'
    },
    {
        'category': 'etc',
        'tier_level': 3,
        'items': [
            ('배드민턴 용품', 30000, 100000, ['운동', '취미'], None),
            ('헬스장', 70000, 100000, ['운동', '구독'], None),
            ('책/전자책', 10000, 30000, ['교육', '취미'], None),
        ],
        'frequency': 'occasional'
    },
]

# 수익 거래 템플릿
EARN_TEMPLATES = [
    {
        'category': 'salary',
        'tier_level': 0,
        'items': [
            ('월급', 3000000, 3500000, [], '정기 급여'),
        ],
        'frequency': 'monthly'
    },
    {
        'category': 'bonus',
        'tier_level': 1,
        'items': [
            ('성과급', 500000, 1000000, [], '분기별 성과급'),
        ],
        'frequency': 'rare'  # 3개월에 1회 정도
    },
    {
        'category': 'side_income',
        'tier_level': 2,
        'items': [
            ('부업 수입', 100000, 300000, [], '프리랜서 작업'),
            ('중고거래', 50000, 200000, [], '물건 판매'),
        ],
        'frequency': 'occasional'
    },
]

def get_random_date(start_date, end_date):
    """시작일과 종료일 사이의 랜덤한 날짜 반환"""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randint(0, days_between)
    return start_date + timedelta(days=random_days)

def generate_transactions():
    """더미 거래 데이터 생성"""
    print("더미 데이터 생성을 시작합니다...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. 태그 생성
        print("\n1. 태그 생성 중...")
        for name, description, color in TAGS:
            cursor.execute(
                """INSERT OR IGNORE INTO asset_tags (name, description, color) 
                   VALUES (?, ?, ?)""",
                (name, description, color)
            )
        print(f"   ✓ {len(TAGS)}개 태그 생성 완료")
        
        # 태그 ID 매핑
        cursor.execute("SELECT id, name FROM asset_tags")
        tag_id_map = {row[1]: row[0] for row in cursor.fetchall()}
        
        # 2. 클래스, 카테고리, 티어 ID 가져오기
        cursor.execute("SELECT id, name FROM asset_classes")
        class_id_map = {row[1]: row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT id, class_id, name FROM asset_categories")
        category_map = {}
        for row in cursor.fetchall():
            cat_id, cls_id, name = row
            if cls_id not in category_map:
                category_map[cls_id] = {}
            category_map[cls_id][name] = cat_id
        
        cursor.execute("SELECT id, class_id, tier_level FROM asset_tiers")
        tier_map = {}
        for row in cursor.fetchall():
            tier_id, cls_id, tier_level = row
            if cls_id not in tier_map:
                tier_map[cls_id] = {}
            tier_map[cls_id][tier_level] = tier_id
        
        # 3. 지출 거래 생성
        print("\n2. 지출 거래 생성 중...")
        spend_count = 0
        spend_class_id = class_id_map['spend']
        
        current_date = START_DATE
        while current_date <= END_DATE:
            for template in SPEND_TEMPLATES:
                category_name = template['category']
                tier_level = template['tier_level']
                frequency = template['frequency']
                
                category_id = category_map[spend_class_id][category_name]
                tier_id = tier_map[spend_class_id][tier_level]
                
                # 빈도에 따라 생성 개수 결정
                if frequency == 'monthly':
                    # 매월 1회 (월 초)
                    if current_date.day <= 5:
                        for item in template['items']:
                            name, min_cost, max_cost, tags, desc = item
                            cost = random.randint(min_cost, max_cost)
                            date = current_date + timedelta(days=random.randint(0, 5))
                            
                            cursor.execute(
                                """INSERT INTO assets 
                                   (name, cost, class_id, category_id, tier_id, date, description)
                                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                (name, cost, spend_class_id, category_id, tier_id, 
                                 date.strftime('%Y-%m-%d'), desc)
                            )
                            asset_id = cursor.lastrowid
                            
                            # 태그 연결
                            for tag_name in tags:
                                if tag_name in tag_id_map:
                                    cursor.execute(
                                        """INSERT INTO asset_tag_relations (asset_id, tag_id)
                                           VALUES (?, ?)""",
                                        (asset_id, tag_id_map[tag_name])
                                    )
                            spend_count += 1
                
                elif frequency == 'daily':
                    # 매일 1-3회
                    daily_count = random.randint(1, 3)
                    for _ in range(daily_count):
                        item = random.choice(template['items'])
                        name, min_cost, max_cost, tags, desc = item
                        cost = random.randint(min_cost, max_cost)
                        
                        cursor.execute(
                            """INSERT INTO assets 
                               (name, cost, class_id, category_id, tier_id, date, description)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (name, cost, spend_class_id, category_id, tier_id,
                             current_date.strftime('%Y-%m-%d'), desc)
                        )
                        asset_id = cursor.lastrowid
                        
                        for tag_name in tags:
                            if tag_name in tag_id_map:
                                cursor.execute(
                                    """INSERT INTO asset_tag_relations (asset_id, tag_id)
                                       VALUES (?, ?)""",
                                    (asset_id, tag_id_map[tag_name])
                                )
                        spend_count += 1
                
                elif frequency == 'frequent':
                    # 주 3-5회 (확률 60%)
                    if random.random() < 0.6:
                        item = random.choice(template['items'])
                        name, min_cost, max_cost, tags, desc = item
                        cost = random.randint(min_cost, max_cost)
                        
                        cursor.execute(
                            """INSERT INTO assets 
                               (name, cost, class_id, category_id, tier_id, date, description)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (name, cost, spend_class_id, category_id, tier_id,
                             current_date.strftime('%Y-%m-%d'), desc)
                        )
                        asset_id = cursor.lastrowid
                        
                        for tag_name in tags:
                            if tag_name in tag_id_map:
                                cursor.execute(
                                    """INSERT INTO asset_tag_relations (asset_id, tag_id)
                                       VALUES (?, ?)""",
                                    (asset_id, tag_id_map[tag_name])
                                )
                        spend_count += 1
                
                elif frequency == 'weekly':
                    # 주 1-2회 (확률 25%)
                    if random.random() < 0.25:
                        item = random.choice(template['items'])
                        name, min_cost, max_cost, tags, desc = item
                        cost = random.randint(min_cost, max_cost)
                        
                        cursor.execute(
                            """INSERT INTO assets 
                               (name, cost, class_id, category_id, tier_id, date, description)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (name, cost, spend_class_id, category_id, tier_id,
                             current_date.strftime('%Y-%m-%d'), desc)
                        )
                        asset_id = cursor.lastrowid
                        
                        for tag_name in tags:
                            if tag_name in tag_id_map:
                                cursor.execute(
                                    """INSERT INTO asset_tag_relations (asset_id, tag_id)
                                       VALUES (?, ?)""",
                                    (asset_id, tag_id_map[tag_name])
                                )
                        spend_count += 1
                
                elif frequency == 'occasional':
                    # 월 2-4회 (확률 10%)
                    if random.random() < 0.1:
                        item = random.choice(template['items'])
                        name, min_cost, max_cost, tags, desc = item
                        cost = random.randint(min_cost, max_cost)
                        
                        cursor.execute(
                            """INSERT INTO assets 
                               (name, cost, class_id, category_id, tier_id, date, description)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (name, cost, spend_class_id, category_id, tier_id,
                             current_date.strftime('%Y-%m-%d'), desc)
                        )
                        asset_id = cursor.lastrowid
                        
                        for tag_name in tags:
                            if tag_name in tag_id_map:
                                cursor.execute(
                                    """INSERT INTO asset_tag_relations (asset_id, tag_id)
                                       VALUES (?, ?)""",
                                    (asset_id, tag_id_map[tag_name])
                                )
                        spend_count += 1
            
            current_date += timedelta(days=1)
        
        print(f"   ✓ {spend_count}개 지출 거래 생성 완료")
        
        # 4. 수익 거래 생성
        print("\n3. 수익 거래 생성 중...")
        earn_count = 0
        earn_class_id = class_id_map['earn']
        
        current_date = START_DATE
        while current_date <= END_DATE:
            for template in EARN_TEMPLATES:
                category_name = template['category']
                tier_level = template['tier_level']
                frequency = template['frequency']
                
                category_id = category_map[earn_class_id][category_name]
                tier_id = tier_map[earn_class_id][tier_level]
                
                if frequency == 'monthly':
                    # 매월 1회 (25일 전후)
                    if 23 <= current_date.day <= 27:
                        for item in template['items']:
                            name, min_amount, max_amount, tags, desc = item
                            amount = random.randint(min_amount, max_amount)
                            
                            cursor.execute(
                                """INSERT INTO assets 
                                   (name, cost, class_id, category_id, tier_id, date, description)
                                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                (name, amount, earn_class_id, category_id, tier_id,
                                 current_date.strftime('%Y-%m-%d'), desc)
                            )
                            earn_count += 1
                
                elif frequency == 'rare':
                    # 3개월에 1회 (확률 3%)
                    if random.random() < 0.03:
                        item = random.choice(template['items'])
                        name, min_amount, max_amount, tags, desc = item
                        amount = random.randint(min_amount, max_amount)
                        
                        cursor.execute(
                            """INSERT INTO assets 
                               (name, cost, class_id, category_id, tier_id, date, description)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (name, amount, earn_class_id, category_id, tier_id,
                             current_date.strftime('%Y-%m-%d'), desc)
                        )
                        earn_count += 1
                
                elif frequency == 'occasional':
                    # 월 1-2회 (확률 5%)
                    if random.random() < 0.05:
                        item = random.choice(template['items'])
                        name, min_amount, max_amount, tags, desc = item
                        amount = random.randint(min_amount, max_amount)
                        
                        cursor.execute(
                            """INSERT INTO assets 
                               (name, cost, class_id, category_id, tier_id, date, description)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (name, amount, earn_class_id, category_id, tier_id,
                             current_date.strftime('%Y-%m-%d'), desc)
                        )
                        earn_count += 1
            
            current_date += timedelta(days=1)
        
        print(f"   ✓ {earn_count}개 수익 거래 생성 완료")
        
        # 5. 태그 사용 횟수 업데이트
        print("\n4. 태그 사용 횟수 업데이트 중...")
        cursor.execute("""
            UPDATE asset_tags 
            SET usage_count = (
                SELECT COUNT(*) 
                FROM asset_tag_relations 
                WHERE asset_tag_relations.tag_id = asset_tags.id
            )
        """)
        print("   ✓ 태그 사용 횟수 업데이트 완료")
        
        conn.commit()
        
        # 6. 통계 출력
        print("\n" + "="*50)
        print("더미 데이터 생성 완료!")
        print("="*50)
        print(f"기간: {START_DATE.strftime('%Y-%m-%d')} ~ {END_DATE.strftime('%Y-%m-%d')}")
        print(f"총 거래 수: {spend_count + earn_count}건")
        print(f"  - 지출: {spend_count}건")
        print(f"  - 수익: {earn_count}건")
        print(f"태그 수: {len(TAGS)}개")
        print("="*50)
        
        # 월별 통계
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', date) as month,
                asset_classes.name as class,
                COUNT(*) as count,
                SUM(cost) as total
            FROM assets
            JOIN asset_classes ON assets.class_id = asset_classes.id
            WHERE date BETWEEN ? AND ?
            GROUP BY month, class
            ORDER BY month, class
        """, (START_DATE.strftime('%Y-%m-%d'), END_DATE.strftime('%Y-%m-%d')))
        
        print("\n월별 통계:")
        for row in cursor.fetchall():
            month, cls, count, total = row
            cls_name = '지출' if cls == 'spend' else '수익' if cls == 'earn' else cls
            print(f"  {month} - {cls_name}: {count:3d}건, {total:>12,}원")

if __name__ == "__main__":
    # 데이터베이스 초기화 먼저 실행
    init_database()
    
    # 더미 데이터 생성
    generate_transactions()

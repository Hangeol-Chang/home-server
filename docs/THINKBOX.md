# Asset-Manager

## 지출 등록
### Table
- name *
- cost *
- class * : spend 고정
- date *
    - default : 오늘
- category *
    - 관리비/공과금
    - 월세
    - 식비
    - 교통 (차량/버스 다 포함)
    - 카페
    - 게임

- tier *
    - 0 : 월/년단위 무조건 쓰게되는 돈
    - 1 : 거의 필수적으로 쓰이는 돈 | 밥값
    - 2 : 여가생활비 | 친구만나는돈, 카페 등
    - 3 : 취미생활비 | 배드민턴/모각코 커피 등
    - 4 : 

    - 99 : 구분 없음.
    - default : 99

- description
    - 그냥 설명

### 수익
- name *
- cost *
- class * : earn으로 고정
- date *
- category *
    - 월급

- tier *
    - 0 : 월 정기적으로 들어오는거(월급)
    - 1 : 특수 (성과급 등)

- description
    - 설명

### 저축
- name *
- cost *
- class * : save
- date *
- category *
- tier *

- description


### 월 계획잡기 등

### DB 구성

#### 1. assets (자산 거래 메인 테이블)
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- name (TEXT, NOT NULL) : 거래명
- cost (REAL, NOT NULL) : 금액
- class_id (INTEGER, FOREIGN KEY -> asset_classes.id, NOT NULL) : 거래 분류 (지출/수익/저축)
- category_id (INTEGER, FOREIGN KEY -> asset_categories.id, NOT NULL) : 카테고리
- tier_id (INTEGER, FOREIGN KEY -> asset_tiers.id, NOT NULL) : 중요도/필수도
- date (DATE, NOT NULL, DEFAULT CURRENT_DATE) : 거래 날짜
- description (TEXT, NULLABLE) : 설명
- created_at (DATETIME, DEFAULT CURRENT_TIMESTAMP) : 생성 시간
- updated_at (DATETIME, DEFAULT CURRENT_TIMESTAMP) : 수정 시간

#### 2. asset_classes (거래 분류 관리)
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- name (TEXT, NOT NULL, UNIQUE) : 분류명 (예: spend, earn, save)
- display_name (TEXT, NOT NULL) : 표시명 (예: 지출, 수익, 저축)
- description (TEXT, NULLABLE) : 설명
- is_active (BOOLEAN, DEFAULT TRUE) : 활성화 여부
- created_at (DATETIME, DEFAULT CURRENT_TIMESTAMP)

초기 데이터:
- spend (지출)
- earn (수익)
- save (저축)

#### 3. asset_categories (카테고리 관리)
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- class_id (INTEGER, FOREIGN KEY -> asset_classes.id, NOT NULL) : 어느 분류에 속하는지
- name (TEXT, NOT NULL) : 카테고리명
- display_name (TEXT, NOT NULL) : 표시명
- description (TEXT, NULLABLE) : 설명
- is_active (BOOLEAN, DEFAULT TRUE) : 활성화 여부
- sort_order (INTEGER, DEFAULT 0) : 정렬 순서
- created_at (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- UNIQUE(class_id, name) : 같은 분류 내에서 카테고리명 중복 불가

초기 데이터 (지출):
- utilities (관리비/공과금)
- rent (월세)
- food (식비)
- transportation (교통)
- cafe (카페)
- game (게임)

초기 데이터 (수익):
- salary (월급)
- bonus (성과급/보너스)

초기 데이터 (저축):
- saving (일반저축)
- investment (투자)

#### 4. asset_tiers (중요도/필수도 관리)
**각 class(spend/earn/save)별로 완전히 독립적인 tier를 관리합니다.**

- id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- class_id (INTEGER, FOREIGN KEY -> asset_classes.id, NOT NULL) : 어느 분류에 속하는지
- tier_level (INTEGER, NOT NULL) : 티어 레벨 (0, 1, 2, 3, ..., 99)
- name (TEXT, NOT NULL) : 티어명 (내부 식별용)
- display_name (TEXT, NOT NULL) : 표시명 (사용자에게 보여줄 이름)
- description (TEXT, NULLABLE) : 설명
- is_active (BOOLEAN, DEFAULT TRUE) : 활성화 여부
- sort_order (INTEGER, DEFAULT 0) : 정렬 순서 (tier_level과 별도로 표시 순서 조정 가능)
- created_at (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- UNIQUE(class_id, tier_level) : 같은 분류 내에서 티어 레벨 중복 불가
- UNIQUE(class_id, name) : 같은 분류 내에서 티어명 중복 불가

**초기 데이터 (지출 - spend):**
```
class_id=1 (spend), tier_level=0, name='fixed', display_name='고정비', description='월/년단위 무조건 쓰게되는 돈 (월세, 관리비 등)'
class_id=1 (spend), tier_level=1, name='essential', display_name='필수비', description='거의 필수적으로 쓰이는 돈 (밥값, 교통비 등)'
class_id=1 (spend), tier_level=2, name='leisure', display_name='여가비', description='여가생활비 (친구만나는돈, 카페 등)'
class_id=1 (spend), tier_level=3, name='hobby', display_name='취미비', description='취미생활비 (배드민턴, 모각코 커피 등)'
class_id=1 (spend), tier_level=99, name='unclassified', display_name='구분없음', description='기본값'
```

**초기 데이터 (수익 - earn):**
```
class_id=2 (earn), tier_level=0, name='regular', display_name='정기수익', description='월 정기적으로 들어오는 수익 (월급)'
class_id=2 (earn), tier_level=1, name='bonus', display_name='특수수익', description='비정기적 추가 수익 (성과급, 보너스 등)'
class_id=2 (earn), tier_level=2, name='side', display_name='부수익', description='부업, 알바 등의 수익'
class_id=2 (earn), tier_level=99, name='unclassified', display_name='구분없음', description='기본값'
```

**초기 데이터 (저축 - save):**
```
class_id=3 (save), tier_level=0, name='regular_saving', display_name='정기저축', description='매월 고정으로 저축하는 금액'
class_id=3 (save), tier_level=1, name='emergency_fund', display_name='비상금', description='비상상황 대비 저축'
class_id=3 (save), tier_level=2, name='goal_saving', display_name='목표저축', description='특정 목표를 위한 저축 (여행, 물건 구매 등)'
class_id=3 (save), tier_level=3, name='investment', display_name='투자', description='장기 투자 목적의 저축'
class_id=3 (save), tier_level=99, name='unclassified', display_name='구분없음', description='기본값'
```

**💡 Tier 사용 예시:**
- 지출 등록 시 → spend의 tier만 선택 가능 (고정비, 필수비, 여가비, 취미비, 구분없음)
- 수익 등록 시 → earn의 tier만 선택 가능 (정기수익, 특수수익, 부수익, 구분없음)
- 저축 등록 시 → save의 tier만 선택 가능 (정기저축, 비상금, 목표저축, 투자, 구분없음)

**💡 Tier 조회 쿼리 예시:**
```sql
-- 지출용 tier 목록 조회
SELECT * FROM asset_tiers 
WHERE class_id = (SELECT id FROM asset_classes WHERE name = 'spend')
AND is_active = TRUE
ORDER BY sort_order, tier_level;

-- 수익용 tier 목록 조회
SELECT * FROM asset_tiers 
WHERE class_id = (SELECT id FROM asset_classes WHERE name = 'earn')
AND is_active = TRUE
ORDER BY sort_order, tier_level;
```

#### 5. budget_plans (월별 예산 계획) - 선택적
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- year (INTEGER, NOT NULL)
- month (INTEGER, NOT NULL)
- class_id (INTEGER, FOREIGN KEY -> asset_classes.id, NOT NULL)
- category_id (INTEGER, FOREIGN KEY -> asset_categories.id, NULLABLE) : NULL이면 전체
- tier_id (INTEGER, FOREIGN KEY -> asset_tiers.id, NULLABLE) : NULL이면 전체
- planned_amount (REAL, NOT NULL) : 계획 금액
- description (TEXT, NULLABLE)
- created_at (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- updated_at (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- UNIQUE(year, month, class_id, category_id, tier_id)

#### 인덱스 설계
- assets 테이블:
  - INDEX idx_assets_date ON assets(date) : 날짜별 조회 최적화
  - INDEX idx_assets_class ON assets(class_id) : 분류별 조회 최적화
  - INDEX idx_assets_category ON assets(category_id) : 카테고리별 조회 최적화
  - INDEX idx_assets_date_class ON assets(date, class_id) : 날짜+분류 복합 조회 최적화

- asset_categories 테이블:
  - INDEX idx_categories_class ON asset_categories(class_id, is_active) : 활성 카테고리 조회 최적화

- asset_tiers 테이블:
  - INDEX idx_tiers_class ON asset_tiers(class_id, is_active) : 활성 티어 조회 최적화

#### 주요 쿼리 예시

1. 특정 월의 지출 조회:
```sql
SELECT * FROM assets 
WHERE class_id = (SELECT id FROM asset_classes WHERE name = 'spend')
AND strftime('%Y-%m', date) = '2025-10'
ORDER BY date DESC;
```

2. 카테고리별 월간 지출 합계:
```sql
SELECT ac.display_name, SUM(a.cost) as total
FROM assets a
JOIN asset_categories ac ON a.category_id = ac.id
WHERE a.class_id = (SELECT id FROM asset_classes WHERE name = 'spend')
AND strftime('%Y-%m', a.date) = '2025-10'
GROUP BY ac.id
ORDER BY total DESC;
```

3. 티어별 월간 지출 통계:
```sql
SELECT at.display_name, COUNT(*) as count, SUM(a.cost) as total
FROM assets a
JOIN asset_tiers at ON a.tier_id = at.id
WHERE a.class_id = (SELECT id FROM asset_classes WHERE name = 'spend')
AND strftime('%Y-%m', a.date) = '2025-10'
GROUP BY at.id
ORDER BY at.tier_level;
```

# Schdule-Manager

# Nodepad
일기장처럼 매일에 대한 기록이 가능한 페이지.
obsidian에 쓰고있는 git과 연동해서, 글을 옵시디언 앱에서 확인할 수 있게 할 것.
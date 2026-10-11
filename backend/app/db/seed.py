"""首次启动时写入演示数据：测试账号、分类、图书、借阅历史、评论与消息。"""
import random
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.security import hash_password
from ..models import Book, Borrow, Category, Message, Review, User

CATEGORIES = [
    ("文学小说", "中外小说、散文与诗歌"),
    ("科学技术", "计算机、物理与科普读物"),
    ("历史人文", "中外历史与人物传记"),
    ("经济管理", "经济学、管理与投资"),
    ("艺术设计", "艺术史与设计美学"),
    ("少儿读物", "童话与儿童文学"),
]

BOOKS = [
    ("三体", "刘慈欣", "9787536692930", "重庆出版社", "文学小说", "科幻,雨果奖", 4,
     "文化大革命之际，一次秘密的绝密计划意外地与外星文明取得联系，人类历史的进程从此改变。地球文明向宇宙发出的第一声啼鸣，以太阳为中心，以光速向宇宙深处飞驰……"),
    ("活着", "余华", "9787506365437", "作家出版社", "文学小说", "经典,当代文学", 3,
     "地主少爷福贵嗜赌成性，终于赌光了家业一贫如洗。穷困之中福贵因母亲生病前去求医，没想到半路上被国民党部队抓了壮丁……"),
    ("百年孤独", "加西亚·马尔克斯", "9787544253994", "南海出版公司", "文学小说", "外国文学,魔幻现实主义", 3,
     "描写了布恩迪亚家族七代人的传奇故事，以及加勒比海沿岸小镇马孔多的百年兴衰，反映了拉丁美洲一个世纪以来风云变幻的历史。"),
    ("围城", "钱锺书", "9787020127894", "人民文学出版社", "文学小说", "经典,讽刺", 2,
     "围城故事发生于1920到1940年代。主角方鸿渐是中国南方一个乡绅青年，在海外游学数年后返乡，途中的种种经历与婚恋纠葛折射出人生的围城。"),
    ("时间简史", "史蒂芬·霍金", "9787535732309", "湖南科学技术出版社", "科学技术", "物理,科普", 3,
     "讲述关于宇宙本性的最前沿知识，从宇宙大爆炸到黑洞，从量子力学到相对论，是普及宇宙学知识的经典之作。"),
    ("人类简史", "尤瓦尔·赫拉利", "9787508647357", "中信出版社", "历史人文", "历史,科普", 4,
     "十万年前，地球上至少有六种不同的人，但今日，世界舞台为什么只剩下了我们自己？从认知革命、农业革命到科学革命，我们真的了解自己吗？"),
    ("算法导论", "托马斯·科尔曼", "9787111407010", "机械工业出版社", "科学技术", "计算机,算法", 2,
     "全面论述了算法的内容，对每一个算法都给出了清晰的分析与证明，是一本广泛使用的算法教材与参考书。"),
    ("深入理解计算机系统", "兰德尔·E. 布莱恩特", "9787111544937", "机械工业出版社", "科学技术", "计算机,系统", 3,
     "从程序员的视角详细阐述计算机系统的本质概念，展示这些概念如何实实在在地影响应用程序的正确性、性能和实用性。"),
    ("Python编程：从入门到实践", "埃里克·马瑟斯", "9787115428028", "人民邮电出版社", "科学技术", "编程,Python", 5,
     "一本针对所有层次的Python读者而作的Python入门书。全书分两部分：第一部分介绍用Python编程所必须了解的基本概念；第二部分将理论付诸实践。"),
    ("明朝那些事儿", "当年明月", "9787801656087", "中国海关出版社", "历史人文", "历史,通俗说史", 4,
     "对明朝十七帝和其他王公权贵和小人物的命运进行全景展示，尤其对官场政治、战争、帝王心术着墨最多，并加入对当时政治经济制度的评价。"),
    ("万历十五年", "黄仁宇", "9787101052039", "中华书局", "历史人文", "历史,明史", 2,
     "万历十五年，亦即公元1587年，在西欧历史上为西班牙舰队全部出动征英的前一年。当年，在明朝发生了若干为历史学家所易于忽视的事件。"),
    ("穷查理宝典", "彼得·考夫曼", "9787508683326", "中信出版社", "经济管理", "投资,思维模型", 3,
     "完整收录了查理·芒格的个人传记与投资哲学，以及过去二十年来芒格主要的公开演讲和媒体访谈。"),
    ("经济学原理", "曼昆", "9787301256532", "北京大学出版社", "经济管理", "经济,教材", 3,
     "曼昆的《经济学原理》是国内外广受欢迎的经济学经典教材之一。本书主要从供给与需求、企业行为与消费者行为等角度阐述经济学基本原理。"),
    ("艺术的故事", "贡布里希", "9787807463726", "广西美术出版社", "艺术设计", "艺术,美术史", 2,
     "概括地叙述了从最早的洞窟绘画到当今的实验艺术的发展历程，以朴素的语言重新讲述艺术史，阐明艺术史是各种传统不断迂回、不断改变的历史。"),
    ("设计中的设计", "原研哉", "9787208068485", "上海人民出版社", "艺术设计", "设计,美学", 2,
     "原研哉的设计作品展现出来的不仅仅是设计本身，更多的是对设计背后的文化与思考的探究。设计不是一种技能，而是捕捉事物本质的感觉能力与洞察能力。"),
    ("小王子", "安托万·德·圣-埃克苏佩里", "9787020042494", "人民文学出版社", "少儿读物", "童话,经典", 5,
     "小王子是一个超凡脱俗的仙童，他遨游太空的历险记温暖了全世界的读者。在对爱与责任的感悟中，我们每个人都能看见自己的影子。"),
    ("夏洛的网", "E.B.怀特", "9787532761801", "上海译文出版社", "少儿读物", "童话,友谊", 3,
     "在朱克曼家的谷仓里，快乐地生活着一群动物。小猪威尔伯和蜘蛛夏洛建立了真挚的友谊。一个关于友谊与承诺的故事。"),
    ("窗边的小豆豆", "黑柳彻子", "9787544250580", "南海出版公司", "少儿读物", "教育,成长", 4,
     "讲述了作者上小学时的一段真实故事：因淘气被原学校退学后，来到巴学园，在小林校长的爱护和引导下，一般人眼里怪怪的小豆豆逐渐成了一个大家都能接受的孩子。"),
]


def seed_data(db: Session) -> None:
    if (db.query(func.count(User.id)).scalar() or 0) > 0:
        return

    random.seed(42)

    admin = User(
        username="admin", password_hash=hash_password("admin123"),
        nickname="系统管理员", email="admin@library.local", role="admin",
    )
    normal = User(
        username="user", password_hash=hash_password("user123"),
        nickname="书友小读", email="user@library.local", phone="13800000002", role="user",
    )
    vip = User(
        username="vip", password_hash=hash_password("vip123"),
        nickname="尊享读者", email="vip@library.local", phone="13800000003", role="vip",
    )
    db.add_all([admin, normal, vip])
    db.flush()

    categories = {name: Category(name=name, description=desc) for name, desc in CATEGORIES}
    db.add_all(categories.values())
    db.flush()

    books = []
    for title, author, isbn, publisher, cat, tags, copies, desc in BOOKS:
        book = Book(
            title=title, author=author, isbn=isbn, publisher=publisher,
            description=desc, category_id=categories[cat].id, tags=tags,
            total_copies=copies, available_copies=copies,
        )
        books.append(book)
    db.add_all(books)
    db.flush()

    # 过去 6 个月的历史借阅记录（全部已归还），用于仪表盘趋势展示
    now = datetime.now()
    borrows = []
    for _ in range(160):
        days_ago = random.randint(0, 175)
        borrowed_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))
        book = random.choice(books)
        user = random.choice([normal, vip, admin])
        returned_at = borrowed_at + timedelta(days=random.randint(2, 13))
        if returned_at > now:
            returned_at = now - timedelta(hours=random.randint(1, 12))
        borrows.append(Borrow(
            user_id=user.id, book_id=book.id, status="returned",
            borrowed_at=borrowed_at, due_date=borrowed_at + timedelta(days=14),
            returned_at=returned_at,
        ))
    # 少量在借记录：多数为近期借出（未逾期），个别逾期 / 待确认归还
    active_specs = [
        (normal, 8, False, "borrowed"),   # user 在借 2 册（未逾期，额度 5 还可再借）
        (normal, 12, False, "borrowed"),
        (normal, 22, True, "borrowed"),   # user 逾期 1 册
        (normal, 10, False, "returning"), # user 归还待确认 1 册
        (vip, 3, False, "borrowed"),      # vip 在借 3 册
        (vip, 7, False, "returning"),
        (vip, 25, True, "borrowed"),      # vip 逾期 1 册
        (vip, 6, False, "borrowed"),
        (admin, 2, False, "borrowed"),
    ]
    for user, days_ago, overdue, status in active_specs:
        borrowed_at = now - timedelta(days=days_ago, hours=random.randint(0, 12))
        due_days = 2 if overdue else 14
        borrows.append(Borrow(
            user_id=user.id, book_id=random.choice(books).id, status=status,
            borrowed_at=borrowed_at, due_date=borrowed_at + timedelta(days=due_days),
        ))
    db.add_all(borrows)
    db.flush()

    # 在借记录需要扣减对应图书的在馆数量
    active_counts: dict[int, int] = {}
    for b in borrows:
        if b.status != "returned":
            active_counts[b.book_id] = active_counts.get(b.book_id, 0) + 1
    for book in books:
        taken = active_counts.get(book.id, 0)
        book.available_copies = max(0, book.total_copies - min(taken, book.total_copies))

    # 少量演示评论
    reviews = [
        (0, 1, 5, "气势磅礴的科幻史诗，黑暗森林法则令人不寒而栗，强烈推荐！"),
        (0, 2, 5, "读完久久不能平静，人类在宇宙中的位置值得我们深思。"),
        (1, 1, 4, "福贵的一生太苦了，但活着本身就是意义，值得反复阅读。"),
        (1, 3, 5, "平实的文字里藏着巨大的力量，余华最好的作品之一。"),
        (5, 2, 4, "视角宏大又通俗易懂，刷新了我对人类历史的认知。"),
        (8, 1, 5, "Python 入门首选，例子丰富，跟着练完就能上手写项目。"),
        (9, 3, 4, "把明史写得妙趣横生，一口气读完根本停不下来。"),
        (15, 2, 5, "写给大人的童话，每次重读都有新的感动。"),
    ]
    for book_idx, user_id, rating, content in reviews:
        db.add(Review(book_id=books[book_idx].id, user_id=user_id, rating=rating, content=content))

    db.add_all([
        Message(
            title="世界读书日专题活动开启",
            content="4 月 23 日世界读书日，本馆推出「共读一本书」专题活动，借阅指定书目可获双倍积分，欢迎大家参与。",
            created_by=admin.id,
        ),
        Message(
            title="新书上架通知",
            content="本月新到一批科学技术与少儿读物，已在首页同步上架，欢迎前往借阅。每人限借额度不变。",
            created_by=admin.id,
        ),
        Message(
            title="系统维护通知",
            content="本系统将于本周日凌晨 2:00-4:00 进行例行维护，期间可能短暂无法访问，请提前安排借阅与归还。",
            created_by=admin.id,
        ),
    ])
    db.commit()

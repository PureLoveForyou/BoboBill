import random
from datetime import datetime, timedelta
from tinydb import TinyDB
import os

os.makedirs("database", exist_ok=True)
db = TinyDB("database/db.json")
db.truncate()

categories = {
    '餐饮': ['美团外卖', '饿了么', '肯德基', '麦当劳', '星巴克', '瑞幸咖啡', '必胜客', '海底捞', '喜茶', '奈雪的茶', '老乡鸡', '真功夫', '沙县小吃', '黄焖鸡米饭'],
    '交通': ['滴滴出行', '高德打车', '地铁充值', '公交卡充值', '中石化加油', '中石油加油', '停车费', '高速公路', '12306火车票', '携程机票'],
    '购物': ['京东', '淘宝', '拼多多', '天猫超市', '网易严选', '小米商城', '华为商城', '优衣库', 'H&M', '无印良品'],
    '娱乐': ['腾讯视频', '爱奇艺', '优酷', '网易云音乐', 'QQ音乐', 'Steam游戏', '电影票', 'KTV', '网吧充值'],
    '医疗': ['药店购药', '医院挂号', '体检中心', '牙科诊所', '眼镜店'],
    '教育': ['在线课程', '书店购书', '培训班', '考试报名费'],
    '转账': ['微信转账', '支付宝转账', '银行转账'],
    '工资': ['工资收入', '奖金', '年终奖', '绩效奖金'],
    '投资': ['理财收益', '基金分红', '股票收益', '余额宝收益'],
    '其他': ['话费充值', '水电费', '燃气费', '物业费', '快递费']
}

platforms = ['wechat', 'alipay', 'bank']

def generate_bills(count=200):
    bills = []
    base_date = datetime.now()
    
    for i in range(count):
        days_ago = random.randint(0, 90)
        date = (base_date - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        category = random.choice(list(categories.keys()))
        merchant = random.choice(categories[category])
        
        if category in ['工资', '投资']:
            amount = round(random.uniform(1000, 20000), 2)
            bill_type = 'income'
        elif category == '转账':
            if random.random() > 0.5:
                amount = round(random.uniform(100, 5000), 2)
                bill_type = 'income'
            else:
                amount = -round(random.uniform(50, 2000), 2)
                bill_type = 'expense'
        else:
            amount = -round(random.uniform(5, 500), 2)
            bill_type = 'expense'
        
        platform = random.choice(platforms)
        
        bill = {
            'name': merchant,
            'amount': amount,
            'type': bill_type,
            'date': date,
            'category': category,
            'platform': platform,
            'merchant': merchant,
            'note': '',
            'transaction_id': f'mock_{random.randint(100000, 999999)}'
        }
        
        bills.append(bill)
    
    bills.sort(key=lambda x: x['date'], reverse=True)
    return bills

print("正在生成 200 条模拟账单数据...")
bills = generate_bills(200)

for bill in bills:
    db.insert(bill)

income_count = len([b for b in bills if b['amount'] > 0])
expense_count = len([b for b in bills if b['amount'] < 0])
total_income = sum(b['amount'] for b in bills if b['amount'] > 0)
total_expense = sum(abs(b['amount']) for b in bills if b['amount'] < 0)

print(f"\n生成完成！")
print(f"总收入: {income_count} 笔，共 ¥{total_income:.2f}")
print(f"总支出: {expense_count} 笔，共 ¥{total_expense:.2f}")
print(f"结余: ¥{total_income - total_expense:.2f}")

"""Mock data generator for BoboBill development."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from tinydb import TinyDB
from datetime import datetime, timedelta
import random

db = TinyDB("database/db.json")
db.truncate()

categories = ['餐饮', '交通', '购物', '娱乐', '医疗', '教育', '转账', '工资', '投资', '其他']
expense_categories = ['餐饮', '交通', '购物', '娱乐', '医疗', '教育', '其他']
income_categories = ['工资', '投资', '转账']
platforms = ['wechat', 'alipay']

merchants = {
    '餐饮': ['美团外卖', '饿了么', '星巴克', '肯德基', '麦当劳', '海底捞', '瑞幸咖啡', '蜜雪冰城', '喜茶', '便利蜂', '盒马鲜生'],
    '交通': ['滴滴出行', '高德打车', '中国石化', '上海地铁', '12306', '中国国航', '哈啰单车'],
    '购物': ['淘宝', '京东', '拼多多', '天猫超市', '优衣库', '名创优品', '无印良品', '苏宁易购'],
    '娱乐': ['腾讯视频', '网易云音乐', 'Steam', '万达电影', '美团团购', 'Netflix', 'B站大会员'],
    '医疗': ['北京协和医院', '大参林药房', '丁香医生', '平安好医生'],
    '教育': ['得到App', '腾讯课堂', '多邻国', 'Coursera', '极客时间'],
    '转账': ['张三', '李四', '王五', '微信红包'],
    '工资': ['XX科技有限公司', '工资代发'],
    '投资': ['招商银行理财', '天天基金', '余额宝'],
    '其他': ['中国移动', '中国电信', '物业费', '水电费', '顺丰快递'],
}

bills = []
base_date = datetime(2026, 1, 1)

# 6 months of data
for day_offset in range(180):
    date = base_date + timedelta(days=day_offset)
    date_str = date.strftime("%Y-%m-%d")

    # 2-5 expense bills per day
    num_expenses = random.randint(1, 5)
    for _ in range(num_expenses):
        cat = random.choice(expense_categories)
        merchant = random.choice(merchants[cat])
        amount = round(random.uniform(5, 300), 2)
        if cat in ['购物'] and random.random() > 0.6:
            amount = round(random.uniform(100, 2000), 2)
        if cat == '交通' and merchant == '12306':
            amount = round(random.uniform(50, 800), 2)

        bills.append({
            'name': merchant,
            'amount': -amount,
            'type': 'expense',
            'date': date_str,
            'category': cat,
            'platform': random.choice(platforms),
            'merchant': merchant,
            'note': '',
        })

    # Occasional income
    if date.day == 15 or date.day == 28:  # payday
        salary = round(random.uniform(8000, 15000), 2)
        bills.append({
            'name': 'XX科技有限公司',
            'amount': salary,
            'type': 'income',
            'date': date_str,
            'category': '工资',
            'platform': 'alipay',
            'merchant': 'XX科技有限公司',
            'note': '月工资',
        })

    if random.random() > 0.85:
        cat = random.choice(['投资', '转账'])
        merchant = random.choice(merchants[cat])
        amount = round(random.uniform(100, 5000), 2)
        bills.append({
            'name': merchant,
            'amount': amount,
            'type': 'income',
            'date': date_str,
            'category': cat,
            'platform': random.choice(platforms),
            'merchant': merchant,
            'note': '',
        })

# Insert all
for bill in bills:
    db.insert(bill)

print(f"Inserted {len(bills)} bills ({sum(1 for b in bills if b['type']=='expense')} expenses, {sum(1 for b in bills if b['type']=='income')} incomes)")
print(f"Date range: {bills[-1]['date']} ~ {bills[0]['date']}")

import requests
import json

BASE_URL = "http://localhost:8000/api"

# 测试用户登录
def test_login():
    response = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "test",
        "password": "test123"
    })
    if response.status_code == 200:
        return response.json()
    # 如果登录失败，尝试注册
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "username": "test",
        "password": "test123"
    })
    if response.status_code == 200:
        # 再次登录
        response = requests.post(f"{BASE_URL}/auth/login", data={
            "username": "test",
            "password": "test123"
        })
        return response.json()
    return None

# 测试创建猫咪
def test_create_cat(user_id):
    # 测试新品种和毛色
    test_cases = [
        {
            "name": "小白",
            "gender": "female",
            "breed": "英国短毛猫",
            "color": "金渐层",
            "birth_date": "2023-01-15",
            "neutered": False
        },
        {
            "name": "小黑",
            "gender": "male",
            "breed": "布偶猫",
            "color": "海豹重点色",
            "birth_date": "2023-06-20",
            "neutered": True
        },
        {
            "name": "小花",
            "gender": "female",
            "breed": "其他",  # 测试自定义品种
            "color": "其他",  # 测试自定义毛色
            "birth_date": "2024-03-10",
            "neutered": False
        }
    ]
    
    for cat_data in test_cases:
        response = requests.post(f"{BASE_URL}/cats/", params={"user_id": user_id}, json=cat_data)
        print(f"创建猫咪 {cat_data['name']}: {response.status_code}")
        if response.status_code == 200:
            cat = response.json()
            print(f"  品种: {cat.get('breed')}, 毛色: {cat.get('color')}")
        else:
            print(f"  错误: {response.text}")

# 测试获取猫咪列表
def test_get_cats(user_id):
    response = requests.get(f"{BASE_URL}/cats/", params={"user_id": user_id})
    if response.status_code == 200:
        cats = response.json()
        print(f"\n获取猫咪列表: {len(cats)} 只")
        for cat in cats:
            breed = cat.get('breed', '未知')
            color = cat.get('color', '')
            display = f"{breed} · {color}" if color else breed
            print(f"  {cat['name']}: {display}")
    else:
        print(f"获取猫咪列表失败: {response.text}")

if __name__ == "__main__":
    print("=== 测试品种和毛色功能 ===\n")
    
    # 登录
    user = test_login()
    if not user:
        print("登录失败")
        exit(1)
    
    user_id = user.get('id')
    print(f"用户ID: {user_id}\n")
    
    # 测试创建猫咪
    test_create_cat(user_id)
    
    # 测试获取猫咪列表
    test_get_cats(user_id)
    
    print("\n=== 测试完成 ===")

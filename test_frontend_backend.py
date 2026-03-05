"""
测试前后端联动脚本
检查前端页面是否能正常与后端API通信
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000"
API_BASE_URL = f"{BASE_URL}/api"

def test_connection():
    """测试基本连接"""
    print("=" * 60)
    print("测试1: 基本连接测试")
    print("=" * 60)
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"[OK] 前端页面可访问: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("[FAIL] 无法连接到服务器，请确保后端服务器正在运行")
        return False
    except Exception as e:
        print(f"[FAIL] 连接错误: {e}")
        return False

def test_health_check():
    """测试健康检查API"""
    print("\n" + "=" * 60)
    print("测试2: API健康检查")
    print("=" * 60)
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 健康检查成功: {data}")
            return True
        else:
            print(f"[FAIL] 健康检查失败: 状态码 {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] 健康检查错误: {e}")
        return False

def test_cors():
    """测试CORS配置"""
    print("\n" + "=" * 60)
    print("测试3: CORS配置检查")
    print("=" * 60)
    try:
        response = requests.options(f"{API_BASE_URL}/health", timeout=5)
        headers = response.headers
        cors_header = headers.get('Access-Control-Allow-Origin', '未设置')
        print(f"[OK] CORS配置: Access-Control-Allow-Origin = {cors_header}")
        return True
    except Exception as e:
        print(f"[FAIL] CORS检查错误: {e}")
        return False

def test_api_routes():
    """测试所有API路由是否存在"""
    print("\n" + "=" * 60)
    print("测试4: API路由检查")
    print("=" * 60)
    
    routes = [
        ("/api/upload", "POST", "文件上传接口"),
        ("/api/tables", "POST", "获取表格列表接口"),
        ("/api/extract", "POST", "提取表格接口"),
        ("/api/health", "GET", "健康检查接口"),
        ("/api/test-extract-module", "GET", "测试提取模块接口"),
    ]
    
    results = []
    for route, method, desc in routes:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{route}", timeout=3)
            else:
                # 对于POST请求，发送一个空的请求来检查路由是否存在
                response = requests.post(f"{BASE_URL}{route}", 
                                       json={}, 
                                       timeout=3)
            
            # 404表示路由不存在，其他状态码（如400, 405等）表示路由存在但参数错误
            if response.status_code == 404:
                print(f"[FAIL] {desc} ({route}): 路由不存在 (404)")
                results.append(False)
            else:
                print(f"[OK] {desc} ({route}): 路由存在 (状态码: {response.status_code})")
                results.append(True)
        except Exception as e:
            print(f"[FAIL] {desc} ({route}): 错误 - {e}")
            results.append(False)
    
    return all(results)

def test_extract_module():
    """测试提取模块是否可用"""
    print("\n" + "=" * 60)
    print("测试5: 提取模块检查")
    print("=" * 60)
    try:
        response = requests.get(f"{API_BASE_URL}/test-extract-module", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 提取模块测试成功: {data.get('message', 'OK')}")
            return True
        else:
            print(f"[FAIL] 提取模块测试失败: 状态码 {response.status_code}")
            data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            print(f"  错误信息: {data.get('error', '未知错误')}")
            return False
    except Exception as e:
        print(f"[FAIL] 提取模块测试错误: {e}")
        return False

def test_frontend_api_config():
    """检查前端API配置"""
    print("\n" + "=" * 60)
    print("测试6: 前端API配置检查")
    print("=" * 60)
    try:
        with open('frontend/index.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查API_BASE_URL配置
        if 'API_BASE_URL' in content:
            print("[OK] 前端包含API_BASE_URL配置")
        else:
            print("[FAIL] 前端未找到API_BASE_URL配置")
            return False
        
        # 检查API调用（前端使用模板字符串，所以检查API路径部分）
        api_calls = [
            ('/upload', '/api/upload'),
            ('/tables', '/api/tables'),
            ('/extract', '/api/extract'),
            ('/download', '/api/download')
        ]
        
        for api_key, api_full in api_calls:
            # 检查是否包含API路径（可能是 /api/upload 或 ${API_BASE_URL}/upload）
            if api_key in content or api_full in content:
                print(f"[OK] 前端包含 {api_full} 调用")
            else:
                print(f"[FAIL] 前端未找到 {api_full} 调用")
        
        return True
    except Exception as e:
        print(f"[FAIL] 检查前端配置错误: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("前后端联动测试")
    print("=" * 60)
    print(f"后端地址: {BASE_URL}")
    print(f"API地址: {API_BASE_URL}")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("基本连接", test_connection()))
    results.append(("健康检查", test_health_check()))
    results.append(("CORS配置", test_cors()))
    results.append(("API路由", test_api_routes()))
    results.append(("提取模块", test_extract_module()))
    results.append(("前端配置", test_frontend_api_config()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("\n[OK] 所有测试通过！前后端联动正常。")
        return 0
    else:
        print("\n[FAIL] 部分测试失败，请检查上述错误信息。")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


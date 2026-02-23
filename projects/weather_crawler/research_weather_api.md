# wttr.in 天气 API 分析报告

## API 概览

**端点**: `https://wttr.in/{location}?format=j1`  
**示例**: `https://wttr.in/Beijing?format=j1`  
**响应格式**: JSON  
**HTTP 状态**: 200 OK  
**Content-Type**: application/json

---

## 数据结构概览

API 返回的 JSON 包含三个主要部分：

```
{
  "current_condition": [...],    // 当前天气状况（数组，通常只有一个元素）
  "nearest_area": [...],         // 最近区域信息
  "request": [...],              // 请求信息
  "weather": [...]               // 未来天气预报（包含多天数据）
}
```

---

## 关键字段提取

### 1. 当前温度

**JSON 路径**:
- 摄氏度: `current_condition[0].temp_C`
- 华氏度: `current_condition[0].temp_F`
- 体感温度（摄氏）: `current_condition[0].FeelsLikeC`
- 体感温度（华氏）: `current_condition[0].FeelsLikeF`

**示例值**:
```json
{
  "temp_C": "9",
  "temp_F": "48",
  "FeelsLikeC": "5",
  "FeelsLikeF": "42"
}
```

**代码示例**:
```python
current_temp_c = data['current_condition'][0]['temp_C']
current_temp_f = data['current_condition'][0]['temp_F']
feels_like_c = data['current_condition'][0]['FeelsLikeC']
```

---

### 2. 天气状况

**JSON 路径**:
- 天气描述: `current_condition[0].weatherDesc[0].value`
- 天气代码: `current_condition[0].weatherCode`
- 云量: `current_condition[0].cloudcover`

**示例值**:
```json
{
  "weatherDesc": [{"value": "Sunny"}],
  "weatherCode": "113",
  "cloudcover": "0"
}
```

**天气代码说明**:
- `113`: Sunny/Clear（晴朗）
- `116`: Partly Cloudy（多云）
- `122`: Overcast（阴天）
- 更多代码需参考 wttr.in 文档

**代码示例**:
```python
weather_desc = data['current_condition'][0]['weatherDesc'][0]['value']
weather_code = data['current_condition'][0]['weatherCode']
cloud_cover = int(data['current_condition'][0]['cloudcover'])
```

---

### 3. 湿度

**JSON 路径**: `current_condition[0].humidity`

**示例值**: `"7"` (百分比)

**代码示例**:
```python
humidity = int(data['current_condition'][0]['humidity'])
print(f"湿度: {humidity}%")
```

---

### 4. 风速

**JSON 路径**:
- 公里/小时: `current_condition[0].windspeedKmph`
- 英里/小时: `current_condition[0].windspeedMiles`
- 风向（度数）: `current_condition[0].winddirDegree`
- 风向（16方位）: `current_condition[0].winddir16Point`

**示例值**:
```json
{
  "windspeedKmph": "29",
  "windspeedMiles": "18",
  "winddirDegree": "318",
  "winddir16Point": "NW"
}
```

**代码示例**:
```python
wind_speed_kmph = int(data['current_condition'][0]['windspeedKmph'])
wind_direction = data['current_condition'][0]['winddir16Point']
print(f"风速: {wind_speed_kmph} km/h, 风向: {wind_direction}")
```

---

### 5. 降水概率

**注意**: `current_condition` 中没有降水概率字段，但有实际降水量。

**当前降水量 JSON 路径**:
- 毫米: `current_condition[0].precipMM`
- 英寸: `current_condition[0].precipInches`

**未来降水概率 JSON 路径** (在 `weather[].hourly[]` 中):
- 降雨概率: `weather[0].hourly[0].chanceofrain`
- 降雪概率: `weather[0].hourly[0].chanceofsnow`

**示例值**:
```json
// 当前降水
{
  "precipMM": "0.0",
  "precipInches": "0.0"
}

// 未来降水概率（小时级）
{
  "chanceofrain": "0",
  "chanceofsnow": "0"
}
```

**代码示例**:
```python
# 当前降水
current_precip_mm = float(data['current_condition'][0]['precipMM'])

# 未来降水概率（今天第一个小时）
if data['weather']:
    first_hour = data['weather'][0]['hourly'][0]
    rain_chance = int(first_hour['chanceofrain'])
    snow_chance = int(first_hour['chanceofsnow'])
    print(f"降雨概率: {rain_chance}%, 降雪概率: {snow_chance}%")
```

---

## 完整数据提取示例

```python
import requests
import json

def get_weather(city):
    """获取指定城市的天气信息"""
    url = f"https://wttr.in/{city}?format=j1"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 提取当前天气
        current = data['current_condition'][0]
        
        weather_info = {
            '温度': {
                '当前温度(°C)': current['temp_C'],
                '体感温度(°C)': current['FeelsLikeC']
            },
            '天气状况': {
                '描述': current['weatherDesc'][0]['value'],
                '天气代码': current['weatherCode'],
                '云量(%)': current['cloudcover']
            },
            '湿度(%)': current['humidity'],
            '风速': {
                '速度(km/h)': current['windspeedKmph'],
                '风向': current['winddir16Point']
            },
            '降水': {
                '当前降水量(mm)': current['precipMM']
            }
        }
        
        # 提取未来降水概率（今天）
        if data['weather']:
            today = data['weather'][0]
            weather_info['降水概率'] = {
                '降雨概率(%)': today['hourly'][0]['chanceofrain'],
                '降雪概率(%)': today['hourly'][0]['chanceofsnow']
            }
        
        return weather_info
        
    except requests.exceptions.RequestException as e:
        return {'error': f'请求失败: {str(e)}'}
    except (KeyError, IndexError) as e:
        return {'error': f'数据解析失败: {str(e)}'}
    except json.JSONDecodeError:
        return {'error': 'JSON 解析失败'}

# 使用示例
if __name__ == '__main__':
    weather = get_weather('Beijing')
    print(json.dumps(weather, ensure_ascii=False, indent=2))
```

---

## 其他有用字段

### 观测时间
- 本地时间: `current_condition[0].localObsDateTime`
- UTC 时间: `current_condition[0].observation_time`

### 能见度
- 公里: `current_condition[0].visibility`
- 英里: `current_condition[0].visibilityMiles`

### 气压
- 毫巴: `current_condition[0].pressure`
- 英寸: `current_condition[0].pressureInches`

### UV 指数
- `current_condition[0].uvIndex`

### 位置信息
```python
area = data['nearest_area'][0]
location = {
    '城市': area['areaName'][0]['value'],
    '国家': area['country'][0]['value'],
    '纬度': area['latitude'],
    '经度': area['longitude']
}
```

---

## 可能的错误情况

### 1. 网络错误
**情况**: 无法连接到 wttr.in 服务器
```python
except requests.exceptions.ConnectionError:
    print("网络连接失败，请检查网络")
```

### 2. 超时错误
**情况**: 请求超时
```python
except requests.exceptions.Timeout:
    print("请求超时，请稍后重试")
```

### 3. HTTP 错误
**情况**: 服务器返回 4xx 或 5xx 状态码
```python
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("城市名称无效")
    elif e.response.status_code == 500:
        print("服务器内部错误")
```

### 4. 城市名称无效
**情况**: 输入的城市名称不存在或拼写错误
- API 通常会返回最接近的位置，但可能不准确
- 建议验证 `nearest_area` 中的城市名称是否匹配

### 5. JSON 解析错误
**情况**: 返回的不是有效的 JSON
```python
except json.JSONDecodeError:
    print("数据格式错误")
```

### 6. 数据结构变化
**情况**: API 返回的数据结构与预期不符
```python
except (KeyError, IndexError) as e:
    print(f"数据字段缺失: {e}")
```

### 7. 空数据
**情况**: 某些字段可能为空或不存在
```python
# 安全访问
def safe_get(data, *keys, default='N/A'):
    """安全地获取嵌套字典的值"""
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, IndexError, TypeError):
        return default

# 使用示例
temp = safe_get(data, 'current_condition', 0, 'temp_C', default='未知')
```

---

## 错误处理完整示例

```python
import requests
import json
from typing import Dict, Any

def get_weather_safe(city: str) -> Dict[str, Any]:
    """
    安全地获取天气信息，包含完整的错误处理
    """
    url = f"https://wttr.in/{city}?format=j1"
    
    try:
        # 设置超时和重试
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # 解析 JSON
        data = response.json()
        
        # 验证数据结构
        if 'current_condition' not in data or not data['current_condition']:
            return {'error': '数据格式异常：缺少 current_condition'}
        
        current = data['current_condition'][0]
        
        # 提取数据（使用 get 方法提供默认值）
        weather_info = {
            'status': 'success',
            'city': city,
            'data': {
                'temperature_c': current.get('temp_C', 'N/A'),
                'feels_like_c': current.get('FeelsLikeC', 'N/A'),
                'weather': current.get('weatherDesc', [{}])[0].get('value', 'N/A'),
                'humidity': current.get('humidity', 'N/A'),
                'wind_speed_kmph': current.get('windspeedKmph', 'N/A'),
                'wind_direction': current.get('winddir16Point', 'N/A'),
                'precipitation_mm': current.get('precipMM', 'N/A'),
                'observation_time': current.get('localObsDateTime', 'N/A')
            }
        }
        
        return weather_info
        
    except requests.exceptions.Timeout:
        return {'error': '请求超时', 'status': 'timeout'}
    
    except requests.exceptions.ConnectionError:
        return {'error': '网络连接失败', 'status': 'connection_error'}
    
    except requests.exceptions.HTTPError as e:
        return {
            'error': f'HTTP 错误: {e.response.status_code}',
            'status': 'http_error',
            'status_code': e.response.status_code
        }
    
    except json.JSONDecodeError:
        return {'error': 'JSON 解析失败', 'status': 'json_error'}
    
    except Exception as e:
        return {'error': f'未知错误: {str(e)}', 'status': 'unknown_error'}

# 使用示例
result = get_weather_safe('Beijing')
if result.get('status') == 'success':
    print(f"温度: {result['data']['temperature_c']}°C")
else:
    print(f"错误: {result['error']}")
```

---

## API 限制和注意事项

1. **速率限制**: wttr.in 可能有请求频率限制，建议添加缓存机制
2. **城市名称**: 支持中文和英文，但英文更稳定
3. **数据更新频率**: 通常每小时更新一次
4. **免费服务**: 无需 API key，但不保证 SLA
5. **数据类型**: 所有数值都是字符串格式，需要转换

---

## 推荐的数据提取策略

1. **使用 get() 方法**: 避免 KeyError
2. **类型转换**: 将字符串转换为数值时添加异常处理
3. **缓存机制**: 避免频繁请求同一城市
4. **重试逻辑**: 网络失败时自动重试（指数退避）
5. **日志记录**: 记录所有错误和异常情况

---

## 总结

wttr.in API 提供了丰富的天气数据，数据结构清晰，易于解析。关键要点：

- 当前天气在 `current_condition[0]` 中
- 所有数值都是字符串，需要类型转换
- 降水概率在 `weather[].hourly[]` 中，不在当前天气中
- 必须做好错误处理和数据验证
- 建议添加缓存和重试机制

**最佳实践**: 使用 `get()` 方法和默认值，确保代码健壮性。

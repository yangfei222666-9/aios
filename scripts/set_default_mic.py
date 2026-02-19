"""设置 PD200X Podcast Microphone 为默认录音设备"""
import comtypes
from comtypes import GUID, HRESULT
import ctypes
from ctypes import wintypes
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# COM interfaces for IPolicyConfig (undocumented but widely used)
IID_IPolicyConfig = GUID('{f8679f50-850a-41cf-9c72-430f290290c8}')
CLSID_PolicyConfigClient = GUID('{870af99c-171d-4f9e-af0d-e63df40c2bc9}')

class IPolicyConfig(comtypes.IUnknown):
    _iid_ = IID_IPolicyConfig
    _methods_ = [
        comtypes.COMMETHOD([], HRESULT, 'Unused1'),
        comtypes.COMMETHOD([], HRESULT, 'Unused2'),
        comtypes.COMMETHOD([], HRESULT, 'Unused3'),
        comtypes.COMMETHOD([], HRESULT, 'Unused4'),
        comtypes.COMMETHOD([], HRESULT, 'Unused5'),
        comtypes.COMMETHOD([], HRESULT, 'Unused6'),
        comtypes.COMMETHOD([], HRESULT, 'Unused7'),
        comtypes.COMMETHOD([], HRESULT, 'Unused8'),
        comtypes.COMMETHOD([], HRESULT, 'Unused9'),
        comtypes.COMMETHOD([], HRESULT, 'Unused10'),
        comtypes.COMMETHOD([], HRESULT, 'SetDefaultEndpoint',
                          (['in'], ctypes.c_wchar_p, 'wszDeviceId'),
                          (['in'], ctypes.c_uint, 'eRole')),
    ]

# PD200X 麦克风设备 ID (capture endpoint 0.0.1)
PD200X_MIC_ID = r'{0.0.1.00000000}.{5ef772d1-7a95-4368-b8e6-f202e58185ff}'

try:
    comtypes.CoInitialize()
    policy_config = comtypes.CoCreateInstance(
        CLSID_PolicyConfigClient, IPolicyConfig)
    
    # eRole: 0=Console, 1=Multimedia, 2=Communications
    for role in range(3):
        hr = policy_config.SetDefaultEndpoint(PD200X_MIC_ID, role)
        role_name = ['Console', 'Multimedia', 'Communications'][role]
        print(f"  Set {role_name}: {'OK' if hr == 0 else f'FAILED ({hr})'}")
    
    print("\n✅ PD200X 已设为默认录音设备")
except Exception as e:
    print(f"❌ 设置失败: {e}")
finally:
    comtypes.CoUninitialize()

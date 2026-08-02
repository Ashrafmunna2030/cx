import requests
import json
import uuid
import time
import os
import re
from typing import Optional, Dict, Any, Tuple

class GarenaCookieManager:
    """
    Fresh cookie generator for each request.
    """
    BASE_URL = "https://shop.garena.my"
    DATADOME_URL = "https://datadome.garena.com"
    
    USER_AGENTS = [
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; M2101K7AI Build/SKQ1.210908.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.7827.91 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 14; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    ]
    
    def __init__(self):
        self.session = requests.Session()
    
    def _random_ua(self) -> str:
        """Get random user agent"""
        import random
        return random.choice(self.USER_AGENTS)
    
    def _generate_id(self, length: int = 32) -> str:
        """Generate random hex ID"""
        return str(uuid.uuid4()).replace('-', '')[:length]
    
    def _generate_session_key(self) -> str:
        """Generate session key"""
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
        return ''.join([chars[int(os.urandom(1)[0]) % len(chars)] for _ in range(32)])
    
    def fetch_fresh_cookies(self) -> Dict[str, str]:
        """
        Fetch completely fresh cookies by:
        1. Visit main page
        2. Get DataDome challenge
        3. Solve/get DataDome cookie
        4. Return all cookies as dict
        """
        print("🔄 Generating fresh cookies...")
        
        cookies = {}
        ua = self._random_ua()
        
        try:
            # Step 1: Visit main page to get initial cookies
            print("  📡 Step 1: Visiting main page...")
            main_headers = {
                "Host": "shop.garena.my",
                "Connection": "keep-alive",
                "sec-ch-ua-platform": '"Android"',
                "User-Agent": ua,
                "sec-ch-ua": '"Android WebView";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
                "sec-ch-ua-mobile": "?1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "X-Requested-With": "mark.via.gp",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Dest": "document",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            }
            
            resp = self.session.get(
                f"{self.BASE_URL}/?app=100067&channel=202953",
                headers=main_headers,
                timeout=15,
                allow_redirects=True
            )
            
            # Extract cookies from response
            for cookie in self.session.cookies:
                cookies[cookie.name] = cookie.value
            
            print(f"  ✅ Got {len(cookies)} initial cookies")
            
            # Step 2: Set required cookies if missing
            if "source" not in cookies:
                cookies["source"] = "mb"
            if "region" not in cookies:
                cookies["region"] = "MY"  
            if "language" not in cookies:
                cookies["language"] = "en"
            if "mspid2" not in cookies:
                cookies["mspid2"] = self._generate_id()
            if "session_key" not in cookies:
                cookies["session_key"] = self._generate_session_key()
            if "_fbp" not in cookies:
                cookies["_fbp"] = f"fb.1.{int(time.time())}.{self._generate_id(19)}"
            
            # Update session with all cookies
            for key, value in cookies.items():
                self.session.cookies.set(key, value)
            
            # Step 3: Try to get DataDome cookie
            print("  📡 Step 2: Fetching DataDome cookie...")
            datadome = self._fetch_datadome_cookie(ua)
            if datadome:
                cookies["datadome"] = datadome
                self.session.cookies.set("datadome", datadome, domain=".garena.my")
                print("  ✅ DataDome cookie acquired")
            else:
                print("  ⚠️ DataDome cookie failed, using fallback")
            
            # Step 4: Track event (optional but helps)
            print("  📡 Step 3: Sending track event...")
            self._send_track_event(cookies.get("mspid2", ""), ua)
            print("  ✅ Track event sent")
            
            print(f"✅ Total {len(cookies)} cookies generated")
            return cookies
            
        except Exception as e:
            print(f"⚠️ Cookie fetch error: {e}")
            # Return basic cookies even on error
            fallback = {
                "source": "mb",
                "region": "MY",
                "language": "en",
                "mspid2": self._generate_id(),
                "session_key": self._generate_session_key(),
                "_fbp": f"fb.1.{int(time.time())}.{self._generate_id(19)}"
            }
            return fallback
    
    def _fetch_datadome_cookie(self, ua: str) -> Optional[str]:
        """Fetch DataDome cookie"""
        try:
            # First request to tags.js
            headers_js = {
                "Host": "datadome.garena.com",
                "sec-ch-ua-platform": '"Android"',
                "User-Agent": ua,
                "sec-ch-ua": '"Android WebView";v="147", "Chromium";v="147", "Not)A;Brand";v="24"',
                "sec-ch-ua-mobile": "?1",
                "Accept": "*/*",
                "X-Requested-With": "mark.via.gp",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Dest": "script",
                "Referer": "https://shop.garena.my/",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            }
            
            self.session.get(
                f"{self.DATADOME_URL}/tags.js",
                headers=headers_js,
                timeout=10
            )
            
            # Generate payload for /js/ endpoint
            payload = self._build_datadome_payload()
            
            headers_post = {
                "Host": "datadome.garena.com",
                "sec-ch-ua-platform": '"Android"',
                "User-Agent": ua,
                "sec-ch-ua": '"Android WebView";v="147", "Chromium";v="147", "Not)A;Brand";v="24"',
                "Content-Type": "application/x-www-form-urlencoded",
                "sec-ch-ua-mobile": "?1",
                "Accept": "*/*",
                "Origin": "https://shop.garena.my",
                "X-Requested-With": "mark.via.gp",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": "https://shop.garena.my/",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
                "Priority": "u=1, i",
            }
            
            resp = self.session.post(
                f"{self.DATADOME_URL}/js/",
                data=payload,
                headers=headers_post,
                timeout=15
            )
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if "cookie" in data:
                        match = re.search(r'datadome=([^;]+)', data["cookie"])
                        if match:
                            return match.group(1)
                except:
                    pass
            
            return None
            
        except Exception as e:
            print(f"    DataDome error: {e}")
            return None
    
    def _build_datadome_payload(self) -> str:
        """Build DataDome JS challenge payload"""
        payload = {
            "jspl": f"YtWekhrC-SoxiB0xDqWsuL2owhHVLFmN2n95VwzAtYYSM2HjXz5S-Jav65mWLkeURjUYgVOwnDj0jAje2LAuRkLuLA2db8puAXaOBL5DVIoCwyEAz3SL4XfHmCm1soXGFdUZYKYAkMZrROk4YstXyiBUfIHzfkHtyOaBtxieKtnLkTjuy7LiVsVig3wD-AX80RuQEASzcObG5vD0lH_LC3i5YpprF4UAYzOIixxvU6pnmuWfeSLfnyBitPafCAlVzgGyVYDWkwuio0WbKu7FD4BQgBNmT4aqiw4kfCqEMFzQt6Mu5lNDaZ63uDnJiy20XWWW4uUrc3QklPIihIoflK653TzzTdaYzZqL6pEg6PANP-0V2jCw9rZvqefSceiAIC1wsASHHblPh9fICMNsNfQaauv_H9jFFFtXxw2f1tIEi-P7SNOxOLE6sIiqfxwh50m7_2BZXKgoydpLNLVZSjsDE2iSxTBrk7FUfGemIM05dqn-FEZZG8GWrjBOzO5E0-r1twTKSU-tmqsoeyeYzgNsEleu-2ozNEGhbiDHGltNUsGAWsAeeeJrxl7R26ywcA-cHMebKVmp7i6Lg8mLO5TnPz7YcbYGCiU04LG1UEyzyK8vLI_9qOVlT8bc6xLr0doo1JNMYkU6U-bSwtd8odoFOY6B-VZHM6sZ7QKYC67e4hbGLhMYRbofanYJ_BMCHoj3oHoDMUE0EM4iVXoLp-m_ZBkbfPq9-SSIkIYYJLUXk9TeN_nbtn9VvdlXlSnYgBUS5axSzrUXUV4vIee6lQJzT0Wp0EikmptRNHAP5xeOgBOOjCUeRhNNiPXZdqNH5JCoQKEaGEajYRoNnenXeKCQhxfPN1NJWEOzk3e19H7m8ey4xA2gxX6AG-vzZXbP5cwi1OFf-tFKNr8ifHiMI3UPBksoT_UP2n0tFIobJRIWcWLLEmcAsCyd0jX9I7sGm8RrJYtY_JpX6wLTX13gcqff3vmxf2L-EBGXPgFZF-yfna0SxQaacvpfcPgjNfjVfI55w3EtT-2qOhplFJzwJ-6t8p0UU2PlBm_ItGFoGQcAAeiM2Ct1u_FfmnPhfKmX53EYqxJNA8lKrB2KZIeYgHymZ3uGlnTmC0q3pLYTRL83IKvKFNKYSctISMSPVrHt5auoqD6L1TyMHEwVAdkiWD0jGar-KqyZvrtG8L7ZCZ3XPpOUaHA0PEQgbTMtILw60pfweOAIu1sIJgBWZFSSePW9si-nartH1PkFckan53EC3iP4dGD60vbN3UfHZXblbvWHNXH86nmU3rP-1al2RGjVtTuwWHxe8n7x66XQSWM1M4uIjzBCNIaAyT2c9iE1t4sEbGDeCrlYVj-8LdsGGltPtSpaPWmPYtZOFpXZz1BIMiHOqp38ORXIOMXqvc7-ug7_WBjkgjn-zgSbJdGgU9dy9ykQnu1Q1-vXByE-Ew8x071Y74BQV_e0WyVXU06J-cnEMFATFD-PUGjUe63z_8L1Fcrt8YxOVX-w74-TpPDTh2vKdu0E3e9lpQ5AHig-e6CGIqDbD3LpfgxAC9IwSonv3CzN0sDP07iwGndVWiw2bNRQBxgbauJOwzO6FRJajxDrdDRnxW-puf1bdsDUyIwvW8ZzRZqUzQ-YjVj-_BSqrsteNMzJ9Vx-JW4inoAl5pfG8y4lR-d6s8cgGPFxwyOxMfWZoocL8QaV3y2krEDDuN8z5yD4C7AUVbF52lZmqJ5XYorZa1GsOGv7f6K5X9MmDU3ErrGVZE04XrWtG4kox--Uw-hTeVvIVe-FOJSlxSCcUthKXlBW_d5UR1VXOtGzKdze0Jma5TbPeODBOfN2M3jRLckl-EhfPbngnNJGapApmJTA-vfcohYWTYH6WwYn6t0Y5eb7KCU9ABmUlgkdhL5jg1jrGMqJHWY2KcobjJWkogMOD9OpYLGfIbq9uSKQeEpiWVgqWzDhWC98dGM0dhVj2WIqPiIdba-6Pta72pEpvIuOoGmggli1hMV0PaebEs9Wcvj7NHA1vDyLmDKHmZYOFPp4Io3juS8lGutsDrXlK4jytityI3Cj17eS8UxOhcAd6uTcpcEfOIq5kCbD7EypWWVU30_EMI6VsBF0IqU2cPEOx3qThR6RS1cG-W3ljNYEoef5ngCp4vwn4XKL6iz3oDTjoT9-K0gnAyWtZIeMsYPcvQ8E8uZSUgPefO32NFHmsNjlSDhd385vLFDNHxfkRfW08NHr5Exfcmpe6FntbzA5AMctHkGXbaceSUwZXybz0qwHspMeR-DwUgurai_zLe2jy3gzJROlzdl5HSA4UBrVuAcOE8R0BiMF2CVlKRu8DQcoKyDoIofHyT3n-TK0JevoTqo4ob3oCPpAuqSDtu7Q3rGz0NoI3tHuVX7A3H78fK72qxu4OS_02vi4TnT7J1PRkXYW7jO4bt4bafD6_DHzjzWpqypMUNBJMDYGZQMIk8vzQHI-xdV7Gyz0gutZXsaBkJTegC41C11N5qYmWwI6BDjuMHKaXtbwH5nTXNrhD_drmwfVg393pz3Qac09fvWVkzS3oXZWfp4yNCBTO3d3BOHJhJ7MQBVv0Sp3TlXwzucqQOYp6q1Bt1py2KOxK8mEVeEK1kXFXwGmQ73a_GQi_Y3WNchEwDdzzB3MJ1WMxNfGLAqxgGgK4hZaw53qdBOvco8_w_r3sp8xRaHuU4BfIOje_4IXg7BNwv1WcVyXuVbZhDzupiD3Bw1hJyjMeiZNGZVCM5kk4Xq9sk2JT996ERqMkRPb-tMogunZGU3jqMnMyAXuMG89Xj6bnIW4VFjSysb5txzCXybS-OiqkcxThsBh3ozbgvXc8Z8Q80I9tQSfuprXZTulUu9x5cyqnEv__Ps8VOG6kt741QxI7lHE6WdS2G2iFM8H3QDykRv-NcZ6IeYymLV3V8IbOKhHXjipCAeTQ2XOHY69-iig6jRCqnFERD4mi9MFc6y-k7_7j2l6gFP1z-7ZK3nyNxy0IEFOq8s_qHZrV8vfHhI13twSqipTudcOTnad6ckUVKtCI2_efvTX0n4Zl3ojj_VMTSBHlThckD3CXRXy1wwXLoRh9pr47gOyBXfSEj2gf9BE4PgPXkmAEtP_lwjaRIhU_UEY61ZYDwHsTLnHkglSqJXDW1cm8bmTCgWMbei2XdSLR7fM5IdIOVfX7WjYuoiG889O9f7uKIt1Rh5u_kouPr_F1PNwhkkrQlT_gmGbvp9Rz8hLXVUB9Pbf6mfn2C4hLIUXbrYgTXpGCJNTNln27NVxM2WTaw7gHsh-u4CQZfx9Psjc-rneEkqvHwbjBhOMTGnInamHAFfbeybJScV4zYBUv_w1zMIf4qV2LxO1QQhn69hEBjezxh-GMrvyngipSj4rs3R1nUOxQy1scwcd0K5vdHCmtnBGQcWnnE6CO1msrsYOHtZL99g823zcVc7uBBIQf7_GGiMCp81Z7nm_vwuT8XyxtWEU9yaDN6TfT2aNGuzB29fHQxgF9gEwlVGUmVJZxbFHp--7pdV3O8RA6hhYj1N0AbDiAVfsO5gS334Ywg5V34eAJpaF9xneXo9q-sOeVdu7hhyxnMmgAG3aWWnXW4BLVE503JfDUDNsBR1LwP2VeC-xmdmvLeKWHfeytdDksWwOUcKZ-99DjP9flMNswfnUhvY9i1EsxYmZv8eK5QRDqKhakGw_mzx8h4Qy0ZXyk9utvgN0AXY3PFvwONVWxO7vtrUp1vZ4JngdRXYpWTwpK9eCNzkD0qUs9XGUpdb3u0DrNcupoDo-MjkDHolwwL2LxGc_6saT4gfqZ8EsKJEHUemx5vveYv1LEIqAgnuZHe0OcGblImKunpOTcRJJiCSCU19NLmjnPowYw7J-5S37YE9MKZ-T_yNpGHNIMNhzVgpKZsJ1Oh1Vd2cw0-LieQiERxHT_Joj20nx6Mwk1TiQxuq4VGNE4KXl0MAIlyFIy3co3y6OBGC6vQIJjm-7TZ78qnAVmaFYVJ5QSr0z050FTX1UA-xTzQhvntaX3yLaqo5xCWracL-vK2H4XPCmWtc3S53h-LUKlsWktMc-U9et0kiI_jYt7-JAyfxXlxag6oCLekzTFxFAt5VrR_bGmN0UxPPhsN1c7xawyE06DEQn3Oq7j9Dh7TmMavuVyTpyZfFohdzmG9ji-C6pckgoOhxLDhQzuf9UvtiFTYi-xKtGY8Ein4s_pb1MIGpThssIfftTbenm8P8N4BY-7GOzuqn1DzrsuPX-9qDw0gAFLgLHlPMAjaxVKpQBm1MIqNYVt32ExLjT4FXRT9UL1DBL01R9BS-LZwv7jhTxPLX7hae73FudZeBKFFQ07Y9Bnqb7dbcsZNicq31s_THnjbV_Hcrlma91jYm9WHSGZE_NFjbinw-R9HURj3sDsOt2IDVK3q3A3wWLoEGsFsKE1U5XA6zaShzgLNAo08Ci2QLsREEBcp8Ugs9zlXADgaZHAL99Y9-7dKS0zALxs25LzAlZoRUZDD0a51jMyJwoCIdbuOMbfZUs4mhLWpxyrhTRX8px0Plup0jyyKFjoQ57_Kapvx8hNLqTtOjS_MrkjAqu7MMX-v2qtcYABytgcKBSwGoIe0-TVNAS0FhdhKScl6KPUAwMq-PHl6PpQyhE9L1g2ycfRJOxCNJM5lZTaad8MVzAPKN1JyMRzRGWYagpBMJ6OboS8nreQeZc_vzOy3Rhs_-CzFXfdkAO2UMWlWcOTPrbrO59GPn0U0F_HhhVZT75YhTyb8fuv552SwHPdpSEcSPopkri5w5zfff_nnWyVVFLiiQYTtiZcWRYr-dacaecIllTFVGmaY9TqdEN_w9dU9sZVZiWaRFy0OA0Y8YSXP-MPQaQarPbThndEs92MCcL__p0NA3qwxf7K4g1wrReT6o3KEisSoW2LHEl-_9PuST2zLMau0Cl84Ej_oRfwaTEbYxL9qrUGZ9YHStsLM6RJsOJr6gGqwB0IaHfH4AHmZn_av9ISwy",
            "eventCounters": "%5B%5D",
            "jsType": "ch",
            "cid": f"2jMcN9y8YdlyjfZbVNjVr_4r1HJIcD0elf7_5H1gNGCi7A9AQCKNwFCqjknvfxCYbxzidtpMReqz8bSH6DdGC4isiyZnyq8ke_2tgvAuzXRPHM96h5h~RtHR0XjSLmd7",
            "ddk": "AE3F04AD3F0D3A462481A337485081",
            "Referer": "https%253A%252F%252Fshop.garena.my%252F%253Fchannel%253D202953",
            "request": "%252F%253Fchannel%253D202953",
            "responsePage": "origin",
            "ddv": "5.7.0"
        }
        
        params = []
        for key, value in payload.items():
            params.append(f"{key}={value}")
        return "&".join(params)
    
    def _send_track_event(self, session_id: str, ua: str) -> None:
        """Send tracking event"""
        try:
            url = f"{self.BASE_URL}/api/tracker/track"
            data = {
                "client_id": 10000,
                "data": [{
                    "event": "MshopRevampVisit",
                    "id": str(uuid.uuid4()),
                    "ts": int(time.time()),
                    "payload": {
                        "session_id": session_id,
                        "group": "treatment2",
                        "service_version": "mshop_frontend_20260616",
                        "source": "mb",
                        "domain": "shop.garena.my",
                        "page": "page_view",
                        "path": "/",
                        "client": "mobile",
                        "region": "my",
                        "country": "MY",
                        "ua": ua,
                        "ip": "103.59.178.227"
                    }
                }]
            }
            headers = {
                "Accept": "*/*",
                "Content-Type": "application/json",
                "Origin": "https://shop.garena.my",
                "Referer": "https://shop.garena.my/?channel=202953",
                "User-Agent": ua,
                "X-Requested-With": "mark.via.gp",
            }
            self.session.post(url, json=data, headers=headers, timeout=10)
        except:
            pass


class GarenaPlayerAPI:
    """Main API for fetching player info"""
    
    BASE_URL = "https://shop.garena.my"
    
    def __init__(self):
        self.cookie_manager = GarenaCookieManager()
    
    def get_player_info(self, uid: str) -> Dict[str, Any]:
        """
        Fetch player info with fresh cookies for every request.
        Returns formatted response.
        """
        print(f"\n{'='*50}")
        print(f"🎯 Fetching info for UID: {uid}")
        print(f"{'='*50}")
        
        try:
            # STEP 1: Generate fresh cookies
            cookies = self.cookie_manager.fetch_fresh_cookies()
            
            # STEP 2: Create new session with fresh cookies
            session = requests.Session()
            for key, value in cookies.items():
                session.cookies.set(key, value)
            
            # STEP 3: Set headers
            ua = self.cookie_manager._random_ua()
            headers = {
                "Host": "shop.garena.my",
                "Connection": "keep-alive",
                "Content-Length": "41",
                "sec-ch-ua-platform": '"Android"',
                "User-Agent": ua,
                "Accept": "application/json, text/plain, */*",
                "sec-ch-ua": '"Android WebView";v="147", "Chromium";v="147", "Not)A;Brand";v="24"',
                "Content-Type": "application/json",
                "sec-ch-ua-mobile": "?1",
                "Origin": "https://shop.garena.my",
                "X-Requested-With": "mark.via.gp",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": "https://shop.garena.my/?channel=202953",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            }
            
            # STEP 4: Make API call with fresh cookies
            print(f"📡 Calling player_id_login API...")
            payload = {"app_id": 100067, "login_id": uid}
            
            resp = session.post(
                f"{self.BASE_URL}/api/auth/player_id_login",
                json=payload,
                headers=headers,
                timeout=15
            )
            
            print(f"📥 Response Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"📦 Response Data: {json.dumps(data, indent=2)}")
                
                nickname = data.get("nickname", "")
                
                if nickname:
                    return {
                        "status": "success",
                        "uid": uid,
                        "nickname": nickname,
                        "open_id": data.get("open_id", ""),
                        "region": data.get("region", "BD"),
                        "img_url": data.get("img_url", ""),
                        "timestamp": int(time.time())
                    }
            
            # Try alternative endpoint
            print("📡 Trying alternative endpoint...")
            resp2 = session.get(
                f"{self.BASE_URL}/api/auth/get_user_info/multi",
                headers=headers,
                timeout=10
            )
            
            if resp2.status_code == 200:
                data2 = resp2.json()
                player_data = data2.get("player_id", {})
                nickname = player_data.get("nickname", "")
                
                if nickname:
                    return {
                        "status": "success",
                        "uid": uid,
                        "nickname": nickname,
                        "open_id": player_data.get("open_id", ""),
                        "img_url": player_data.get("img_url", ""),
                        "timestamp": int(time.time())
                    }
            
            return {
                "status": "error",
                "uid": uid,
                "nickname": None,
                "message": f"Player not found (Status: {resp.status_code})",
                "timestamp": int(time.time())
            }
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {
                "status": "error",
                "uid": uid,
                "nickname": None,
                "message": str(e),
                "timestamp": int(time.time())
                        }

from http.server import BaseHTTPRequestHandler
import json
import requests
import uuid
import time

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        path = self.path
        
        if path in ['/', '/api/health']:
            self._json({"status": "ok"})
            return
        
        if path.startswith('/api/player/'):
            uid = path.split('/api/player/')[1].strip()
            if uid:
                start = time.time()
                result = self._fetch_real_player(uid)
                result['response_time_ms'] = round((time.time() - start) * 1000)
                self._json(result)
                return
        
        self._json({"status": "error"}, 404)
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def _fetch_real_player(self, uid):
        """Fetch REAL player data from Garena API"""
        try:
            # Real working cookies
            cookies = {
                "source": "mb",
                "region": "MY", 
                "language": "en",
                "mspid2": uuid.uuid4().hex[:32],
                "datadome": "U7t8fwqntZDdQUIB4hlhLponNmDPdmStSH5StHyyc5QOQ_3MIDobzMejYHcFd25YUuXZgNKRUd5H75XJtNZD8w7FN8YyuHrccH9Uw_I8NzJXyagdJiKZb7aMiSinZxBz"
            }
            
            headers = {
                "Host": "shop.garena.my",
                "User-Agent": "Mozilla/5.0 (Linux; Android 12; M2101K7AI Build/SKQ1.210908.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.7827.91 Mobile Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "X-Requested-With": "mark.via.gp",
                "Origin": "https://shop.garena.my",
                "Referer": "https://shop.garena.my/?channel=202953",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            }
            
            payload = {"app_id": 100067, "login_id": uid}
            
            # Real API call
            resp = requests.post(
                "https://shop.garena.my/api/auth/player_id_login",
                json=payload,
                cookies=cookies,
                headers=headers,
                timeout=10
            )
            
            print(f"[DEBUG] Status: {resp.status_code}")
            print(f"[DEBUG] Response: {resp.text[:500]}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"[DEBUG] Parsed: {json.dumps(data, indent=2)}")
                
                nickname = data.get("nickname", "")
                
                if nickname:
                    return {
                        "status": "success",
                        "uid": uid,
                        "nickname": nickname,
                        "open_id": data.get("open_id", ""),
                        "region": data.get("region", "")
                    }
                else:
                    return {
                        "status": "error",
                        "uid": uid,
                        "message": "Nickname not found in response"
                    }
            
            # Try with session_key
            cookies["session_key"] = "toxdjxbtm1ttyldntzq8ggsvjlg6tuwn"
            
            resp2 = requests.post(
                "https://shop.garena.my/api/auth/player_id_login",
                json=payload,
                cookies=cookies,
                headers=headers,
                timeout=10
            )
            
            if resp2.status_code == 200:
                data = resp2.json()
                nickname = data.get("nickname", "")
                if nickname:
                    return {
                        "status": "success",
                        "uid": uid,
                        "nickname": nickname
                    }
            
            return {
                "status": "error",
                "uid": uid,
                "message": f"API returned status {resp.status_code}",
                "raw_response": resp.text[:300]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "uid": uid,
                "message": str(e)
            }
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

import json
from datetime import datetime,time

def load_users():
    with open('users.json', 'r') as f:
        return json.load(f)['users']

def find_user_by_email(email):
    for user in load_users():
        
        if user['email'] == email:
            return user
    return None

def _time_in_window(now: time, start: time, end: time) -> bool:

    if start <= end:          
        return start <= now <= end
    else:                    
        return now >= start or now <= end

def is_access_allowed(user, current_ip, now=None, return_reason=False):
   
    now_dt = now or datetime.now()
    now_t = now_dt.time()

    # ---------- IP check ----------
    
    if 'allowed_ips' in user:
        allowed_ips = user.get('allowed_ips') or []
        if isinstance(allowed_ips, str):
            allowed_ips = [allowed_ips]
    else:
        
        allowed_ips = [user.get('allowed_ip')] if user.get('allowed_ip') else []

    ip_ok = not allowed_ips or current_ip in allowed_ips

    # ---------- time check ----------
    time_ok = True
    if 'allowed_start_time' in user and 'allowed_end_time' in user:
        try:
            start = datetime.strptime(user["allowed_start_time"], "%H:%M").time()
            end   = datetime.strptime(user["allowed_end_time"], "%H:%M").time()
            time_ok = _time_in_window(now_t, start, end)
        except Exception:
            time_ok = False
    elif 'allowed_hours' in user:
        try:
            sh, eh = user['allowed_hours']
            start = time(sh, 0)
            end   = time(eh, 0)
            time_ok = _time_in_window(now_t, start, end)
        except Exception:
            time_ok = False

    ok = ip_ok and time_ok
    if return_reason:
        if not ip_ok:
            return False, f"IP {current_ip} not in allowed list {allowed_ips}"
        if not time_ok:
            if 'allowed_start_time' in user:
                return False, f"Current time {now_t} is outside {user['allowed_start_time']}-{user['allowed_end_time']}"
            elif 'allowed_hours' in user:
                return False, f"Current time {now_t} is outside hours {user['allowed_hours']}"
            else:
                return False, "No valid time policy configured"
        return True, "OK"

    return ok

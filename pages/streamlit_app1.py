import streamlit as st
import requests
import time
import datetime
import pytz
from pathlib import Path
import streamlit_authenticator as stauth
from synology_api.core_sys_info import SysInfo
from synology_api.event_scheduler import EventScheduler
from synology_api.task_scheduler import TaskScheduler




sgt = pytz.timezone("Asia/Singapore")


st.header("NAS Syst Dashboard", divider="rainbow")
base = "http://testsvrs.synology.me:5000/webapi"
NAS_HOST = "testsvrs.synology.me"
NAS_PORT = "5000"
RESTART_TASK_NAME = "Dashboard Scheduled Restart"

config = {
    "credentials": {
        "usernames": {
            "admin": {
                "email": st.secrets["credentials"]["usernames"]["admin"]["email"],
                "first_name": st.secrets["credentials"]["usernames"]["admin"]["first_name"],
                "last_name": st.secrets["credentials"]["usernames"]["admin"]["last_name"],
                "username": st.secrets["credentials"]["usernames"]["admin"]["username"],
                "password": st.secrets["credentials"]["usernames"]["admin"]["password"],
                "logged_in": False,
                "failed_login_attempts": 0
            }
        }
    },
    "cookie": {
        "name": st.secrets["cookie"]["name"],
        "key": st.secrets["cookie"]["key"],
        "expiry_days": st.secrets["cookie"]["expiry_days"]
    }
}
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login(location='unrendered')

if not st.session_state.get('authentication_status'):
    st.error("You must log in first.")
    if st.button("Go to Login"):
        st.switch_page("Login.py")
    st.stop()

authenticator.logout(location='sidebar')


@st.cache_data(ttl=30)
def get_sid():
                    
                
        
    try:
        login = requests.get(f"{base}/auth.cgi", params={
                "api":"SYNO.API.Auth",
                "version": 6,
                "method": "login",
                "account": st.secrets["secrets"]["DB_USERNAME"],
                "passwd": st.secrets["secrets"]["DB_PASSWORD"],
                "session": "FileStation",
                "format" : "sid"
            }, timeout=10)
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the NAS. Check that QuickConnect is enabled and your QuickConnect ID is correct.")
        return None
    except requests.exceptions.Timeout:
        st.error("Connection timed out. The NAS may be offline or unreachable.")
        return None

    if login.status_code != 200:
        st.error(f"Server returned HTTP {login.status_code}. Response: {login.text[:300]}")
        return None

    if not login.text.strip():
        st.error("Server returned an empty response. QuickConnect may not be reaching your NAS — check that it's online and QuickConnect is enabled in DSM.")
        return None

    try:
        data = login.json()
    except requests.exceptions.JSONDecodeError:
        st.error(f"Server returned non-JSON response. Raw response: {login.text[:300]}")
        return None

    if not data.get("success"):
        st.error(f"Login failed: {data.get('error')}")
        return None
    return data["data"]["sid"]
def get_system_info(sid):
    try:
        resp = requests.get(f"{base}/entry.cgi", params={
        "api": "SYNO.Core.System",
        "version": 1,
        "method": "info",
        "_sid": sid
    })
        return resp.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            st.error("Lost connection to NAS while fetching system info.")
            return {}
def get_storage_info(sid):
    try: 
        resp = requests.get(f"{base}/entry.cgi", params= {
        "api": "SYNO.Storage.CGI.Storage",
        "version": 1,
        "method":"load_info",
        "_sid": sid
        })
        return resp.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        st.error("Lost connection to NAS while fetching storage info.")
        return {}
def get_utilization(sid):
    try:
        resp = requests.get(f"{base}/entry.cgi", params={
        "api":"SYNO.Core.System.Utilization",
        "version": 1,
        "method":"get",
        "_sid":sid
    })
        return resp.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        st.error("Lost connection to NAS while fetching utilization info.")
        return {}
def _clean_quickconnect_id(raw_id: str) -> str:
    """Accepts either a bare QuickConnect ID ('Testsvrs') or a pasted URL/link
    ('https://Testsvrs.quickconnect.to', 'QuickConnect.to/Testsvrs:5000', etc.)
    and returns just the bare ID, so a copy-paste mistake doesn't break the connection."""
    cleaned = raw_id.strip()
    cleaned = cleaned.replace("https://", "").replace("http://", "")
    cleaned = cleaned.split("/")[-1] if "/" in cleaned else cleaned  # take last path segment
    cleaned = cleaned.split(":")[0]  # drop any port
    cleaned = cleaned.split(".")[0]  # drop .quickconnect.to or similar suffix
    return cleaned
    
@st.cache_resource(ttl=1800)
def get_clients():
    creds = dict(
        ip_address=NAS_HOST,
        port=NAS_PORT,
        secure=False,
        username=st.secrets["secrets"]["DB_USERNAME"],
        password=st.secrets["secrets"]["DB_PASSWORD"],
        dsm_version = 6,
        debug = True,
    )
    result = {}
    for label, cls in [("sys", SysInfo), ("scheduler", EventScheduler), ("tasks", TaskScheduler)]:
        try:
            result[label] = cls(**creds)
        except Exception as e:
            st.error(f"Failed to initialize '{label}' client ({cls.__name__}): {e}")
            return None
    return result
        
def find_task_by_name(tasks_client,name):
    result = tasks_client.get_task_list()
    if not result.get("success"):
        return None
    for task in result.get("data", {}).get("tasks",[]):
        if task.get("name") == name:
            return task
    return None
    
        

sid = get_sid()
clients=get_clients() if sid else None

st.subheader("Power Controls")
    

if sid and clients:
    
    col_shutdown,col_start=st.columns(2)
    day_map = {"Mon": "1", "Tue": "2", "Wed": "3", "Thu": "4", "Fri": "5", "Sat": "6", "Sun": "0"}

    with col_shutdown:
        st.write("Shutdown Schedule")
        st.caption("Recurring shutdown via the NAS's built-in power schedule — persists even if this tab is closed.")
        shutdown_time = st.time_input("Shutdown time", value=datetime.time(22,0))
        shutdown_repeat_choice = st.multiselect(
            "Repeat on", options=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            default=["Mon", "Tue", "Wed", "Thu", "Fri"], key="shutdown_days"
        )
        shutdown_repeat_days = ",".join(day_map[d] for d in shutdown_repeat_choice) if shutdown_repeat_choice else ""
 
        if st.button("💾 Save Shutdown Schedule", use_container_width=True):
            existing = clients["scheduler"].load_power_schedule()
            existing_poweron = existing.get("data", {}).get("poweron_tasks", []) if existing.get("success") else []
            new_poweroff_tasks = [{
                "enabled": True, "hour": shutdown_time.hour, "min": shutdown_time.minute,
                "weekdays": shutdown_repeat_days
            }] if shutdown_repeat_days else []
            result = clients["scheduler"].set_power_schedule(
                poweron_tasks=existing_poweron, poweroff_tasks=new_poweroff_tasks
            )
            if result.get("success"):
                st.success(f"Shutdown scheduled for {shutdown_time.strftime('%H:%M')} on {', '.join(shutdown_repeat_choice) or 'no days'}")
            else:
                err = result.get("error", {})
                st.error(f"Failed to save (code {err.get('code', '?')})")
 
        st.divider()
        if st.button("⏻ Shutdown NAS now", type="primary", use_container_width=True):
            if st.session_state.get("confirm_shutdown_now"):
                result = clients["sys"].shutdown()
                st.session_state["confirm_shutdown_now"] = False
                if isinstance(result, dict) and not result.get("success", True):
                    err = result.get("error", {})
                    st.error(f"Shutdown failed (code {err.get('code', '?')})")
                else:
                    st.success("NAS is shutting down...")
            else:
                st.session_state["confirm_shutdown_now"] = True
                st.warning("Click again to confirm immediate shutdown.")
    with col_start:
        st.write("**Startup Schedule**")
        st.caption("Uses the NAS's built-in power schedule (RTC-based) so it starts back up even after a full shutdown.")
        start_time = st.time_input("Daily startup time", value=datetime.time(8, 0))
        repeat_choice = st.multiselect(
            "Repeat on",
            options=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            default=["Mon", "Tue", "Wed", "Thu", "Fri"], key="startup_days"
        )
        repeat_days = ",".join(day_map[d] for d in repeat_choice) if repeat_choice else ""
 
        if st.button("💾 Save Startup Schedule", use_container_width=True):
            existing = clients["scheduler"].load_power_schedule()
            existing_poweroff = existing.get("data", {}).get("poweroff_tasks", []) if existing.get("success") else []
            new_poweron_tasks = [{
                "enabled": True, "hour": start_time.hour, "min": start_time.minute,
                "weekdays": repeat_days
            }] if repeat_days else []
            result3 = clients["scheduler"].set_power_schedule(
                poweron_tasks=new_poweron_tasks, poweroff_tasks=existing_poweroff
            )
            if result3.get("success"):
                st.success(f"Startup scheduled for {start_time.strftime('%H:%M')} on {', '.join(repeat_choice) or 'no days selected'}")
            else:
                err = result3.get("error", {})
                st.error(f"Failed to save schedule (code {err.get('code', '?')})")
 
        with st.expander("View current power schedule on NAS"):
            schedule = clients["scheduler"].load_power_schedule()
            if schedule.get("success"):
                st.json(schedule["data"])
            else:
                err = schedule.get("error", {})
                st.error(f"Could not read schedule (code {err.get('code', '?')})")
 
        
    st.divider()
    sys_info=get_system_info(sid)
    storage_info= get_storage_info(sid)
    util_info = get_utilization(sid)
    if sys_info.get("success"):
        data = sys_info["data"]
        col1,col2,col3 = st.columns(3)
        col1.metric("Model",data.get("model","N/A"))
        col2.metric("CPU Temperature",f"{data.get("sys_temp","N/A")}°C")

        
    else:
        st.error(f"System info failed:{sys_info.get('error')}")
    
    if util_info.get("success"):
        util = util_info["data"]
        st.subheader("CPU and Memory")
        col1,col2,col3 = st.columns(3)
        if "cpu" in util:
            col1.metric("CPU usage", f"{util['cpu'].get('user_load', 'N/A')}%")
        if "memory" in util:
            col2.metric("Memory Usage", f"{util['memory'].get('real_usage', 'N/A')}%")

    

        
        
    else:
        st.warning(f"Utilization info failed: {util_info.get('error')}")
    if storage_info.get("success"):
        st.subheader("Storage Volumes")

        def bytes_to_human(b):
            try:
                b = int(b)
            except (TypeError, ValueError):
                return "N/A"
            if b >= 1_099_511_627_776:  # 1 TB
                return f"{b / 1_099_511_627_776:.2f} TB"
            elif b >= 1_073_741_824:  # 1 GB
                return f"{b / 1_073_741_824:.2f} GB"
            elif b >= 1_048_576:  # 1 MB
                return f"{b / 1_048_576:.2f} MB"
            return f"{b} B"

        volumes = storage_info["data"].get("volumes", [])
        if not volumes:
            st.warning("No volumes found in storage info.")
        else:
            for vol in volumes:
                vol_id = vol.get("id") or vol.get("volume_path") or "Unknown Volume"
                status = vol.get("status", "N/A")

                # Synology DSM uses 'size' dict OR top-level used_size/total_size
                size_block = vol.get("size", {})
                used  = vol.get("used_size")  or size_block.get("used")
                total = vol.get("total_size") or size_block.get("total")
                free  = vol.get("free_size")  or size_block.get("avail")

                st.write(f"**{vol_id}** — Status: `{status}`")

                col1, col2, col3 = st.columns(3)
                col1.metric("Total", bytes_to_human(total))
                col2.metric("Used",  bytes_to_human(used))
                col3.metric("Free",  bytes_to_human((int(total) - int(used)) if total and used else free))

                if used and total:
                    try:
                        pct = round(int(used) / int(total) * 100, 1)
                        st.progress(pct / 100, text=f"{pct}% used")
                    except (ValueError, ZeroDivisionError):
                        pass

                st.divider()

       
    else:
        st.error(f"Storage info failed: {storage_info.get('error')}")
else:
    st.stop()


time.sleep(30)
st.rerun()

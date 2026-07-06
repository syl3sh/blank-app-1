import streamlit as st
import requests
import time
import datetime
import wakeonlan
import pytz
from pathlib import Path
import streamlit_authenticator as stauth




sgt = pytz.timezone("Asia/Singapore")


st.header("NAS Syst Dashboard", divider="rainbow")
base = "http://testsvrs.synology.me:5000/webapi"


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
        st.switch_page("loginnewpage.py")
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

def shutdown_nas(sid):
    """Ask the NAS to shut down. A dropped connection during this call
    usually means the NAS went down mid-response, so treat that as success."""
    try:
        resp = requests.get(f"{base}/entry.cgi", params={
            "api": "SYNO.Core.System",
            "version": 1,
            "method": "shutdown",
            "_sid": sid
        }, timeout=5)
        return resp.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return {"success": True, "note": "Connection dropped — shutdown likely in progress"}
 
 
def restart_nas(sid):
    """Ask the NAS to reboot. Same caveat as shutdown_nas re: dropped connections."""
    try:
        resp = requests.get(f"{base}/entry.cgi", params={
            "api": "SYNO.Core.System",
            "version": 1,
            "method": "reboot",
            "_sid": sid
        }, timeout=5)
        return resp.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return {"success": True, "note": "Connection dropped — reboot likely in progress"}

        
def set_power_schedule(sid, startup_enabled, startup_hour, startup_min,
                       shutdown_enabled, shutdown_hour, shutdown_min,
                       restart_enabled, restart_hour, restart_min, repeat_days):
    resp = requests.post(f"{base}/entry.cgi", data={
        "api": "SYNO.Core.System.PowerSchedule",
        "version": 1,
        "method": "set",
        "_sid": sid,
        "start_enabled": str(startup_enabled).lower(),
        "start_hour": startup_hour,
        "start_min": startup_min,
        "shut_enabled": str(shutdown_enabled).lower(),
        "shut_hour": shutdown_hour,
        "shut_min": shutdown_min,
        "restart_enabled": str(restart_enabled).lower(),
        "restart_hour": restart_hour,
        "restart_min": restart_min,

        "repeat_days": repeat_days  # e.g. "1,2,3,4,5" for Mon-Fri, "0,1,2,3,4,5,6" for every day
    })
    return resp.json()
def get_power_schedule(sid):
    """Read back the schedule currently stored on the NAS so you can verify it stuck."""
    try:
        resp = requests.get(f"{base}/entry.cgi", params={
            "api": "SYNO.Core.System.PowerSchedule",
            "version": 1,
            "method": "get",
            "_sid": sid
        }, timeout=10)
        return resp.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return {"success": False, "error": {"code": -1, "message": "Connection lost while fetching power schedule"}}

sid = get_sid()

st.subheader("Power Controls")
    

if sid:
    
    col_shutdown,col_restart,col_start=st.columns(3)

    with col_shutdown:
        shutdown_date = st.date_input("Shutdown date",min_value=datetime.date.today())
        shutdown_time = st.time_input("Shutdown time", value=datetime.time(22,0))
        shutdowntime = sgt.localize(datetime.datetime.combine(shutdown_date,shutdown_time))
        if st.button("⏻ Shutdown NAS", type="primary", use_container_width=True):
            if st.session_state.get("confirm_shutdown"):
                st.session_state["shutdowntime"] = shutdowntime
                st.session_state["confirm_shutdown"] = False
                st.success(f"Shutdown scheduled for {shutdowntime.strftime('%Y-%m-%d %H:%M')}")
            else:
                st.session_state["confirm_shutdown"] = True
                st.warning("Click Shutdown again to confirm.")
        if "shutdowntime" in st.session_state:
            now_in_sgt = datetime.datetime.now(sgt)
            time_difference1 = st.session_state["shutdowntime"]-now_in_sgt
            mins_left = int(time_difference1.total_seconds()/60)
            if time_difference1.total_seconds() <= 0:
                result = shutdown_nas(sid)
                if result.get("success"):
                    st.success("NAS is shutting down...")
                    del st.session_state["shutdowntime"]
                else:
                    st.error(f"Shutdown failed: {result.get('error')}")
                    st.error(f"Shutdown failed (code {err.get('code', '?')}): {err.get('message', result)}")
            else:
                st.info(f"Shutdown in {mins_left} minutes")
    with col_restart:
        restart_date = st.date_input("Restart date",min_value=datetime.date.today())
        restart_time = st.time_input("Restart time", value=datetime.time(22,0))
        restarttime = sgt.localize(datetime.datetime.combine(restart_date,restart_time))
        if st.button("🔄 Restart NAS", use_container_width=True):
            if st.session_state.get("confirm_restart"):
                st.session_state["restarttime"] = restarttime
                st.session_state["confirm_restart"] = False
                st.success(f"Restart scheduled for {restarttime.strftime('%Y-%m-%d %H:%M')}")
            else:
                st.session_state["confirm_restart"] = True
                st.warning("Click Restart again to confirm.")
        if "restarttime" in st.session_state:
            now_in_sgt = datetime.datetime.now(sgt)
            timedifference2 = st.session_state["restarttime"]-now_in_sgt
            mins_left1 = int(timedifference2.total_seconds()/60)
            if timedifference2.total_seconds()<=0:
                result1 = restart_nas(sid)
                if result1.get("success"):
                    st.success("NAS is restarting...")
                    del st.session_state["restarttime"]
                else:
                    st.error(f"Restart failed: {result1.get('error')}")
                    st.error(f"Restart failed (code {err.get('code', '?')}): {err.get('message', result1)}")
            else:
                st.info(f"Restart in {mins_left1} minutes")
    with col_start:
        st.write("Scheduled Startup")
        st.caption("Uses the NAS's power schedule so it can start after a full shutdown.")
        start_time = st.time_input("Daily startup time", value = datetime.time(9,0))
        repeat_choice = st.multiselect(
            "Repeat on",
            options=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            default=["Mon", "Tue", "Wed", "Thu", "Fri"]
        )
        day_map = {"Mon": "1", "Tue": "2", "Wed": "3", "Thu": "4", "Fri": "5", "Sat": "6", "Sun": "0"}
        repeat_days = ",".join(day_map[d] for d in repeat_choice) if repeat_choice else ""
        if st.button("Save Startup Schedule", use_container_width = True):
            result3 = set_power_schedule(
                sid,
                startup_enabled = True,
                startup_hour= start_time.hour,
                startup_min = start_time.minute,
                shutdown_enabled=False,
                shutdown_hour= 0,
                shutdown_min = 0,
                restart_enabled = False,
                restart_hour = 0,
                restart_min = 0,
                repeat_days= repeat_days,
            )
            if  result3.get("success"):
                st.success(f"Startup scheduled for {start_time.strftime('%H:%M')} on {', '.join(repeat_choice) or 'no days selected'}")
            else:
                err = result3.get("error", {})
                st.error(f"Failed to save schedule (code {err.get('code', '?')}): {err.get('message', result3)}")
 
        with st.expander("View current power schedule on NAS"):
            schedule = get_power_schedule(sid)
            if schedule.get("success"):
                st.json(schedule["data"])
            else:
                err = schedule.get("error", {})
                st.error(f"Could not read schedule (code {err.get('code', '?')}): {err.get('message', schedule)}")
      

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

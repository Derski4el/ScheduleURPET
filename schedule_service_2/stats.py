import pandas as pd
from datetime import datetime, timedelta
import json

ALL_GROUPS = [
    "ИСИП-118", "ТН-101", "Э-114", "ОДЛ-120", "ЮР-146", "ПН-101", "ИСИП-213", "ИСИП-215", 
    "ИСИПу-216", "ИСИП-306", "ИСИП-309", "ИСИП-414(314)", "ИСИП-402", "ИСИП-403", "ЗУ-201", 
    "Э-213", "ОДЛу-116(216)", "ОДЛу-119(219)", "ОДЛ-313(213)", "ПСОу-145(245)", "ПСА-201", 
    "ПСО-328(238)", "ПСО-339(239)"
]

def parse_schedule(file_path, group_name):
    df = pd.read_excel(file_path, header=None)
    
    session_times = [
        "09:00-10:30", "10:45-12:15", "13:00-14:30",
        "14:40-16:10", "16:20-17:50", "18:00-19:30"
    ]
    
    base_date = datetime(2025, 4, 14)

    if group_name == "all":
        all_schedules = {}
        for group in ALL_GROUPS:
            schedule_data = parse_schedule(file_path, group)
            all_schedules[group] = schedule_data.get("schedule", [])
        return {"schedule": all_schedules}

    schedule = []
    header_row = df.iloc[0]
    group_col = None
    for col in range(len(header_row)):
        if isinstance(header_row[col], str) and group_name in header_row[col]:
            group_col = col
            break

    if group_col is None:
        return {"schedule": [], "error": f"Group {group_name} not found"}

    current_date = base_date
    session_block = []
    session_index = 0

    for index, row in df.iterrows():
        if isinstance(row[0], str) and "пара" in row[0]:
            if session_index < len(session_times):
                sessions = []
                subject = row[group_col] if pd.notna(row[group_col]) else ""
                cabinet = row[group_col+1] if group_col+1 < len(row) and pd.notna(row[group_col+1]) else ""
                teacher = ""
                if subject and "," in subject:
                    parts = subject.split(",", 1)
                    subject = parts[0].strip()
                    teacher = parts[1].strip() if len(parts) > 1 else ""
                if subject or cabinet:
                    sessions.append({
                        "time": session_times[session_index],
                        "subject": subject,
                        "teacher": teacher,
                        "cabinet": cabinet
                    })
                session_block.append(sessions)
                session_index += 1
        else:
            if session_block:
                day_schedule = {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "sessions": []
                }
                for session_list in session_block:
                    for session in session_list:
                        day_schedule["sessions"].append(session)
                if day_schedule["sessions"]:
                    schedule.append(day_schedule)
                session_block = []
                session_index = 0
                current_date += timedelta(days=1)

    if session_block:
        day_schedule = {
            "date": current_date.strftime("%Y-%m-%d"),
            "sessions": []
        }
        for session_list in session_block:
            for session in session_list:
                day_schedule["sessions"].append(session)
        if day_schedule["sessions"]:
            schedule.append(day_schedule)

    return {"schedule": schedule}

if __name__ == "__main__":
    file_path = "14.04 - 18.04-1.xlsx"
    group_name = "all"
    result = parse_schedule(file_path, group_name)
    print(json.dumps(result, indent=2, ensure_ascii=False))
